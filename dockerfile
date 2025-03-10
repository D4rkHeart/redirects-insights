FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/ ./scripts/
RUN chmod +x /app/scripts/init_ssh.sh

CMD ["/bin/bash", "-c", "/app/scripts/init_ssh.sh && python /app/scripts/analyze_redirects.py"]
