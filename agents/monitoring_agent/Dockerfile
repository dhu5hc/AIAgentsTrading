FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY monitoring_agent.py .

CMD ["python", "monitoring_agent.py"]
