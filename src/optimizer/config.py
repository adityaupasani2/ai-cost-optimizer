from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    prometheus_url: str = "http://kube-prometheus-stack-prometheus.monitoring.svc.cluster.local:9090"
    scrape_interval_seconds: int = 300
    cost_threshold_usd: float = 10.0
    cpu_waste_threshold: float = 0.3
    memory_waste_threshold: float = 0.3
    aws_region: str = "us-east-1"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
