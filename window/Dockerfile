### 安装 python 包
FROM python:3.8 as builder

WORKDIR /app

COPY requirements.txt ./requirements.txt

RUN set -eux; \
    # 切换到国内源
    python -m pip install -i https://mirrors.aliyun.com/pypi/simple/ --upgrade pip; \
    pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/; \
    # 安装包
    pip install -r requirements.txt;

# 最终镜像
FROM python:3.8-slim-buster

WORKDIR /app

COPY . .

# 复制包
COPY --from=builder /usr/local/lib/python3.8/site-packages/ /usr/local/lib/python3.8/site-packages/

# 启动服务
CMD [ "python", "water_stream_window.py", "worker", "-l", "info"]