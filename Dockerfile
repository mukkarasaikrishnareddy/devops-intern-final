FROM python:3.12-slim

WORKDIR /app

COPY hello.py .

EXPOSE 8080

CMD ["python", "hello.py"]
