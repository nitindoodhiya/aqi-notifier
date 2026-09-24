#!/bin/bash

# Start Ollama server in the background
ollama serve &
OLLAMA_PID=$!

echo "[Ollama Setup] Waiting for Ollama server to initialize..."
until python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:11434/api/tags')" 2>/dev/null; do
    sleep 2
done

MODEL_NAME=${OLLAMA_MODEL:-mistral}
echo "[Ollama Setup] Checking model status for '$MODEL_NAME'..."

# Check if model is already pulled
if python3 -c "import urllib.request, json; data=json.loads(urllib.request.urlopen('http://localhost:11434/api/tags').read()); exit(0 if any(m['name'].startswith('$MODEL_NAME') for m in data.get('models', [])) else 1)" 2>/dev/null; then
    echo "[Ollama Setup] Model '$MODEL_NAME' is already installed."
else
    echo "[Ollama Setup] Pulling '$MODEL_NAME'... (Streaming progress below)"
    # Stream pull status log lines
    python3 -c "
import urllib.request, json
req = urllib.request.Request('http://localhost:11434/api/pull', data=json.dumps({'name': '$MODEL_NAME'}).encode('utf-8'), headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as response:
    last_status = ''
    for line in response:
        if line:
            msg = json.loads(line.decode('utf-8'))
            status = msg.get('status', '')
            completed = msg.get('completed', 0)
            total = msg.get('total', 0)
            if total > 0:
                pct = round((completed / total) * 100, 1)
                log_line = f'{status}: {pct}% ({completed}/{total} bytes)'
            else:
                log_line = status
            if log_line != last_status:
                print(f'[Ollama Pull] {log_line}', flush=True)
                last_status = log_line
"
    echo "[Ollama Setup] Model '$MODEL_NAME' successfully downloaded!"
fi

# Keep server running
wait $OLLAMA_PID