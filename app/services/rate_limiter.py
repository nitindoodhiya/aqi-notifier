from typing import Dict, Optional, Any
from datetime import datetime, timedelta

class RateLimiterService:
    def __init__(self, cooldown_hours: int = 4):
        self.cooldown = timedelta(hours=cooldown_hours)
        self.last_notified_timestamps: Dict[str, datetime] = {}
        self.last_state: Dict[int, Optional[str]] = {}
        # Metadata storage for frontend API
        self.state: Dict[int, Dict[str, Any]] = {}

    def get_last_fired_state(self, location_id: int) -> Optional[str]:
        return self.last_state.get(location_id)

    def set_last_event(self, location_id: int, event_type: Optional[str] = None):
        self.last_state[location_id] = event_type

    def update_state(self, location_id: int, event_type: Optional[str]):
        """
        Updates the active system state and handles cooldown resets on recovery.
        """
        if event_type == "RETURN_TO_NORMAL" and self.get_last_fired_state(location_id) != None:
            # Clear all previous cooldown timers for this location upon recovery
            keys_to_clear = [k for k in self.last_notified_timestamps if k.startswith(f"{location_id}_")]
            for k in keys_to_clear:
                del self.last_notified_timestamps[k]
        self.last_state[location_id] = event_type

    def is_rate_limited(self, location_id: int, event_type: str) -> bool:
        """
        Checks if an alert notification should be suppressed based on cooldown rules.
        """

        key = f"{location_id}"
        last_time = self.last_notified_timestamps.get(key)
        print(
            f"state={self.get_last_fired_state(location_id)}, "
            f"event_type={event_type}, "
            f"last_time={last_time}, "
            f"within_cooldown={last_time}"
        )
        if self.get_last_fired_state(location_id) == event_type and last_time and (datetime.utcnow() - last_time) < self.cooldown:
            return True

        return False

    def record_notification_sent(self, location_id: int, event_type: str):
        """
        Records the timestamp when an LLM notification is actually sent.
        """
        key = f"{location_id}"
        self.last_notified_timestamps[key] = datetime.utcnow()
        self.state[location_id] = {
            "last_state": event_type,
            "last_notified_at": datetime.utcnow().isoformat()
        }

rate_limiter = RateLimiterService()