from fastapi import FastAPI
from fastapi.responses import FileResponse
import uvicorn
import asyncio

app = FastAPI()

@app.post("/generate-3d")
async def generate_3d():
    print("MOCK WORKER: Generating 3D model...")
    await asyncio.sleep(1)  # Simulate generation time
    return FileResponse("Box.glb", media_type="model/gltf-binary")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
