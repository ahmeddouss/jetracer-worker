FROM arm64v8/python:3.8-slim

RUN apt-get update && apt-get install -y \
    libzbar0 \
    libzbar-dev \ 
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    ffmpeg \
    network-manager \
    alsa-utils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "camera.py"]
