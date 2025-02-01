# Use official Python image
FROM python:3.8

# Set the working directory inside the container
WORKDIR /app

# Copy project files into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for Django
EXPOSE 8000

# Run migrations and start Django server
CMD ["bash", "-c", "python3 manage.py migrate && python3 manage.py runserver 0.0.0.0:8000"]
