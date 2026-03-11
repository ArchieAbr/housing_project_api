# Use an official lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /code

# Copy the requirements file and install dependencies
COPY ./app/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the rest of the application code
COPY ./app /code/app

# Copy data file for seeding
COPY ./leeds_housing_data.csv /code/leeds_housing_data.csv

# Command to run the application using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]