from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserConfig(BaseModel):
    user_id: str
    city_name: str
    location_id: int
    baseline_sensitivity: float

class AQIReading(BaseModel):
    timestamp: datetime
    value: float

class DetectionResult(BaseModel):
    trigger: bool
    type: Optional[str] = None
    current: float
    baseline_avg: float
    spike_threshold: float
    drop_threshold: float
    sustained_threshold: float
    reason: str

class AuditLog(BaseModel):
    id: str
    timestamp: datetime
    user_id: str
    city: str
    current_reading: float
    detection: DetectionResult
    status: str  # 'FIRED', 'RATE_LIMITED', 'NO_ACTION'
    message: Optional[str] = None

class MockInjectRequest(BaseModel):
    location_id: int
    value: float