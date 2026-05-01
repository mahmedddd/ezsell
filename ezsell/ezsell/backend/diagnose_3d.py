import asyncio
import os
import json
import sys
from pathlib import Path

# Add backend to path so we can import modules
sys.path.append(os.getcwd())

from core.config import settings
from services.image_to_3d import (
    start_image_to_3d_task, 
    start_multiview_to_3d_task,
    upload_image_to_tripo
)

async def diagnose_product_10():
    print("--- Diagnostic Start ---")
    print(f"TRIPO_API_KEY: {settings.TRIPO_API_KEY[:5]}...{settings.TRIPO_API_KEY[-5:] if settings.TRIPO_API_KEY else 'NONE'}")
    
    # Same logic as ar_assets.py
    def get_abs_path(rel_p):
        if not rel_p: return None
        if rel_p.startswith("/") and not rel_p.startswith("//"):
            if rel_p.startswith("/uploads/"):
                # Path(rel_p.lstrip("/")) ALREADY contains "uploads"
                return os.path.abspath(rel_p.lstrip("/"))
        return None

    # Mocking product 10 images (from previous sqlite check)
    images = ["/uploads/listings/db5fef4f-a650-4746-9e8e-75c2783b2de3.png"]
    
    print(f"Images: {images}")
    
    try:
        if len(images) > 1:
            print("Trying Multiview...")
            tokens = []
            for img in images:
                abs_p = get_abs_path(img)
                print(f"Checking: {abs_p}")
                if abs_p and os.path.exists(abs_p):
                    print(f"Uploading: {abs_p}")
                    token = await upload_image_to_tripo(abs_p)
                    tokens.append(token)
            
            if not tokens: raise ValueError("No valid local images found to upload")
            task_id = await start_multiview_to_3d_task(file_tokens=tokens)
            print(f"SUCCESS (Multiview): {task_id}")
        else:
            print("Trying Single View (all_images=true but only 1 image)...")
            target = images[0]
            abs_p = get_abs_path(target)
            print(f"Checking: {abs_p}")
            if abs_p and os.path.exists(abs_p):
                print(f"Uploading: {abs_p}")
                token = await upload_image_to_tripo(abs_p)
                task_id = await start_image_to_3d_task(file_token=token)
                print(f"SUCCESS (Single): {task_id}")
            else:
                print("ABSOLUTE PATH NOT FOUND")
                
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(diagnose_product_10())
