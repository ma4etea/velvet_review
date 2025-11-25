from redis.asyncio import Redis
from redis.asyncio.client import Pipeline


class CustomRedis(Redis): ...


class CustomPipeline(Pipeline): ...
