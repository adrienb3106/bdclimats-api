FROM python:3.12-slim
WORKDIR /app

# Install the application dependencies
COPY requirements.txt ./
RUN python -m pip install --upgrade pip && python -m pip install --no-cache-dir -r requirements.txt
