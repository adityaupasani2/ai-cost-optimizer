import os
import time
import logging
import requests
from datetime import datetime, timedelta
from prometheus_client import start_http_server, Gauge, Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Prometheus Metrics ────────────────────────────────────────────────────────

llm_cost_total = Gauge(
    "llm_cost_total_usd",
    "Total LLM API cost in USD",
    ["provider", "model"]
)

llm_tokens_total = Counter(
    "llm_tokens_total",
    "Total tokens consumed",
    ["provider", "model", "type"]  # type = prompt / completion
)

llm_requests_total = Counter(
    "llm_requests_total",
    "Total API requests made",
    ["provider", "model", "status"]
)

llm_cost_per_request = Gauge(
    "llm_cost_per_request_usd",
    "Average cost per request in USD",
    ["provider", "model"]
)

llm_scrape_success = Gauge(
    "llm_exporter_scrape_success",
    "1 if last scrape succeeded, 0 if failed",
    ["provider"]
)

# ── Pricing Table (USD per 1K tokens) ────────────────────────────────────────

PRICING = {
    "openai": {
        "gpt-4o":              {"prompt": 0.005,   "completion": 0.015},
        "gpt-4o-mini":         {"prompt": 0.00015, "completion": 0.0006},
        "gpt-4-turbo":         {"prompt": 0.01,    "completion": 0.03},
        "gpt-3.5-turbo":       {"prompt": 0.0005,  "completion": 0.0015},
    },
    "anthropic": {
        "claude-3-5-sonnet":   {"prompt": 0.003,   "completion": 0.015},
        "claude-3-5-haiku":    {"prompt": 0.0008,  "completion": 0.004},
        "claude-3-opus":       {"prompt": 0.015,   "completion": 0.075},
    }
}

# ── OpenAI Fetcher ────────────────────────────────────────────────────────────

def fetch_openai_usage():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set, skipping")
        llm_scrape_success.labels(provider="openai").set(0)
        return

    try:
        date_str = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(
            f"https://api.openai.com/v1/usage?date={date_str}",
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"OpenAI API error: {response.status_code}")
            llm_scrape_success.labels(provider="openai").set(0)
            return

        data = response.json()

        for item in data.get("data", []):
            model = item.get("snapshot_id", "unknown")
            prompt_tokens = item.get("n_context_tokens_total", 0)
            completion_tokens = item.get("n_generated_tokens_total", 0)

            llm_tokens_total.labels(
                provider="openai", model=model, type="prompt"
            ).inc(prompt_tokens)

            llm_tokens_total.labels(
                provider="openai", model=model, type="completion"
            ).inc(completion_tokens)

            # Calculate cost
            pricing = PRICING["openai"].get(model, {"prompt": 0.001, "completion": 0.002})
            cost = (prompt_tokens / 1000 * pricing["prompt"]) + \
                   (completion_tokens / 1000 * pricing["completion"])

            llm_cost_total.labels(provider="openai", model=model).set(cost)

            requests_count = item.get("n_requests", 1)
            llm_requests_total.labels(
                provider="openai", model=model, status="success"
            ).inc(requests_count)

            if requests_count > 0:
                llm_cost_per_request.labels(
                    provider="openai", model=model
                ).set(cost / requests_count)

        llm_scrape_success.labels(provider="openai").set(1)
        logger.info("✅ OpenAI metrics updated")

    except Exception as e:
        logger.error(f"OpenAI fetch error: {e}")
        llm_scrape_success.labels(provider="openai").set(0)

# ── Anthropic Fetcher ─────────────────────────────────────────────────────────

def fetch_anthropic_usage():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set, skipping")
        llm_scrape_success.labels(provider="anthropic").set(0)
        return

    try:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        response = requests.get(
            "https://api.anthropic.com/v1/usage",
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"Anthropic API error: {response.status_code}")
            llm_scrape_success.labels(provider="anthropic").set(0)
            return

        data = response.json()

        for item in data.get("data", []):
            model = item.get("model", "unknown")
            prompt_tokens = item.get("input_tokens", 0)
            completion_tokens = item.get("output_tokens", 0)

            llm_tokens_total.labels(
                provider="anthropic", model=model, type="prompt"
            ).inc(prompt_tokens)

            llm_tokens_total.labels(
                provider="anthropic", model=model, type="completion"
            ).inc(completion_tokens)

            pricing = PRICING["anthropic"].get(model, {"prompt": 0.003, "completion": 0.015})
            cost = (prompt_tokens / 1000 * pricing["prompt"]) + \
                   (completion_tokens / 1000 * pricing["completion"])

            llm_cost_total.labels(provider="anthropic", model=model).set(cost)
            llm_scrape_success.labels(provider="anthropic").set(1)

        logger.info("✅ Anthropic metrics updated")

    except Exception as e:
        logger.error(f"Anthropic fetch error: {e}")
        llm_scrape_success.labels(provider="anthropic").set(0)

# ── Main Loop ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("EXPORTER_PORT", "9101"))
    interval = int(os.getenv("SCRAPE_INTERVAL", "60"))

    logger.info(f"🚀 LLM Cost Exporter starting on port {port}")
    start_http_server(port)

    while True:
        logger.info("📊 Fetching LLM usage metrics...")
        fetch_openai_usage()
        fetch_anthropic_usage()
        logger.info(f"✅ Done. Sleeping {interval}s...")
        time.sleep(interval)
