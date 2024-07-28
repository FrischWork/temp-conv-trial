FROM python:3.9-slim

COPY init_kafka.py /app/init_kafka.py
RUN pip install confluent_kafka

CMD ["python", "/app/init_kafka.py"]
