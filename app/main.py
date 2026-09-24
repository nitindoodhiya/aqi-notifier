import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from typing import List, Dict
from datetime import datetime
from pydantic import BaseModel

from app.schemas import UserConfig, AQIReading, AuditLog, MockInjectRequest
from app.services.openaq_service import openaq_service
from app.services.detection_service import detection_service
from app.services.ollama_service import ollama_service
from app.services.rate_limiter import rate_limiter
from app.services.evaluation_service import evaluation_service

app = FastAPI(title="Proactive Air Quality Insight Agent")

USERS = [
    UserConfig(user_id="user_1", city_name="Los Angeles", location_id=2178, baseline_sensitivity=0.8),
    UserConfig(user_id="user_2", city_name="London", location_id=1044, baseline_sensitivity=0.7),
    UserConfig(user_id="user_3", city_name="Delhi", location_id=8023, baseline_sensitivity=1.5),
]

history_store: Dict[int, List[AQIReading]] = {}
audit_logs: List[AuditLog] = []

# ==========================================
# WEB APP FRONTEND ROUTE
# ==========================================

@app.get("/")
async def serve_dashboard():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    return FileResponse(template_path)

# ==========================================
# API ENDPOINTS
# ==========================================

@app.post("/api/trigger-cycle")
async def run_cycle():
    for user in USERS:
        val = await openaq_service.fetch_latest_aqi(user.location_id)
        if val is None:
            continue
        await process_reading(user, val)
    return {"status": "Complete", "logs_count": len(audit_logs)}

@app.post("/api/mock-reading")
async def mock_reading(payload: MockInjectRequest):
    user = next((u for u in USERS if u.location_id == payload.location_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    log_entry = await process_reading(user, payload.value)
    return log_entry

class EvaluationRequest(BaseModel):
    user: UserConfig
    data_points: List[float]

@app.post("/api/evaluate")
async def evaluate_dataset(req: EvaluationRequest):
    """
    Offline evaluation harness endpoint to replay datasets through detection logic.
    """
    return evaluation_service.replay_dataset(req.user, req.data_points)

@app.get("/api/logs")
async def get_logs():
    return {"logs": audit_logs, "active_states": rate_limiter.state}

async def process_reading(user: UserConfig, val: float) -> AuditLog:
    if user.location_id not in history_store:
        history_store[user.location_id] = []
    
    history_store[user.location_id].append(AQIReading(timestamp=datetime.utcnow(), value=val))
    if len(history_store[user.location_id]) > 24:
        history_store[user.location_id].pop(0)

    history = history_store[user.location_id]
    last_state = rate_limiter.get_last_fired_state(user.location_id)
    detection = detection_service.evaluate(user, history, last_state)
    
    status = "NO_ACTION"
    message = None

    
    if detection.trigger:
        
        # 1. Rate limit or fire notification
        if rate_limiter.is_rate_limited(user.location_id, detection.type):
            status = "RATE_LIMITED"
            message = f"[{detection.type}] Notification suppressed due to active cooldown."
        else:
            status = "FIRED"
            message = await ollama_service.generate_notification(user, detection, history)
            rate_limiter.update_state(user.location_id, detection.type)
        # 2. Record notification time for cooldown tracking
            rate_limiter.record_notification_sent(user.location_id, detection.type)
    rate_limiter.set_last_event(user.location_id, detection.type)

    log_entry = AuditLog(
        id=f"log_{int(datetime.utcnow().timestamp())}_{user.user_id}",
        timestamp=datetime.utcnow(),
        user_id=user.user_id,
        city=user.city_name,
        current_reading=val,
        detection=detection,
        status=status,
        message=message
    )
    audit_logs.insert(0, log_entry)
    return log_entry