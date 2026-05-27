FROM python:3.12-slim
WORKDIR /opt/mersal-guard
COPY app.py agent.py xig/ web/ config/ ./
RUN useradd --system --create-home mersal && mkdir -p /var/lib/mersal-guard && chown mersal:mersal /var/lib/mersal-guard
ENV MERSAL_HOST=0.0.0.0 MERSAL_PORT=8090 MERSAL_DB=/var/lib/mersal-guard/mersal-guard.sqlite3
EXPOSE 8090
USER mersal
CMD ["python3", "app.py"]
