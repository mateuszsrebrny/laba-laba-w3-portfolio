# Use an official Python image
FROM python:3.11

# Set working directory inside the container
WORKDIR /src/

# Copy dependencies
COPY requirements.txt /src/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts /src/scripts

# Copy the FastAPI app
COPY app /src/app 

# Expose the port for Uvicorn
EXPOSE 10000

# Copy the alembic.ini
COPY alembic.ini /src/alembic.ini

ARG GIT_COMMIT=unknown-docker
ENV GIT_COMMIT=$GIT_COMMIT

# Run FastAPI with Uvicorn
CMD ["bash", "-c", "ls -l && uvicorn app.main:app --host 0.0.0.0 --port 10000"]
#CMD ["bash", "-c", "alembic stamp head && sleep 20"]


