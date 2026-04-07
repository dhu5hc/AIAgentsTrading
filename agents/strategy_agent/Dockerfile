FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY strategy_agent.py .

CMD ["python", "strategy_agent.py"]
