FROM ubuntu:26.04
ENV DEBIAN_FRONTEND=noninteractive TMPDIR=/var/tmp/telegram-build
RUN mkdir -p "$TMPDIR" && apt-get update && apt-get install -y --no-install-recommends \
 python3 osc ca-certificates util-linux xz-utils && rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["python3", "tools/pipeline.py", "cloud-cycle"]
