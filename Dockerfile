# Use the official Python 3.9 image from the Docker Hub
FROM python:3.9-slim-buster

# Install Poetry
RUN pip install --no-cache-dir poetry

# Set the working directory inside the container
WORKDIR /app

# Copy only the files needed for installing dependencies to the Docker image
COPY pyproject.toml poetry.lock ./

# Install the project dependencies
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi --no-dev

# Copy the rest of your project files into the Docker image
COPY . .

EXPOSE 8888

# Set the command to run your application
ENTRYPOINT ["poetry", "run"]
CMD ["python", "server.py"]
