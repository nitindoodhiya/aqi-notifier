from typing import List, Optional
from app.schemas import UserConfig, AQIReading, DetectionResult

class DetectionService:
    def __init__(self):
        self.SPIKE_MULTIPLIER = 1.4           # Current reading > 1.4x baseline average
        self.DROP_MULTIPLIER = 0.6            # Current reading < 0.6x baseline average
        self.BASE_TREND_THRESHOLD = 15.0       # Cumulative shift over window
        self.NORMAL_AQI_THRESHOLD = 35.0       # Safe threshold to consider "normal"

    def evaluate(
        self, 
        user: UserConfig, 
        history: List[AQIReading], 
        last_state: Optional[str] = None
    ) -> DetectionResult:
        if not history or len(history) <= 2:
            return self._no_action(user, history)

        current_val = history[-1].value
        prev_val = history[-2].value
        baseline_avg = round(sum(r.value for r in history[:-1]) / len(history[:-1]), 2)

        # ------------------------------------------------------------------
        # CALCULATE THRESHOLDS (FIXED)
        # ------------------------------------------------------------------
        spike_threshold = max((baseline_avg * self.SPIKE_MULTIPLIER) / user.baseline_sensitivity, 40.0)
        
        # Lower sensitivity = harder to trigger drop (lower target)
        calculated_drop_target = (baseline_avg * self.DROP_MULTIPLIER) * user.baseline_sensitivity
        
        # Use min() so high previous values don't inflate the lower threshold
        drop_threshold = min(calculated_drop_target, prev_val * 0.75)
        # drop if current_val + drop_threshold <= prev_val
        
        sustained_threshold = self.BASE_TREND_THRESHOLD * user.baseline_sensitivity

        def build_result(trigger: bool, event_type: Optional[str], reason: str) -> DetectionResult:
            return DetectionResult(
                trigger=trigger,
                type=event_type,
                current=current_val,
                baseline_avg=baseline_avg,
                spike_threshold=0,
                drop_threshold=0,
                sustained_threshold=0,
                reason=reason
            )

        # ------------------------------------------------------------------
        # RULE 1: Sudden Spike
        # ------------------------------------------------------------------
        if current_val > spike_threshold and current_val > (prev_val * 1.25):
            return build_result(
                trigger=True,
                event_type="SUDDEN_SPIKE",
                reason=f"Sudden spike detected: Current value {current_val} jumped from previous ({prev_val})."
            )

        # ------------------------------------------------------------------
        # RULE 2: Return to Normal / Recovery
        # ------------------------------------------------------------------
        #elevated_states = ["SUDDEN_SPIKE", "SUSTAINED_INCREASE", "SUDDEN_DROP", "SUSTAINED_DECREASE"]
        if current_val <= self.NORMAL_AQI_THRESHOLD:
            return build_result(
                trigger= last_state != None,
                event_type= None if last_state == None else "RETURN_TO_NORMAL",
                reason=f"Air quality returned to normal safe level ({current_val} AQI)."
            )

        # ------------------------------------------------------------------
        # RULE 3: Sudden Drop
        # ------------------------------------------------------------------
        if current_val <= drop_threshold and current_val <= (prev_val * 0.75):
            return build_result(
                trigger=True,
                event_type="SUDDEN_DROP",
                reason=f"Sudden drop detected: Current value {current_val} dropped sharply from previous ({prev_val})."
            )

        # ------------------------------------------------------------------
        # RULE 4: Sustained Trend
        # ------------------------------------------------------------------
        trend_result = self._evaluate_sustained_trend(user, history, baseline_avg, spike_threshold, drop_threshold, sustained_threshold)
        if trend_result and trend_result.trigger:
            return trend_result

        # ------------------------------------------------------------------
        # DEFAULT: Normal / No Action
        # ------------------------------------------------------------------
        return build_result(
            trigger=False,
            event_type=None,
            reason="Air quality levels within normal baseline operating range."
        )

    def _evaluate_sustained_trend(
        self, 
        user: UserConfig, 
        history: List[AQIReading], 
        baseline_avg: float,
        spike_thresh: float,
        drop_thresh: float,
        sustained_thresh: float,
        window_size: int = 4
    ) -> Optional[DetectionResult]:
        if len(history) < window_size:
            return None

        window = [r.value for r in history[-window_size:]]
        deltas = [window[i] - window[i - 1] for i in range(1, len(window))]

        is_sustained_up = all(d >= 0 for d in deltas) and (window[-1] > window[0])
        is_sustained_down = all(d <= 0 for d in deltas) and (window[-1] < window[0])

        if not (is_sustained_up or is_sustained_down):
            return None

        total_change = window[-1] - window[0]

        if abs(total_change) >= sustained_thresh:
            direction = "INCREASE" if is_sustained_up else "DECREASE"
            return DetectionResult(
                trigger=True,
                type=f"SUSTAINED_{direction}",
                current=window[-1],
                baseline_avg=baseline_avg,
                spike_threshold=round(spike_thresh, 1),
                drop_threshold=round(drop_thresh, 1),
                sustained_threshold=round(sustained_thresh, 1),
                reason=(
                    f"Sustained {direction.lower()} across last {window_size} readings. "
                    f"Total shift: {total_change:+.1f} AQI."
                )
            )

        return None

    def _no_action(self, user: UserConfig, history: List[AQIReading]) -> DetectionResult:
        current_val = history[-1].value if history else 0.0
        baseline_avg = round(sum(r.value for r in history) / len(history), 2) if history else 0.0
        prev_val = history[-2].value if len(history) >= 2 else current_val
        
        spike_threshold = max((baseline_avg * self.SPIKE_MULTIPLIER) / user.baseline_sensitivity, 40.0)
        
        # Calculate drop threshold using min()
        calculated_drop_target = (baseline_avg * self.DROP_MULTIPLIER) * user.baseline_sensitivity
        drop_threshold = min(calculated_drop_target, prev_val * 0.75)
        
        sustained_threshold = self.BASE_TREND_THRESHOLD * user.baseline_sensitivity

        return DetectionResult(
            trigger=False,
            type=None,
            current=current_val,
            baseline_avg=baseline_avg,
            spike_threshold=round(spike_threshold, 1),
            drop_threshold=round(drop_threshold, 1),
            sustained_threshold=round(sustained_thresh, 1) if 'sustained_thresh' in locals() else round(sustained_threshold, 1),
            reason="Insufficient history to determine trend."
        )

detection_service = DetectionService()