import logging
import os
import time
import uuid
import httpx

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("api-gateway")

app = FastAPI()

# Output directory for logs
OUTPUT_DIR = "responses"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class Query(BaseModel):
    prompt: str

@app.post("/generate")
async def generate(query: Query):
    """
    Proxies the generation request to the LLM Engine.
    Streams the response back to the client while saving it to a file.
    """
    # Unique ID for this request
    request_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
    output_path = os.path.join(OUTPUT_DIR, f"{request_id}.txt")
    
    # URL of the internal LLM Engine
    # Note: We assume the engine is running on port 8081 by default or configured env.
    # The config.py defines API_PORT which is for THIS gateway (8080).
    # We need the ENGINE URL.
    # Let's assume the engine runs on localhost:8081 for now, or use an env var.
    # We will need to run the engine on a different port than this gateway.
    # Let's hardcode 8081 for the engine or add it to config.
    engine_url = os.getenv("LLM_ENGINE_URL", "http://localhost:8081/generate")

    payload = {
        "prompt": query.prompt,
        "max_tokens": 256,
        "temperature": 0.7
    }

    async def stream_and_save():
        buffer = []
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", engine_url, json=payload) as resp:
                    if resp.status_code != 200:
                        error_msg = f"Engine returned status {resp.status_code}"
                        logger.error(error_msg)
                        yield error_msg
                        return

                    async for chunk in resp.aiter_text():
                        if chunk:
                            buffer.append(chunk)
                            yield chunk
        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            yield f"\n[Error: {str(e)}]"
        finally:
            # Save the complete response
            if buffer:
                final_text = "".join(buffer)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(final_text)
                logger.info(f"Saved response to {output_path}")

    return StreamingResponse(
        stream_and_save(),
        media_type="text/plain"
    )
