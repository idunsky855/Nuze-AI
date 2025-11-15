#!/bin/sh
set -e # Exit immediately if a command exits with a non-zero status.


MODEL_TO_PULL="llama3.2"


echo "Starting Ollama server in background..."
# Try to locate the ollama binary in PATH, fallback to common locations
OLLAMA_BIN="$(command -v ollama 2>/dev/null || true)"
if [ -z "$OLLAMA_BIN" ]; then
  if [ -x /bin/ollama ]; then
    OLLAMA_BIN=/bin/ollama
  elif [ -x /usr/bin/ollama ]; then
    OLLAMA_BIN=/usr/bin/ollama
  fi
fi

if [ -z "$OLLAMA_BIN" ]; then
  echo "ERROR: 'ollama' binary not found in PATH or /bin/ollama or /usr/bin/ollama."
  echo "PATH=$PATH"
  echo "ls /bin:" && ls -la /bin || true
  echo "ls /usr/bin:" && ls -la /usr/bin || true
  exit 127
fi

echo "Using ollama binary: $OLLAMA_BIN"
$OLLAMA_BIN serve &
# Store the server process ID
pid=$!

echo "Ollama server started (PID: $pid). Waiting for it to become available..."

# Wait loop for the server to be ready
attempts=0
max_attempts=12 # Wait up to 60 seconds (12 * 5s)
while ! "$OLLAMA_BIN" list > /dev/null 2>&1; do
  attempts=$((attempts+1))
  if [ $attempts -ge $max_attempts ]; then
    echo "Ollama server failed to start after ${max_attempts} attempts."
    exit 1
  fi
  echo "Waiting for Ollama server... (Attempt $attempts/$max_attempts)"
  sleep 5
done

echo "Ollama server is ready."

# Check if the model exists, pull if not
echo "Checking for model: $MODEL_TO_PULL"
# Use grep -q for quiet check, exit code 0 if found, 1 if not
if ! "$OLLAMA_BIN" list | grep -q "^${MODEL_TO_PULL}"; then
  echo "Model not found. Pulling $MODEL_TO_PULL..."
  "$OLLAMA_BIN" pull "$MODEL_TO_PULL"
  echo "Model pull finished."
else
  echo "Model $MODEL_TO_PULL already exists."
fi

echo "Initialization complete. Ollama server process (PID: $pid) is running."
# Wait for the background Ollama server process to terminate
# This keeps the script running and the container alive
wait $pid