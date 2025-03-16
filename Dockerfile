# Use an official Python image
FROM python:3.11

# Set working directory inside the container
WORKDIR /

# Copy dependencies
COPY requirements.txt /app/ 

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the FastAPI app
COPY app /app 

# Expose the port for Uvicorn
EXPOSE 8000

# Run FastAPI with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
