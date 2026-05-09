from redis.asyncio import Redis

redis_client=Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)


async def clear_products_routers_cache():
    async for key in redis_client.scan_iter("products_router:*"):
        await redis_client.delete(key)
        
async def clear_orders_routers_cache():
    async for key in redis_client.scan_iter("orders_router:*"):
        await redis_client.delete(key)
        
async def clear_category_routers_cache():
    async for key in redis_client.scan_iter("categories_router:*"):
        await redis_client.delete(key)