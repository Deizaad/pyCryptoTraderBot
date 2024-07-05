FROM python:3.12-slim

# Install Poetry
RUN pip install poetry

# Copy and install dependencies using Poetry
WORKDIR /app
COPY pyproject.toml poetry.lock /app/
RUN poetry install --no-root --no-interaction --no-ansi

# Copy the rest of your application code
COPY . /app

# Clean up
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Run the bot main file
CMD ["python", "Application/test.py"]