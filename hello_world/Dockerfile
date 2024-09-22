FROM python:3.9-slim

WORKDIR /app

RUN pip install neo4j bcrypt

COPY . /app

CMD ["python", "main.py"]
