# Use an official Python image
FROM python:3.11

# Set working directory inside the container
WORKDIR /

# Copy dependencies
COPY requirements.txt /app/ 

ENV DATABASE_URL=postgresql://ll_dev_user:ll_dev_db_pass@172.17.0.1:5432/laba_laba_dev
# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the FastAPI app
COPY app /app 

# Expose the port for Uvicorn
EXPOSE 8000

# Run FastAPI with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
