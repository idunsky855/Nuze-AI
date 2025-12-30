#!/bin/sh
set -e # Exit immediately if a command exits with a non-zero status.


# MODEL_TO_PULL="llama3.2"                # 3 Seconds
# MODEL_TO_PULL="llama3.1:8b"             # 17 Seconds
# MODEL_TO_PULL="gpt-oss:latest"
# MODEL_TO_PULL="deepseek-r1:latest"      # 142 seconds - Didn't work properly
MODEL_TO_PULL="phi4:latest"               # 10 seconds
# MODEL_TO_PULL="qwen3:32b"

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

  # Optional: if a Modfile is mounted at /Modfile, attempt to build or extract its SYSTEM prompt
  if [ -f /news-cls-modfile ]; then
    echo "Found /news-cls-modfile in container. Attempting to build model from news-cls-modfile (if supported)..."
    # Do not fail the whole init if build is not supported or fails
    set +e
    if "$OLLAMA_BIN" help | grep -q "build"; then
      echo "ollama supports 'build' — running build against /news-cls-modfile"
      "$OLLAMA_BIN" build -f /news-cls-modfile || {
        echo "ollama build failed; continuing and attempting to extract SYSTEM prompt instead."
      }
    else
      echo "ollama 'build' subcommand not available; skipping build step."
    fi

    # Best-effort: create a named model 'news-classifier' from Modfile if it doesn't already exist
    if ! "$OLLAMA_BIN" list 2>/dev/null | grep -q "^news-classifier"; then
      echo "Creating Ollama model 'news-classifier' from /news-cls-modfile (best-effort)"
      "$OLLAMA_BIN" create news-classifier -f /news-cls-modfile 2>/dev/null || {
        echo "ollama create failed or not supported; continuing startup."
      }
    else
      echo "Model 'news-classifier' already exists."
    fi

    # Attempt to extract the SYSTEM block from Modfile to a persistent location for later use
    # Extract lines between a line starting with 'SYSTEM' and the closing triple quotes
    awk 'BEGIN{in=0} /^SYSTEM[[:space:]]*"""/ {in=1; next} /^"""[[:space:]]*$/ {in=0; exit} in{print}' /news-cls-modfile > /root/.ollama/modfile_system_prompt.txt 2>/dev/null || true
    if [ -s /root/.ollama/modfile_system_prompt.txt ]; then
      echo "Extracted SYSTEM prompt to /root/.ollama/modfile_system_prompt.txt"
      # If the ollama CLI exposes a 'system' or 'config' command to set a system prompt, try to use it (best-effort)
      if "$OLLAMA_BIN" --help 2>&1 | grep -q "system"; then
        echo "Attempting to apply SYSTEM prompt via 'ollama system' (best-effort)"
        # Try possible 'system' subcommands (best-effort; do not abort on failure)
        "$OLLAMA_BIN" system set "$(cat /root/.ollama/modfile_system_prompt.txt)" 2>/dev/null || true
        "$OLLAMA_BIN" system --set "$(cat /root/.ollama/modfile_system_prompt.txt)" 2>/dev/null || true
      else
        echo "No 'system' subcommand found in ollama CLI; SYSTEM prompt persisted to /root/.ollama/modfile_system_prompt.txt"
      fi
    else
      echo "No SYSTEM block found in /news-cls-modfile or extraction failed."
    fi
    set -e
  fi

  # Check for news-combiner-modfile and create model if it exists
  if [ -f /news-combiner-modfile ]; then
    echo "Found /news-combiner-modfile in container."

    # Best-effort: create a named model 'news-combiner' from Modfile if it doesn't already exist
    if ! "$OLLAMA_BIN" list 2>/dev/null | grep -q "^news-combiner"; then
      echo "Creating Ollama model 'news-combiner' from /news-combiner-modfile"
      "$OLLAMA_BIN" create news-combiner -f /news-combiner-modfile || {
        echo "ollama create failed for news-combiner; continuing startup."
      }
    else
      echo "Model 'news-combiner' already exists."
    fi
  fi

  # Check for news-summarizer-modfile and create model if it exists
  if [ -f /news-summarizer-modfile ]; then
    echo "Found /news-summarizer-modfile in container."

    # Best-effort: create a named model 'news-summarizer' from Modfile if it doesn't already exist
    if ! "$OLLAMA_BIN" list 2>/dev/null | grep -q "^news-summarizer"; then
      echo "Creating Ollama model 'news-summarizer' from /news-summarizer-modfile"
      "$OLLAMA_BIN" create news-summarizer -f /news-summarizer-modfile || {
        echo "ollama create failed for news-summarizer; continuing startup."
      }
    else
      echo "Model 'news-summarizer' already exists."
    fi
  fi

echo "Initialization complete. Ollama server process (PID: $pid) is running."
# Wait for the background Ollama server process to terminate
# This keeps the script running and the container alive
wait $pid