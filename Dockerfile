# Multi-stage build for optimized Docker image
# Stage 1: Build dependencies
FROM python:3.10-slim as builder

# Install UV for package management
RUN pip install --no-cache-dir uv

# Set work directory
WORKDIR /app

# Copy pyproject.toml for dependency installation
COPY pyproject.toml .

# Install dependencies into a virtual environment using UV
RUN uv venv /app/.venv
RUN /app/.venv/bin/uv pip install --no-cache-dir -e .

# Stage 2: Runtime image
FROM python:3.10-slim as runtime

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . .

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH="/app:$PYTHONPATH"

# Create non-root user for security
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

# Create directories for data persistence
RUN mkdir -p /app/data/conversations

# Expose the port
EXPOSE 8000

# Set the entrypoint
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
