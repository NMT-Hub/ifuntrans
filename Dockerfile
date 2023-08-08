# Use the official Python 3.9 image from the Docker Hub
FROM python:3.9-slim-buster

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python -

# Make sure that the PATH includes the Poetry installation so we can run it
ENV PATH="$POETRY_HOME/bin:$PATH"

# Disable the creation of .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Turn off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy only the files needed for installing dependencies to the Docker image
COPY pyproject.toml poetry.lock ./

# Install the project dependencies
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

# Copy the rest of your project files into the Docker image
COPY . .

EXPOSE 8888

# Set the command to run your application
ENTRYPOINT ["poetry", "run"]
CMD ["python", "server.py"]
