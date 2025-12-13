FROM python:3.10-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Accept HF token as build arg
ARG HF_TOKEN=""

# 1. Setup the environment
WORKDIR /app
ENV PYTHONPATH="${PYTHONPATH}:/app"
ENV HF_HOME=/app/models

# 2. Install dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# 3. Copy helper scripts
COPY download_model.py verify_model_cache.py ./

# 4. Pre-download SAM3 model with authentication
RUN if [ -n "$HF_TOKEN" ]; then \
        echo "🔐 Logging into HuggingFace..."; \
        python -c "from huggingface_hub import login; login(token='${HF_TOKEN}'); print('✅ Logged in to HuggingFace')"; \
    else \
        echo "⚠️  No HF_TOKEN provided - attempting anonymous download"; \
    fi && \
    echo "📥 Downloading SAM3 model..." && \
    python download_model.py

# 5. Verify the model was cached correctly
RUN echo "🔍 Verifying model cache..." && python verify_model_cache.py

# 6. Set offline mode for runtime (after successful download)
ENV HF_HUB_OFFLINE=1

# 7. Copy application code
COPY . .

# 8. Expose the port
ENV PORT=8080
EXPOSE 8080

# 9. Run the server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]