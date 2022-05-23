import os
import datetime

import faust

WINDOW_CHANGELOG_TOPIC_NAME = os.getenv('WINDOW_CHANGELOG_TOPIC_NAME', 'water_sensor_data_count_changelog')
SUB_TOPIC_NAME = os.getenv('SUB_TOPIC_NAME', 'water_sensor_data')
APP_NAME = os.getenv('APP_NAME', 'water_stream_window')
KAFKA_BROKER_CONNECT = os.getenv('KAFKA_BROKER_CONNECT', 'kafka://127.0.0.1:9093')
WINDOW_SIZE_SECONDS = os.getenv('WINDOW_SIZE_SECONDS', 60)

app = faust.App(
    APP_NAME,
    broker=KAFKA_BROKER_CONNECT,
    version=1,
    topic_partitions=1,
)

sub_topic = app.topic(SUB_TOPIC_NAME, key_type=str, value_serializer='json')


async def on_changelog_event(event):
    print(event)

table = app.Table(
    APP_NAME,
    default=int,
    on_changelog_event=on_changelog_event,
    changelog_topic=app.topic(WINDOW_CHANGELOG_TOPIC_NAME, key_type=str, value_type=int),
)
table._changelog_topic_name = lambda: WINDOW_CHANGELOG_TOPIC_NAME
window = table.tumbling(datetime.timedelta(seconds=WINDOW_SIZE_SECONDS)).relative_to_stream()


@app.agent(sub_topic)
async def consume(stream):
    async for key, _ in stream.items():
        window[key] += 1

if __name__ == '__main__':
    app.main()
