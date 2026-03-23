import logging
import uuid
import os
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.sampling_params import SamplingParams

from app.core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm-engine")

app = FastAPI()

# Global engine variable
engine: AsyncLLMEngine = None

def get_engine() -> AsyncLLMEngine:
    global engine
    if engine is None:
        logger.info(f"Initializing AsyncLLMEngine with model: {settings.MODEL_NAME}")
        engine_args = AsyncEngineArgs(
            model=settings.MODEL_NAME,
            dtype=settings.DTYPE,
            gpu_memory_utilization=settings.GPU_MEMORY_UTILIZATION,
            max_model_len=settings.MAX_MODEL_LEN,
            max_num_seqs=settings.MAX_NUM_SEQS,
            enforce_eager=settings.ENFORCE_EAGER,
            disable_log_stats=True,
        )
        engine = AsyncLLMEngine.from_engine_args(engine_args)
        logger.info("AsyncLLMEngine initialized.")
    return engine

class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.9

@app.on_event("startup")
async def startup_event():
    # Initialize engine on startup
    get_engine()

@app.post("/generate")
async def generate(request: GenerateRequest):
    """
    Generate text using vLLM AsyncEngine. 
    Streams the output as raw text chunks (or could use JSON/SSE).
    Here we stream raw tokens to match the simplified flow.
    """
    engine_instance = get_engine()
    
    sampling_params = SamplingParams(
        temperature=request.temperature,
        top_p=request.top_p,
        max_tokens=request.max_tokens,
    )
    
    request_id = f"req_{uuid.uuid4().hex}"
    
    # Define generator
    async def stream_results() -> AsyncGenerator[str, None]:
        async for request_output in engine_instance.generate(
            request.prompt, sampling_params, request_id
        ):
            # vLLM returns the full generated text in the last output, 
            # but usually we want deltas.
            # RequestOutput.outputs[0].text is the cumulative text.
            # We need to track what we sent.
            pass  
            # Actually, let's use a simpler logic for deltas if needed.
            # But vLLM `outputs[0].text` is "The whole text so far".
            
        # Refetching logic:
        previous_text = ""
        async for request_output in engine_instance.generate(
            request.prompt, sampling_params, request_id
        ):
            current_text = request_output.outputs[0].text
            # Calculate delta
            delta = current_text[len(previous_text):]
            if delta:
                yield delta
            previous_text = current_text

    return StreamingResponse(stream_results(), media_type="text/plain")
