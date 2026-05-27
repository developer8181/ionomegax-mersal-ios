FROM python:3.12-slim

WORKDIR /app
COPY . /app/extreme-print-management-system
WORKDIR /app/extreme-print-management-system

ENV EPMS_HOST=0.0.0.0
ENV EPMS_PORT=8080
ENV EPMS_DB=/data/extreme-print-management.sqlite3

RUN mkdir -p /data
EXPOSE 8080
CMD ["python3", "app.py"]
