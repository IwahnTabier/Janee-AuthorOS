FROM python:3.12-slim

WORKDIR /app

COPY . .

# Data directory for the SQLite database
RUN mkdir -p /data

VOLUME ["/data"]

# Override DB path via environment variable for Docker persistence
ENV AUTHOR_OS_DB=/data/author_os.db

CMD ["python", "author_os.py"]
