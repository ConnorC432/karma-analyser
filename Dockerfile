FROM python:3.12-slim
LABEL authors="connor"

ENV DEBIAN_FRONTEND=noninteractive

# Use images for development only rn, it will contain secrets from settings.json
WORKDIR /app
COPY . /app

RUN apt update && \
    apt install -y \
    	libffi-dev \
    	libnacl-dev \
    	python3-dev \
    	build-essential \
    	deno

RUN pip install --no-cache-dir -r requirements.txt || true

CMD ["python", "bot.py"]