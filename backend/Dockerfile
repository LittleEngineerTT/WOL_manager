FROM python:3.13-slim

WORKDIR /app

RUN apt update && apt install -y \
    net-tools \
    iputils-ping \
    iproute2 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]