import uuid
import logging
from models import Recommendation, RecommendationType, Severity
from prometheus_client import prom

logger = logging.getLogger(__name__)

# ── LLM Cost Recommendations ──────────────────────────────────────────────────

async def check_llm_costs() -> list[Recommendation]:
    recommendations = []

    results = await prom.query('sum by (model) (llm_cost_total_usd)')

    for result in results:
        model = result["metric"].get("model", "unknown")
        cost  = float(result["value"][1])

        # If using GPT-4 heavily, suggest GPT-4o-mini
        if "gpt-4-turbo" in model and cost > 5.0:
            saving = cost * 0.85
            recommendations.append(Recommendation(
                id=str(uuid.uuid4()),
                type=RecommendationType.LLM_SWITCH,
                severity=Severity.HIGH,
                title=f"Switch {model} to gpt-4o-mini",
                description=f"You're spending ${cost:.2f}/day on {model}. GPT-4o-mini handles 80% of tasks at 97% lower cost.",
                resource=model,
                current_cost_usd=cost,
                projected_saving_usd=saving,
                saving_percentage=85.0,
                action=f"Replace model='{model}' with model='gpt-4o-mini' for non-complex tasks"
            ))

        # If using gpt-4o heavily, suggest batching
        if "gpt-4o" in model and cost > 10.0:
            saving = cost * 0.5
            recommendations.append(Recommendation(
                id=str(uuid.uuid4()),
                type=RecommendationType.LLM_SWITCH,
                severity=Severity.MEDIUM,
                title=f"Enable batch API for {model}",
                description=f"Using OpenAI Batch API gives 50% discount for non-realtime tasks.",
                resource=model,
                current_cost_usd=cost,
                projected_saving_usd=saving,
                saving_percentage=50.0,
                action="Use /v1/batches endpoint for async workloads"
            ))

    return recommendations

# ── Kubernetes Right-sizing ───────────────────────────────────────────────────

async def check_rightsizing() -> list[Recommendation]:
    recommendations = []

    # CPU waste: requested vs actual usage
    results = await prom.query('''
        sum by (namespace, pod) (
            rate(container_cpu_usage_seconds_total{container!=""}[5m])
        ) /
        sum by (namespace, pod) (
            kube_pod_container_resource_requests{resource="cpu"}
        ) < 0.3
    ''')

    for result in results:
        namespace = result["metric"].get("namespace", "default")
        pod       = result["metric"].get("pod", "unknown")
        ratio     = float(result["value"][1])
        waste_pct = (1 - ratio) * 100

        if waste_pct > 50:
            recommendations.append(Recommendation(
                id=str(uuid.uuid4()),
                type=RecommendationType.RIGHTSIZE,
                severity=Severity.MEDIUM,
                title=f"Overprovisioned pod: {pod}",
                description=f"Pod {pod} in {namespace} is using only {ratio*100:.1f}% of requested CPU. Reduce requests by {waste_pct:.0f}%.",
                resource=pod,
                namespace=namespace,
                current_cost_usd=2.0,
                projected_saving_usd=2.0 * (waste_pct / 100),
                saving_percentage=waste_pct,
                action=f"kubectl set resources deployment -n {namespace} --requests=cpu={int(ratio*100)}m"
            ))

    return recommendations

# ── Idle Resources ────────────────────────────────────────────────────────────

async def check_idle_resources() -> list[Recommendation]:
    recommendations = []

    results = await prom.query('''
        sum by (namespace, pod) (
            rate(container_cpu_usage_seconds_total{container!=""}[30m])
        ) < 0.001
    ''')

    for result in results:
        namespace = result["metric"].get("namespace", "default")
        pod       = result["metric"].get("pod", "unknown")

        # Skip system pods
        if namespace in ["kube-system", "monitoring"]:
            continue

        recommendations.append(Recommendation(
            id=str(uuid.uuid4()),
            type=RecommendationType.IDLE_RESOURCE,
            severity=Severity.HIGH,
            title=f"Idle pod detected: {pod}",
            description=f"Pod {pod} has had near-zero CPU usage for 30+ minutes.",
            resource=pod,
            namespace=namespace,
            current_cost_usd=1.5,
            projected_saving_usd=1.5,
            saving_percentage=100.0,
            action=f"kubectl scale deployment -n {namespace} --replicas=0"
        ))

    return recommendations

# ── Main entry point ──────────────────────────────────────────────────────────

async def get_all_recommendations() -> list[Recommendation]:
    llm    = await check_llm_costs()
    right  = await check_rightsizing()
    idle   = await check_idle_resources()
    all_recs = llm + right + idle
    all_recs.sort(key=lambda r: r.projected_saving_usd, reverse=True)
    return all_recs
