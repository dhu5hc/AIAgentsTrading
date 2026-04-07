FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY risk_agent.py .

CMD ["python", "risk_agent.py"]
