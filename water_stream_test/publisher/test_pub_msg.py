import os
import random

import faust


APP_NAME = os.getenv('APP_NAME', 'sensor_data_publisher')
KAFKA_BROKER_CONNECT = os.getenv('KAFKA_BROKER_CONNECT', 'kafka://127.0.0.1:9093')
PUB_TOPIC_NAME = os.getenv('PUB_TOPIC_NAME', 'water_sensor_data')

app = faust.App(
    APP_NAME,
    broker=KAFKA_BROKER_CONNECT,
    version=1,
    topic_partitions=1,
)

pub_topic = app.topic(PUB_TOPIC_NAME, key_type=str, value_serializer='json')


@app.timer(1.0)
async def produce():
    await pub_topic.send(key=random.choice(['1', '2', '3']), value={'value': round(random.random(), 2)})


if __name__ == '__main__':
    app.main()
