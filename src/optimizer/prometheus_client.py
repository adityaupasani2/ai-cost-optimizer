import httpx
import logging
from datetime import datetime, timedelta
from config import settings

logger = logging.getLogger(__name__)

class PrometheusClient:
    def __init__(self):
        self.base_url = settings.prometheus_url

    async def query(self, promql: str) -> list:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/query",
                    params={"query": promql}
                )
                data = response.json()
                if data["status"] == "success":
                    return data["data"]["result"]
                return []
        except Exception as e:
            logger.error(f"Prometheus query error: {e}")
            return []

    async def query_range(self, promql: str, hours: int = 24) -> list:
        try:
            end   = datetime.utcnow()
            start = end - timedelta(hours=hours)
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/query_range",
                    params={
                        "query": promql,
                        "start": start.timestamp(),
                        "end":   end.timestamp(),
                        "step":  "5m"
                    }
                )
                data = response.json()
                if data["status"] == "success":
                    return data["data"]["result"]
                return []
        except Exception as e:
            logger.error(f"Prometheus range query error: {e}")
            return []

prom = PrometheusClient()
