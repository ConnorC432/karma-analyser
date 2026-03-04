## TODO better dockerfile
FROM python:3.12-slim
LABEL authors="connor"

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app
COPY . /app

RUN apt update && \
    apt install -y \
    	libffi-dev \
    	libnacl-dev \
    	python3-dev \
    	build-essential

RUN pip install --no-cache-dir -r requirements.txt || true

CMD ["python", "bot.py"]