# Use an official Python image
FROM python:3.11

# Set working directory inside the container
WORKDIR /src/

COPY requirements.txt /src/
RUN pip install -r requirements.txt

COPY alembic.ini /src/alembic.ini
COPY scripts /src/scripts

COPY alembic /src/alembic/
COPY app /src/app

# Expose the port for Uvicorn
EXPOSE 10000

# Run FastAPI with Uvicorn
CMD ["bash", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 10000"]

