Here is a clean, comprehensive **`README.md`** tailored to your project architecture, Docker setup, and local LLM workflow. You can drop this directly into your repository root.

---

```markdown
# 🌍 Proactive AQI Insight Agent

An intelligent, real-time Air Quality Index (AQI) monitoring and anomaly detection agent powered by **FastAPI** and local LLM notifications via **Ollama**.

The system tracks rolling baseline trends, detects critical environmental events (sudden spikes, drops, and sustained shifts), enforces rate-limiting/cooldown logic, and generates natural-language health notifications.

---

## 🚀 Key Features

* **Real-time Anomaly Detection**: Detects `SUDDEN_SPIKE`, `SUDDEN_DROP`, and `SUSTAINED_INCREASE` shifts against dynamic rolling baselines.
* **Local LLM Integration**: Uses Ollama running locally (`mistral` or configurable models) to construct context-aware health alerts.
* **Self-Healing Docker Architecture**: Containerized multi-service setup featuring automated model pulling on startup.
* **Observability Dashboard**: Single-page live audit log interface for monitoring readings, detection triggers, and AI message outputs.
* **Interactive Testing**: Manual AQI injection and hourly trigger simulation endpoints for rapid demo testing.

---

## 🛠️ Tech Stack

* **Backend Framework**: Python 3.11, FastAPI, Uvicorn, HTTPX
* **LLM Engine**: Ollama (Local container execution)
* **Frontend**: HTML5, Tailwind CSS, JavaScript (SSE / REST API consumption)
* **Containerization**: Docker, Docker Compose

---

## 📦 System Architecture & Directory Layout

```text
.
├── app/
│   ├── main.py                   # FastAPI entrypoint & API routes
│   ├── services/
│   │   ├── detection_service.py  # Anomaly detection state logic & rules
│   │   ├── ollama_service.py     # Local LLM client connection
│   │   └── state_service.py      # User history & cooldown state tracking
│   └── templates/
│       └── index.html            # Real-Time Audit Dashboard UI
├── Dockerfile                    # FastAPI web service container setup
├── docker-compose.yml            # Multi-container orchestration
├── entrypoint.sh                 # Ollama automatic boot & model pull script
└── requirements.txt              # Python dependencies

```

---

## ⚡ Quick Start (Docker Setup)

The easiest way to run the application is via Docker Compose. The setup automatically configures the network and pulls the required Ollama model on boot.

### 1. Clone the Repository

```bash
git clone [https://github.com/your-username/aqi-notifier.git](https://github.com/your-username/aqi-notifier.git)
cd aqi-notifier

```

### 2. Make `entrypoint.sh` Executable

```bash
chmod +x entrypoint.sh

```

### 3. Build and Run Container Stack

```bash
docker compose up -d --build

```

> **Note:** On first startup, the `ollama` container will automatically pull the `mistral` model (~4.1 GB). You can view the download progress live:
> ```bash
> docker logs -f aqi_agent_ollama
> 
> ```
> 
> 

### 4. Access the Dashboard

Once the container startup completes, open your browser and navigate to:
**`http://localhost:8000`**

---

## 🛠️ Local Development (Without Docker)

If you prefer to run the FastAPI server directly on your host machine:

### Prerequisites

1. **Python 3.11+** installed.
2. **Ollama** installed locally and running (`ollama serve`).

### Steps

1. **Pull the Ollama model:**
```bash
ollama pull mistral

```


2. **Set up virtual environment & dependencies:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

```


3. **Run FastAPI Application:**
```bash
uvicorn app.main:app --reload --port 8000

```



---

## 🔌 API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | Renders the Observability Audit Dashboard |
| `GET` | `/api/logs` | Fetches historical log events & detection states |
| `POST` | `/api/trigger-cycle` | Runs an automated polling cycle across all monitored cities |
| `POST` | `/api/mock-reading` | Injects a custom AQI value for real-time testing |

### **Example: Injecting a Mock AQI Spike**

```bash
curl -X POST http://localhost:8000/api/mock-reading \
  -H "Content-Type: application/json" \
  -d '{"location_id": 2178, "value": 350.0}'

```

---

## ⚙️ Configuration & Environment Variables

Key parameters can be configured via environment variables in `docker-compose.yml`:

| Variable | Default Value | Description |
| --- | --- | --- |
| `OLLAMA_HOST` | `http://ollama:11434` | Base URL for the Ollama container endpoint |
| `OLLAMA_MODEL` | `mistral` | Target model name executed by Ollama |

```

```