FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/ ./scripts/

CMD ["python", "./scripts/fetch_and_analyze.py"]
