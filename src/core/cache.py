from langchain_redis import RedisCache
from langchain_classic.globals import set_llm_cache
from src.core.config import settings


def init_llm_cache():
    redis_cache = RedisCache(
        redis_url=settings.redis_url,
        ttl=None,
    )

    set_llm_cache(redis_cache)
