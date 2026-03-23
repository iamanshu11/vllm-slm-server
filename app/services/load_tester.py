import asyncio
import time
import httpx
from app.core.config import settings

URL = settings.BACKEND_URL
CONCURRENT_REQUESTS = 20

PROMPT = "Explain the Transformer neural network architecture (Vaswani et al., 2017) in 3 short sentences."

async def worker(idx: int, start_evt: asyncio.Event):
    """
    Worker task that waits for start event, sends a request, and streams the response.
    """
    await start_evt.wait()
    t0 = time.monotonic()
    
    print(f"User {idx} sending request to {URL}...")
    
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            async with client.stream("POST", URL, json={"prompt": PROMPT}) as resp:
                if resp.status_code != 200:
                    print(f"User {idx} ERROR status {resp.status_code}")
                    return
                
                print(f"User {idx} started receiving at {time.monotonic() - t0:.3f}s")
                
                # Consume stream
                first = False
                async for chunk in resp.aiter_text():
                    if chunk:
                        if not first:
                            print(f"User {idx} first-chunk at {time.monotonic() - t0:.3f}s")
                            first = True
                        # print(f"User {idx} chunk: {chunk[:10]}...") 
                        
                print(f"User {idx} finished at {time.monotonic() - t0:.3f}s")
        except Exception as e:
            print(f"User {idx} request failed: {e}")

async def main():
    start_evt = asyncio.Event()
    tasks = [asyncio.create_task(worker(i, start_evt)) for i in range(CONCURRENT_REQUESTS)]
    
    print(f"Spawning {CONCURRENT_REQUESTS} concurrent requests...")
    await asyncio.sleep(0.5)
    
    t = time.monotonic()
    start_evt.set()
    await asyncio.gather(*tasks)
    
    print(f"All done; elapsed: {time.monotonic()-t:.3f}s")

if __name__ == "__main__":
    asyncio.run(main())
