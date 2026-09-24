from typing import List, Dict, Any
from datetime import datetime
from app.schemas import UserConfig, AQIReading
from app.services.detection_service import detection_service

class EvaluationService:
    def replay_dataset(self, user: UserConfig, mock_data_points: List[float]) -> Dict[str, Any]:
        history: List[AQIReading] = []
        last_state = None
        fired_events = []
        missed_or_ignored = 0

        for val in mock_data_points:
            history.append(AQIReading(timestamp=datetime.utcnow(), value=val))
            result = detection_service.evaluate(user, history, last_state)
            
            if result.trigger:
                fired_events.append({"value": val, "type": result.type})
                last_state = result.type
            else:
                missed_or_ignored += 1

        return {
            "total_points_evaluated": len(mock_data_points),
            "events_fired": len(fired_events),
            "fired_details": fired_events,
            "ignored_points": missed_or_ignored
        }

evaluation_service = EvaluationService()