FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY execution_agent.py .

CMD ["python", "execution_agent.py"]
