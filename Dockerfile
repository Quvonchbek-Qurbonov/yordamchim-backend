FROM python:3.11-slim

WORKDIR /app

# Copy requirements first (better layer caching)
COPY app/requirements.txt ./app/

RUN pip install --no-cache-dir -r app/requirements.txt

# Copy the rest
COPY . .

# Run as non-root user
RUN useradd -m appuser
USER appuser

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]