# Use an official Python runtime as the base image
FROM python:3

# Set the working directory inside the container
WORKDIR /app

# Copy the server.py file to the working directory
COPY server.py .

# Copy the requirements.txt file to the working directory
COPY requirements.txt .

# Create a Python virtual environment
RUN python3 -m venv myenv

# Activate the virtual environment
SHELL ["/bin/bash", "-c", "source myenv/bin/activate"]

# Upgrade pip
RUN pip install --upgrade pip

# Install the dependencies from requirements.txt
RUN pip install -r requirements.txt

# Expose port 8080
EXPOSE 8080

# Set the command to run the server.py file
CMD [ "python3", "server.py" ]
