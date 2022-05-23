import os
import datetime

import faust
from redis import asyncio as aioredis
from pymongo.mongo_client import MongoClient

import models


REDIS_HOST = os.getenv('REDIS_HOST', 'redis://127.0.0.1:6380')
MONGO_HOST = os.getenv('MONGO_HOST', 'mongodb://root:root@127.0.0.1:27017')

WINDOW_CHANGELOG_TOPIC_NAME = os.getenv('WINDOW_CHANGELOG_TOPIC_NAME', 'water_sensor_data_count_changelog')
APP_NAME = os.getenv('APP_NAME', 'water_stream_flush')
KAFKA_BROKER_CONNECT = os.getenv('KAFKA_BROKER_CONNECT', 'kafka://127.0.0.1:9093')
WINDOW_SIZE_SECONDS = os.getenv('WINDOW_SIZE_SECONDS', 60)

CACHE_EXPIRE_SECONDS = os.getenv('CACHE_EXPIRE_SECONDS', 600)
CACHE_DELETE_DELAY_SECONDS = os.getenv('CACHE_DELETE_DELAY_SECONDS', 30)
assert CACHE_DELETE_DELAY_SECONDS <= CACHE_EXPIRE_SECONDS

MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'water')
MONGO_COLLECTION = os.getenv('MONGO_COLLECTION', 'count')
MONGO_FLUSH_INTERVAL = os.getenv('MONGO_FLUSH_INTERVAL', 10)


class MyApp(faust.App):

    @property
    def _mongo(self):
        return MongoClient(MONGO_HOST)

    @property
    def mongo_coll(self):
        return self._mongo[MONGO_DATABASE][MONGO_COLLECTION]

    @property
    def redis(self):
        return aioredis.from_url(REDIS_HOST)

    async def on_stop(self):
        self._mongo.close()
        await self.redis.close()

        await super().on_stop()


app = MyApp(
    APP_NAME,
    broker=KAFKA_BROKER_CONNECT,
    version=1,
    topic_partitions=1,
)

changelog_topic = app.topic(WINDOW_CHANGELOG_TOPIC_NAME, key_type=str, value_type=int)


@app.agent(changelog_topic)
async def consume(stream):

    redis = app.redis
    cache_expire_seconds = datetime.timedelta(seconds=CACHE_EXPIRE_SECONDS)

    async for key, value in stream.items():
        await redis.set(key, value, ex=cache_expire_seconds)


@app.timer(MONGO_FLUSH_INTERVAL)
async def flush():

    redis = app.redis
    mongo_coll = app.mongo_coll

    async for key in redis.scan_iter():

        ttl = await redis.ttl(key)

        if CACHE_EXPIRE_SECONDS - ttl < CACHE_DELETE_DELAY_SECONDS:
            continue

        value = await redis.get(key)
        print(f'key = {key}, value = {value}, ttl = {ttl}')

        sensor_data_count = models.SensorDataCount.from_cache(key, value)
        mongo_coll.update_one(
            filter=sensor_data_count.as_filter_dict(),
            update=sensor_data_count.as_update_dict(),
            upsert=True,
        )

        await redis.delete(key)


if __name__ == '__main__':
    app.main()
