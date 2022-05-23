import os
import ast
from functools import partial
from typing import List, Optional, Union
from dataclasses import dataclass, asdict


BUCKET_MAX_COUNT = os.getenv('BUCKET_MAX_COUNT', 60)


asdict = partial(asdict, dict_factory=lambda x: {k: v for k, v in x if v is not None})


def to_snake_case(x):
    import re
    return re.sub('(?<=[a-z])[A-Z]|(?<!^)[A-Z](?=[a-z])', '_\g<0>', x).lower()


@dataclass
class Count:

    timestamp_after: Optional[float] = None
    timestamp_before: Optional[float] = None
    count: Optional[int] = None

    @classmethod
    def from_cache(cls, key, value):
        key = key.decode('utf-8') if isinstance(key, bytes) else key
        value = value.decode('utf-8') if isinstance(value, bytes) else value

        count = cls()

        if type(value) == str:
            value = int(value)
        count.count = value

        key_list = ast.literal_eval(key)
        sensor_id = key_list[0]
        count.timestamp_after = key_list[1][0]
        count.timestamp_before = key_list[1][1]

        return count, sensor_id

    def asdict(self):
        return asdict(self)


@dataclass
class SensorDataCount:
    sensor_id: Union[int, str, None] = None
    counts: Optional[List[Count]] = None
    # 桶计数
    bucket_count: Optional[int] = None

    @classmethod
    def from_cache(cls, key, value):
        count, sensor_id = Count.from_cache(key, value)

        sensor_data_count = cls()
        sensor_data_count.sensor_id = sensor_id
        sensor_data_count.counts = [count]

        return sensor_data_count

    def asdict(self):
        return asdict(self)

    def as_filter_dict(self):
        return {
            'sensor_id': self.sensor_id,
            'bucket_count': {'$lt': BUCKET_MAX_COUNT},
        }

    def as_update_dict(self):
        count = self.counts[0]
        return {
            '$setOnInsert': {
                'sensor_id': self.sensor_id,
            },
            '$inc': {'bucket_count': 1},
            '$push': {
                'counts': {
                    '$each': [count.asdict()],
                    # '$sort': {'timestamp_after': 1},
                },
            },
        }


if __name__ == '__main__':
    x = SensorDataCount.from_cache(b'["37501207007602", [1652847960.0, 1652848019.9]]', b'123')
    print(x.asdict())
    print(x.as_filter_dict())
    print(x.as_update_dict())
