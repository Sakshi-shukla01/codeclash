# Sandbox image: isi image mein users ka code chalta hai.
# Supported languages: Python, C++ (g++), C (gcc), Java (JDK), JavaScript (Node.js)
# (Folder ka naam "python" purana hai, image ab saari languages ke liye hai.)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends g++ gcc libc6-dev default-jdk-headless nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY runner.py /runner.py

# 65534 = "nobody" user -> root powers nahi
USER 65534:65534
WORKDIR /tmp

CMD ["python", "/runner.py"]
