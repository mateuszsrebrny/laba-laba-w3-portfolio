# Use an official Python image
FROM python:3.11

WORKDIR /src/

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

COPY requirements.txt /src/
RUN /root/.local/bin/uv pip install --system -r requirements.txt

COPY alembic.ini /src/alembic.ini
COPY scripts /src/scripts

# will be overlaid for dev
COPY alembic /src/alembic/
COPY app /src/app

# Expose the port for Uvicorn
EXPOSE 10000

# Run FastAPI with Uvicorn
CMD ["bash", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 10000"]

