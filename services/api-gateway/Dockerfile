FROM python:3.11-slim
LABEL service="api-gateway"
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser
ENV SERVICE_VERSION="1.0.0" PYTHONUNBUFFERED=1
EXPOSE 5000
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import requests; r = requests.get('http://localhost:5000/health/live', timeout=4); exit(0 if r.status_code == 200 else 1)"
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "30", "--access-logfile", "-", "app:app"]
