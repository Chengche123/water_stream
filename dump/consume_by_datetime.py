import os
import sys
import json
import argparse
from datetime import datetime

import jsonlines
import dateparser
from kafka import KafkaConsumer, TopicPartition


KAFKA_BROKER_HOST = os.getenv('KAFKA_BROKER_CONNECT', '127.0.0.1:9093')
SUB_TOPIC_NAME = os.getenv('SUB_TOPIC_NAME', 'water_sensor_data')
DUMP_PATH = os.getenv('DUMP_PATH', 'dump/')


def consumer_by_datetime(begin_datetime: datetime, end_datetime: datetime):

    results = []

    try:
        consumer = KafkaConsumer(
            bootstrap_servers=KAFKA_BROKER_HOST,
            enable_auto_commit=True,
            key_deserializer=lambda m: m.decode('utf-8'),
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        )

        tp0 = TopicPartition(SUB_TOPIC_NAME, 0)
        consumer.assign([tp0])

        begin_timestamp = begin_datetime.timestamp() * 1000
        end_timestamp = end_datetime.timestamp() * 1000

        tp0_from_offset = consumer.offsets_for_times({tp0: begin_timestamp})[tp0]
        if not tp0_from_offset:
            return results
        from_offset = tp0_from_offset.offset

        end_offset = None
        is_end_datetime_ahead = False  # 结束时间是否超前
        tp0_end_offset = consumer.offsets_for_times({tp0: end_timestamp})[tp0]
        if not tp0_end_offset:
            last_record_offset = consumer.end_offsets([tp0])[tp0] - 1
            consumer.seek(tp0, last_record_offset)
            records = consumer.poll(100, max_records=1)
            last_record_datetime = datetime.fromtimestamp(records[tp0][0].timestamp / 1000)
            if end_datetime >= last_record_datetime:
                is_end_datetime_ahead = True
                end_offset = last_record_offset
        else:
            end_offset = tp0_end_offset.offset

        if not end_offset:
            return results

        consumer.seek(tp0, from_offset)

        last_delay_timestamp = 0 if is_end_datetime_ahead else end_timestamp + 1000
        for record in consumer:
            if record.offset >= end_offset:
                record_timestamp = record.timestamp
                if record_timestamp > last_delay_timestamp:
                    break
                if record_timestamp > end_timestamp or record_timestamp < begin_timestamp:
                    continue

            results.append({
                'offset': record.offset,
                'key': record.key,
                'value': record.value,
                'datetime': datetime.fromtimestamp(record.timestamp / 1000).isoformat(),
            })

        return results

    finally:
        consumer.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # 时间格式: https://github.com/scrapinghub/dateparser/blob/master/tests/test_date_parser.py
    parser.add_argument('-b', type=dateparser.parse, help='开始时间', required=True)
    parser.add_argument('-e', type=dateparser.parse, help='结束时间', required=True)
    parser.add_argument('--output', type=str, help="输出文件")

    args = parser.parse_args()
    assert args.b, '开始时间格式不正确'
    assert args.e, '结束时间格式不正确'
    assert args.b <= args.e, '开始时间必须小于等于结束时间'

    results = consumer_by_datetime(args.b, args.e)

    if not results:
        print('no records')
        sys.exit(0)

    filename = args.output or f'{results[0]["offset"]}-{results[-1]["offset"]}.jl'
    os.makedirs(DUMP_PATH, exist_ok=True)
    filepath = os.path.join('dump/', filename)

    with jsonlines.open(filepath, mode='w') as writer:
        for json_data in results:
            writer.write(json_data)
