FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src/ai_news_tracker ./src/ai_news_tracker
COPY scripts ./scripts

# Set the command to run the application
CMD ["python", "src/ai_news_tracker/main.py"]