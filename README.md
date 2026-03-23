# vLLM SLM Server

A lightweight inference server for **Small Language Models (SLMs)** powered by [vLLM](https://github.com/vllm-project/vllm), featuring an API gateway with streaming support and a Streamlit chat UI.

## Architecture

```
┌────────────────┐     ┌──────────────────┐     ┌────────────────┐
│  Streamlit UI  │────▶│   API Gateway    │────▶│   LLM Engine   │
│   (Port 8501)  │     │   (Port 8080)    │     │   (Port 8081)  │
└────────────────┘     └──────────────────┘     └────────────────┘
                        FastAPI + Streaming      vLLM AsyncEngine
```

## Features

- **vLLM-powered inference** — High-throughput serving with GPU memory optimization
- **Streaming responses** — Real-time token-by-token text generation
- **API Gateway** — FastAPI proxy that streams and logs all responses
- **Chat UI** — Interactive Streamlit interface for testing prompts
- **Configurable** — Environment variables for model, GPU memory, sequence limits, etc.

## Supported Models

| Model | Size | Default |
|-------|------|---------|
| `HuggingFaceTB/SmolLM2-1.7B-Instruct` | 1.7B | ✅ |
| `Qwen/Qwen2.5-3B-Instruct` | 3B | ✅ |

## Quick Start

### Prerequisites

- Python 3.10+
- NVIDIA GPU with CUDA support
- ~4 GB VRAM (for default 1.7B model)

### Setup

```bash
# Clone the repo
git clone https://github.com/AyushRaj009/vllm-slm-server.git
cd vllm-slm-server

# Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run

```bash
bash run_services.sh
```

This starts all 3 services:

| Service | URL |
|---------|-----|
| LLM Engine | `http://localhost:8081` |
| API Gateway | `http://localhost:8080` |
| Streamlit UI | `http://localhost:8501` |

Press `Ctrl+C` to stop all services.

### API Usage

```bash
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain quantum computing in simple terms"}'
```

## Configuration

All settings can be overridden via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_NAME` | `HuggingFaceTB/SmolLM2-1.7B-Instruct` | HuggingFace model ID |
| `GPU_MEMORY_UTILIZATION` | `0.92` | Fraction of GPU memory to use |
| `MAX_MODEL_LEN` | `1024` | Maximum sequence length |
| `MAX_NUM_SEQS` | `24` | Max concurrent sequences |
| `DTYPE` | `float16` | Model precision |
| `API_PORT` | `8080` | API Gateway port |

## Project Structure

```
├── app/
│   ├── core/
│   │   └── config.py          # Environment-based settings
│   ├── services/
│   │   ├── llm_engine.py      # vLLM AsyncEngine service
│   │   ├── api_gateway.py     # FastAPI streaming proxy
│   │   └── load_tester.py     # Concurrency load testing
│   └── ui/
│       └── streamlit_app.py   # Chat interface
├── run_services.sh            # Start all services
├── requirements.txt
└── README.md
```

## Tech Stack

- **[vLLM](https://github.com/vllm-project/vllm)** — High-throughput LLM serving engine
- **[FastAPI](https://fastapi.tiangolo.com/)** — Async API framework
- **[Streamlit](https://streamlit.io/)** — Rapid UI prototyping
- **[HTTPX](https://www.python-httpx.org/)** — Async HTTP client

## License

This project is open source. Feel free to use and modify.
