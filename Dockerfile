# Use an official Python image
FROM python:3.11

# Set working directory inside the container
WORKDIR /src/

# Copy dependencies
COPY requirements.txt /src/

# Install dependencies
RUN pip install -r requirements.txt

COPY scripts /src/scripts

# Copy the FastAPI app
COPY app /src/app 

# Expose the port for Uvicorn
EXPOSE 10000

# Copy the alembic stuff
COPY alembic.ini /src/alembic.ini
COPY alembic /src/alembic/

# Run FastAPI with Uvicorn
CMD ["bash", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 10000"]

