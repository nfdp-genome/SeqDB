from arq.connections import RedisSettings
from app.config import settings


async def run_qc_job(ctx, run_id: int):
    """Execute QC for a given run. Called by arq worker."""
    pass


class WorkerSettings:
    functions = [run_qc_job]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
