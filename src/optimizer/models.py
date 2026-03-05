from pydantic import BaseModel
from typing import Optional
from enum import Enum

class RecommendationType(str, Enum):
    RIGHTSIZE     = "rightsize"
    SPOT          = "spot_instance"
    LLM_SWITCH    = "llm_model_switch"
    IDLE_RESOURCE = "idle_resource"
    SCALE_DOWN    = "scale_down"

class Severity(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"

class Recommendation(BaseModel):
    id:                  str
    type:                RecommendationType
    severity:            Severity
    title:               str
    description:         str
    resource:            str
    namespace:           Optional[str] = None
    current_cost_usd:    float
    projected_saving_usd: float
    saving_percentage:   float
    action:              str

class CostSummary(BaseModel):
    total_daily_cost_usd:     float
    total_monthly_cost_usd:   float
    llm_cost_usd:             float
    compute_cost_usd:         float
    top_recommendations:      list[Recommendation]
    potential_savings_usd:    float
    potential_savings_pct:    float
