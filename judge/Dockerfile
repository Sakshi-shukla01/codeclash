# Judge worker image.
# Isme docker CLI chahiye, kyunki worker har submission ke liye naya sandbox container banata hai
# (host ke Docker se baat karke, /var/run/docker.sock ke through).
FROM docker:28-cli AS dockercli

FROM python:3.12-slim
COPY --from=dockercli /usr/local/bin/docker /usr/local/bin/docker

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV PYTHONUNBUFFERED=1
CMD ["python", "worker.py"]
