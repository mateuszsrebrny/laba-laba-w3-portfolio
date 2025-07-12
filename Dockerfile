# Base stage with common dependencies
FROM python:3.11-slim AS base

WORKDIR /src/

# Install uv
#ADD https://astral.sh/uv/install.sh /uv-installer.sh
#RUN sh /uv-installer.sh && rm /uv-installer.sh

# Copy uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set uv to use copy mode for Docker builds
ENV UV_LINK_MODE=copy

# Install Python dependencies (shared by both prod and test)
COPY requirements.txt /src/
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked,id=uv-cache \
    uv pip install --system -r ./requirements.txt

# Pre-download OCR models with cache mount
ENV EASYOCR_MODULE_PATH=/opt/easyocr
RUN --mount=type=cache,target=/tmp/easyocr-cache \
    mkdir -p /tmp/easyocr-cache && \
    export EASYOCR_MODULE_PATH=/tmp/easyocr-cache && \
    python -c "from easyocr import Reader; reader = Reader(['en'], download_enabled=True);" && \
    cp -r /tmp/easyocr-cache /opt/easyocr && \
    chmod -R 755 /opt/easyocr

# Production stage - clean and minimal
FROM base AS production

COPY alembic.ini /src/alembic.ini
COPY scripts /src/scripts

# will be overlaid for dev
COPY alembic /src/alembic/
COPY app /src/app

# Expose the port for Uvicorn
EXPOSE 10000

# Run FastAPI with Uvicorn
CMD ["bash", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 10000"]

# Test stage - extends base with Playwright (NOT production)
FROM base AS test

# Install ALL Playwright system dependencies in one cached operation
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxcomposite1 \
    libxrandr2 libxdamage1 libxkbcommon0 libgbm1 libasound2 \
    libpangocairo-1.0-0 libpango-1.0-0 libcairo2 fonts-liberation \
    libfontconfig1 fonts-ipafont-gothic fonts-freefont-ttf \
    fonts-noto-color-emoji fonts-tlwg-loma-otf fonts-unifont \
    fonts-wqy-zenhei libdrm-amdgpu1 libdrm-nouveau2 libdrm-radeon1 \
    libfontenc1 libgl1 libgl1-mesa-dri libglapi-mesa libglvnd0 \
    libglx-mesa0 libglx0 libllvm15 libsensors-config libsensors5 \
    libunwind8 libx11-xcb1 libxaw7 libxcb-dri2-0 libxcb-dri3-0 \
    libxcb-glx0 libxcb-present0 libxcb-randr0 libxcb-sync1 \
    libxcb-xfixes0 libxfont2 libxkbfile1 libxmu6 libxpm4 \
    libxshmfence1 libxxf86vm1 libz3-4 x11-xkb-utils \
    xfonts-encodings xfonts-utils xserver-common xvfb \
    -o APT::Keep-Downloaded-Packages=true && \
    rm -rf /var/lib/apt/lists/*

# Install test dependencies
COPY requirements-tests.txt /src/
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked,id=uv-cache \
    uv pip install --system -r ./requirements-tests.txt

# Install Playwright browsers with persistent caching
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

RUN --mount=type=cache,target=/tmp/ms-playwright \
    PLAYWRIGHT_BROWSERS_PATH=/tmp/ms-playwright \
    python -m playwright install --only-shell chromium && \
    cp -r /tmp/ms-playwright /ms-playwright

# Copy application code and config (this layer rebuilds when source changes)
COPY alembic.ini /src/alembic.ini
COPY scripts /src/scripts
COPY alembic /src/alembic/
COPY app /src/app
COPY pytest.ini /src/

CMD ["pytest", "tests/"]

