# 단일 venv 기본 이미지. 여러 stack(예: jax + torch)이 필요하면 venv를 추가하고
# requirements 파일을 나눠서 COPY+RUN 레이어를 늘리세요.
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv python3-dev \
        git build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY requirements.txt ./requirements.txt
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

ENV PATH=/opt/venv/bin:$PATH

# 소스는 이미지에 굽지 않음 — 런타임에 bind-mount로 들어옴 (docker-compose.yml).

COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["bash"]
