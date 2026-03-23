import os

class Settings:
    # Service Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8080"))
    
    # Text Generation / LLM Configuration
    # Default to the smaller model for dev/testing, but allow override
    MODEL_NAME: str = os.getenv("MODEL_NAME", "HuggingFaceTB/SmolLM2-1.7B-Instruct")
    # Alternate: "Qwen/Qwen2.5-3B-Instruct"
    
    # vLLM Configuration
    GPU_MEMORY_UTILIZATION: float = float(os.getenv("GPU_MEMORY_UTILIZATION", "0.92"))
    MAX_MODEL_LEN: int = int(os.getenv("MAX_MODEL_LEN", "1024"))
    MAX_NUM_SEQS: int = int(os.getenv("MAX_NUM_SEQS", "24"))
    DTYPE: str = os.getenv("DTYPE", "float16")
    ENFORCE_EAGER: bool = os.getenv("ENFORCE_EAGER", "False").lower() == "true"
    
    # Backend URL for UI/Client
    BACKEND_URL: str = os.getenv("BACKEND_URL", f"http://localhost:{API_PORT}/generate")

settings = Settings()
