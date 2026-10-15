FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    RAADIO_CONF=/config/config.env \
    RAADIO_STATE_DIR=/state \
    TZ=Europe/Tallinn

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y ffmpeg tini tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 raadio \
    && mkdir -p /config /recordings /state \
    && chown -R raadio:raadio /config /recordings /state

WORKDIR /app

COPY recorder/requirements.txt recorder/requirements.txt
RUN pip install --no-cache-dir -r recorder/requirements.txt

COPY --chown=raadio:raadio . .

USER raadio
EXPOSE 8788

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "docker/healthcheck.py"]

ENTRYPOINT ["/usr/bin/tini", "--", "/app/docker/entrypoint.sh"]
CMD ["python", "-u", "recorder/kuku_recorder.py"]
