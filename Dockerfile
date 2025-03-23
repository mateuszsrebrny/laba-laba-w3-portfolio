# Use an official Python image
FROM python:3.11

# Set working directory inside the container
WORKDIR /

# Copy dependencies
COPY requirements.txt /

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the FastAPI app
COPY app /app 

# Expose the port for Uvicorn
EXPOSE 10000

# Run FastAPI with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
