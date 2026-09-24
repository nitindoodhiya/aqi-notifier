import httpx
from typing import List
from app.config import settings
from app.schemas import UserConfig, DetectionResult, AQIReading

class OllamaService:
    def __init__(self):
        self.url = f"{settings.OLLAMA_HOST}/api/generate"

    async def generate_notification(
        self, 
        user: UserConfig, 
        detection: DetectionResult, 
        history: List[AQIReading]
    ) -> str:
        # Format recent history for prompt context (e.g., last 5 readings)
        recent_readings = [round(h.value, 1) for h in history[-5:]]
        
        prompt = f"""
        You are an AI health agent. Write a concise, actionable notification for a user.
        
        Context:
        - City: {user.city_name}
        - Event Type: {detection.type}
        - Current Reading: {detection.current}
        - Recent Reading History (oldest to newest): {recent_readings}
        - Baseline Average: {detection.baseline_avg}
        
        Instructions:
        1. Write 1-2 natural, direct sentences.
        2. Briefly reference the recent numerical trend or sudden shift in context.
        3. Provide exactly ONE clear, actionable health recommendation.
        4. Do NOT output raw JSON or plain status updates.
        """

        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3}
        }

        async with httpx.AsyncClient(timeout=1.0 if detection.type != "RETURN_TO_NORMAL" else 30.0) as client:
            try:
                response = await client.post(self.url, json=payload)
                response.raise_for_status()
                return response.json().get("response", "").strip()
            except Exception as e:
                print(f"[Ollama Error] Fallback output used: {e}")
                return (
                    f"Air quality shift detected in {user.city_name} "
                    f"(Current: {detection.current}, Trend: {recent_readings}). "
                    f"Consider adjusting outdoor activities today."
                )

ollama_service = OllamaService()