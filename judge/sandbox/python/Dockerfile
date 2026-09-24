# Sandbox image: isi image mein users ka code chalta hai.
# Chhoti image rakhi hai, koi extra tool nahi, taaki attack surface kam ho.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY runner.py /runner.py

# 65534 = "nobody" user -> root powers nahi
USER 65534:65534
WORKDIR /tmp

CMD ["python", "/runner.py"]
