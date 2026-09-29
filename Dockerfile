FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/* && \
    useradd --system --uid 10001 --user-group --create-home app && \
    chown app:app /app

COPY requirements.txt .
RUN python3 -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app . .

# Run unprivileged: code execution in the app no longer means root in the container.
USER app

EXPOSE 8000

CMD ["python3", "app.py"]
