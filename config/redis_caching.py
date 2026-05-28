import os

from redis.asyncio import Redis

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://redis:6379/1",
)

CACHE_TTL_SECONDS = int(os.getenv("REDIS_TTL_SECONDS", "120"))

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)


async def clear_products_routers_cache():
    async for key in redis_client.scan_iter("products_router:*"):
        await redis_client.delete(key)
        
async def clear_orders_routers_cache():
    async for key in redis_client.scan_iter("orders_router:*"):
        await redis_client.delete(key)
    async for key in redis_client.scan_iter("orders:*"):
        await redis_client.delete(key)
        
async def clear_category_routers_cache():
    async for key in redis_client.scan_iter("categories_router:*"):
        await redis_client.delete(key)