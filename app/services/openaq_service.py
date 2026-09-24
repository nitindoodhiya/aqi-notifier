import httpx
from typing import Optional
from app.config import settings

class OpenAQService:
    def __init__(self):
        self.base_url = "https://api.openaq.org/v3"
        self.headers = {"X-API-Key": settings.OPENAQ_API_KEY} if settings.OPENAQ_API_KEY else {}

    async def fetch_latest_aqi(self, location_id: int) -> Optional[float]:
        url = f"{self.base_url}/locations/{location_id}/latest"
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                results = data.get("results", [])
                
                # Extract PM2.5 or first valid sensor reading
                for reading in results:
                    if reading.get("value") is not None:
                        return float(reading["value"])
                return None
            except Exception as e:
                print(f"[OpenAQ Error] Location {location_id}: {e}")
                return None

openaq_service = OpenAQService()