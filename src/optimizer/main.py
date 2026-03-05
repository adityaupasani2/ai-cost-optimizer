import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import CostSummary, Recommendation
from recommender import get_all_recommendations
from prometheus_client import prom

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Cost Optimizer",
    description="ML-powered cost optimization for AI/cloud infrastructure",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-cost-optimizer"}

@app.get("/recommendations", response_model=list[Recommendation])
async def recommendations():
    logger.info("Fetching recommendations...")
    return await get_all_recommendations()

@app.get("/summary", response_model=CostSummary)
async def summary():
    recs = await get_all_recommendations()

    llm_results = await prom.query('sum(llm_cost_total_usd)')
    llm_cost    = float(llm_results[0]["value"][1]) if llm_results else 0.0

    total_daily     = llm_cost + 15.0
    total_monthly   = total_daily * 30
    potential_saving = sum(r.projected_saving_usd for r in recs)

    return CostSummary(
        total_daily_cost_usd=total_daily,
        total_monthly_cost_usd=total_monthly,
        llm_cost_usd=llm_cost,
        compute_cost_usd=15.0,
        top_recommendations=recs[:5],
        potential_savings_usd=potential_saving,
        potential_savings_pct=(potential_saving / total_daily * 100) if total_daily > 0 else 0
    )

@app.get("/anomalies")
async def anomalies():
    results = await prom.query('''
        sum by (model) (
            rate(llm_cost_total_usd[1h]) > 
            avg_over_time(llm_cost_total_usd[7d]) * 1.5
        )
    ''')
    return {"anomalies": results, "count": len(results)}

@app.get("/forecast")
async def forecast():
    return {
        "message": "Forecast endpoint — Prophet model runs here in Phase 3b",
        "status": "coming_soon"
    }
