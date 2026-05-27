FROM python:3.12-slim

WORKDIR /app
COPY . /app/

ENV EPMS_HOST=0.0.0.0
ENV EPMS_PORT=8080
ENV EPMS_DB=/data/extreme-print-management.sqlite3
ENV EPMS_PRODUCTION=1
ENV EPMS_REQUIRE_AUTH=true
ENV EPMS_ANONYMIZE_DOCS=true
ENV EPMS_SEED_DEMO=0

RUN mkdir -p /data
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health')"

CMD ["python3", "app_production.py"]
