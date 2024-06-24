FROM python:3.12-alpine

# Install Poetry
RUN pip install poetry

# Copy and install dependencies using Poetry
WORKDIR /bot
COPY pyproject.toml poetry.lock /bot/
RUN poetry install --no-root --no-interaction --no-ansi

# Copy the rest of your application code
COPY . /bot

# Set environment variables
ENV ENV_VARIABLE_NAME=value

# Run the bot main file
CMD ["python", "bot.py"]

# Clean up
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*