# 目录结构

```
water_stream/
|-- flush                              # 消费 changelog ，设置 Redis 缓存，并定时写入 MongoDB
|   |-- Dockerfile
|   |-- models.py                      # MongoDB 模型
|   |-- requirements.txt
|   `-- water_stream_flush.py          # 启动脚本
|-- water_stream_platform              # Docker Compose 部署文件及测试脚本
|   |-- docker-compose.yml
|   |-- publisher                      # 测试脚本，模拟消息生产者
|   |   |-- Dockerfile
|   |   |-- requirements.txt
|   |   `-- test_pub_msg.py            # 启动脚本
|   `-- wait-for-it.sh                 # wait-for-it 脚本，用在 command 中
`-- window                             # kafka-stream 时间窗口
    |-- Dockerfile
    |-- requirements.txt
    `-- water_stream_window.py         # 启动脚本
```

# 部署

```
$ cd water_stream_platform
$ docker-compose build
...
$ docker images | grep water_stream_platform
water_stream_platform_flush           latest              7d209a33124e        45 hours ago        153MB
water_stream_platform_publisher       latest              aa5bf164d696        47 hours ago        148MB
water_stream_platform_window          latest              bc7d17ace01f        2 days ago          148MB
$ docker-compose up -d
Creating network "water_stream_platform_default" with the default driver
Creating water_stream_platform_mongo_1           ... done  # mongo 实例
Creating water_stream_platform_redis_1           ... done  # redis 实例
Creating water_stream_platform_zookeeper_1       ... done  # zookeeper 实例
Creating water_stream_platform_redis-commander_1 ... done  # redis 调试 Web UI
Creating water_stream_platform_mongo-express_1   ... done  # mongo 调试 Web UI
Creating water_stream_platform_kafka_1           ... done  # kafka 实例
Creating water_stream_platform_kafka-ui_1        ... done  # kafka 调试 Web UI
Creating water_stream_platform_window_1          ... done  # kafka-stream 时间窗口
Creating water_stream_platform_flush_1           ... done  # 设置 Redis 缓存，并且定时写入到 MongoDB 中
Creating water_stream_platform_publisher_1       ... done  # 生产者脚本
```

# Reference

[Kafka应用](../../05%20-%20%E4%B8%AD%E9%97%B4%E4%BB%B6/README.md#kafka-应用)