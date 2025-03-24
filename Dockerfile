# Use an official Python image
FROM python:3.11

ENV DOCKER_BUILDKIT=0

ARG GIT_COMMIT=unknown-docker
ENV GIT_COMMIT=$GIT_COMMIT
ARG RENDER_GIT_COMMIT
ENV RENDER_GIT_COMMIT=$RENDER_GIT_COMMIT

RUN echo "--->$RENDER_GIT_COMMIT<--"
RUN echo "--->$GIT_COMMIT<--"
RUN env

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

# Run FastAPI with Uvicorn
CMD ["bash", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 10000"]

