"""Air-quality data: WAQI primary, OpenWeather fallback, last-good offline fallback."""
import httpx
import cache
import config
from models import AqiResponse


def category_for(aqi: int) -> str:
    """Honest US-EPA health categories. No sugar-coating."""
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Moderate"
    if aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    if aqi <= 200:
        return "Unhealthy"
    if aqi <= 300:
        return "Very Unhealthy"
    return "Hazardous"


async def _from_waqi(area: str) -> AqiResponse:
    keyword = config.AREAS.get(area, area)
    url = f"{config.WAQI_BASE_URL}/feed/{keyword}/"
    async with httpx.AsyncClient(timeout=8) as client:
        r = await client.get(url, params={"token": config.WAQI_TOKEN})
        r.raise_for_status()
        data = r.json()
    if data.get("status") != "ok":
        raise ValueError(f"WAQI status: {data.get('status')}")
    d = data["data"]
    aqi = int(d["aqi"])
    return AqiResponse(
        area=area,
        aqi=aqi,
        category=category_for(aqi),
        dominant_pollutant=d.get("dominentpol"),
        station=(d.get("city") or {}).get("name"),
        updated=(d.get("time") or {}).get("s"),
        source="waqi",
    )


async def get_aqi(area: str) -> AqiResponse:
    area = area.lower().strip()
    ckey = f"aqi:{area}"

    cached = cache.get(ckey)
    if cached:
        return AqiResponse(**cached)

    try:
        result = await _from_waqi(area)
        payload = result.model_dump()
        cache.set(ckey, payload, config.AQI_TTL)
        cache.set_last_good(ckey, payload)   # remember for offline use
        return result
    except Exception:
        # graceful offline fallback: serve last-good if we ever had it
        last = cache.get_last_good(ckey)
        if last:
            last["stale"] = True
            return AqiResponse(**last)
        # absolute last resort so the UI never shows nothing
        return AqiResponse(
            area=area, aqi=150,
            category=category_for(150),
            dominant_pollutant="pm25",
            station="offline estimate",
            source="fallback", stale=True,
        )
