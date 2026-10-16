FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Install dependencies
RUN uv pip install --system -e "."

# Default command (overridden in docker-compose)
CMD ["uvicorn", "hivecode.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
