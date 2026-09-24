from abc import ABC, abstractmethod
from typing import List, Optional
from app.schemas import UserConfig, AQIReading, DetectionResult


# ------------------------------------------------------------------
# 1. Flow Context (State & Memory passed down the pipeline)
# ------------------------------------------------------------------
class FlowContext:
    def __init__(self, user: UserConfig, history: List[AQIReading], last_fired_state: Optional[str]):
        self.user = user
        self.history = history
        self.last_fired_state = last_fired_state

        self.current_val: float = history[-1].value if history else 0.0
        self.prev_val: float = history[-2].value if len(history) >= 2 else self.current_val
        self.baseline_avg: float = (
            round(sum(r.value for r in history[:-1]) / len(history[:-1]), 2)
            if len(history) > 1 else 0.0
        )
        self.result: Optional[DetectionResult] = None


# ------------------------------------------------------------------
# 2. Abstract Flowchart Node Base Class
# ------------------------------------------------------------------
class FlowNode(ABC):
    @abstractmethod
    def evaluate(self, ctx: FlowContext) -> bool:
        """
        Evaluates step logic. 
        Returns True to HALT the flowchart (event found), 
        or False to PASS control to the next node.
        """
        pass


# ------------------------------------------------------------------
# Node A: Sudden Spike Check
# ------------------------------------------------------------------
class SpikeNode(FlowNode):
    def __init__(self, spike_multiplier: float = 1.5, absolute_min_aqi: float = 50.0):
        self.spike_multiplier = spike_multiplier
        self.absolute_min_aqi = absolute_min_aqi

    def evaluate(self, ctx: FlowContext) -> bool:
        spike_thresh = (ctx.baseline_avg * self.spike_multiplier) / ctx.user.baseline_sensitivity

        # Noise Suppression: Require a higher jump if already in a active SUDDEN_SPIKE state
        if ctx.last_fired_state == "SUDDEN_SPIKE":
            is_valid_jump = ctx.current_val > (ctx.prev_val * 1.05)
        else:
            is_valid_jump = ctx.current_val > ctx.prev_val

        if ctx.current_val > max(spike_thresh, self.absolute_min_aqi) and is_valid_jump:
            ctx.result = DetectionResult(
                trigger=True,
                type="SUDDEN_SPIKE",
                current=ctx.current_val,
                baseline_avg=ctx.baseline_avg,
                reason=f"[Node: Spike] Reading ({ctx.current_val}) exceeded threshold ({spike_thresh:.1f})."
            )
            return True  # Halt execution

        return False  # Pass to next node


# ------------------------------------------------------------------
# Node B: Sustained Trend Check
# ------------------------------------------------------------------
class SustainedTrendNode(FlowNode):
    def __init__(self, window_size: int = 4, base_trend_threshold: float = 15.0):
        self.window_size = window_size
        self.base_trend_threshold = base_trend_threshold

    def evaluate(self, ctx: FlowContext) -> bool:
        if len(ctx.history) < self.window_size:
            return False

        window = [r.value for r in ctx.history[-self.window_size:]]
        deltas = [window[i] - window[i - 1] for i in range(1, len(window))]

        # Monotonic directional checks allowing plateau steps
        is_up = all(d >= 0 for d in deltas) and (window[-1] > window[0])
        is_down = all(d <= 0 for d in deltas) and (window[-1] < window[0])

        if not (is_up or is_down):
            return False

        total_shift = window[-1] - window[0]
        adjusted_thresh = self.base_trend_threshold * ctx.user.baseline_sensitivity

        if abs(total_shift) >= adjusted_thresh:
            direction = "INCREASE" if is_up else "DECREASE"
            ctx.result = DetectionResult(
                trigger=True,
                type=f"SUSTAINED_{direction}",
                current=ctx.current_val,
                baseline_avg=ctx.baseline_avg,
                reason=f"[Node: Trend] Sustained {direction.lower()} shift of {total_shift:+.1f} AQI across window."
            )
            return True  # Halt execution

        return False  # Pass to next node


# ------------------------------------------------------------------
# Node C: Recovery Check (Return to Normal)
# ------------------------------------------------------------------
class RecoveryNode(FlowNode):
    def __init__(self, safe_aqi_threshold: float = 35.0):
        self.safe_threshold = safe_aqi_threshold

    def evaluate(self, ctx: FlowContext) -> bool:
        elevated_states = ["SUDDEN_SPIKE", "SUSTAINED_INCREASE"]
        
        # Trigger recovery ONLY if previous active state was an elevated alert
        if ctx.last_fired_state in elevated_states and ctx.current_val <= self.safe_threshold:
            ctx.result = DetectionResult(
                trigger=True,
                type="RETURN_TO_NORMAL",
                current=ctx.current_val,
                baseline_avg=ctx.baseline_avg,
                reason=f"[Node: Recovery] AQI dropped to {ctx.current_val}, recovering below safe limit ({self.safe_threshold})."
            )
            return True  # Halt execution

        return False  # Pass to next node


# ------------------------------------------------------------------
# 3. Flowchart Engine Pipeline (Orchestrator)
# ------------------------------------------------------------------
class FlowchartEngine:
    def __init__(self):
        # Defines the exact flowchart node execution sequence
        self.nodes: List[FlowNode] = [
            SpikeNode(),
            SustainedTrendNode(),
            RecoveryNode()
        ]

    def evaluate(
        self, 
        user: UserConfig, 
        history: List[AQIReading], 
        last_fired_state: Optional[str]
    ) -> DetectionResult:
        if not history or len(history) < 2:
            return self._default_no_action(history)

        ctx = FlowContext(user, history, last_fired_state)

        # Traverse the flowchart steps sequentially
        for node in self.nodes:
            if node.evaluate(ctx):
                return ctx.result  # Early exit upon step match

        # If all nodes evaluate to False
        return self._default_no_action(history)

    def _default_no_action(self, history: List[AQIReading]) -> DetectionResult:
        current_val = history[-1].value if history else 0.0
        avg_val = round(sum(r.value for r in history) / len(history), 2) if history else 0.0
        return DetectionResult(
            trigger=False,
            type=None,
            current=current_val,
            baseline_avg=avg_val,
            reason="[Flowchart: Terminal] Air quality within normal baseline parameter limits."
        )


detection_service = FlowchartEngine()