# AR furniture customization endpoints
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import cv2
import numpy as np
from pathlib import Path
import uuid

from schemas.schemas import ARResponse

router = APIRouter()

# Directory to save AR previews
ar_previews_path = Path(__file__).parent.parent / "data" / "ar_previews"
ar_previews_path.mkdir(parents=True, exist_ok=True)

@router.post("/ar-preview", response_model=ARResponse)
async def generate_ar_preview(
    furniture_item: str,
    room_image: UploadFile = File(...)
):
    """Generate an AR preview of furniture in the user's room"""
    
    try:
        # Read the uploaded image
        contents = await room_image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Simple AR overlay simulation (in production, use advanced AR libraries)
        height, width = img.shape[:2]
        
        # Add furniture overlay text (placeholder - would use actual 3D models)
        overlay_text = f"{furniture_item} - AR Preview"
        cv2.putText(img, overlay_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
        
        # Draw a placeholder rectangle to represent furniture
        furniture_x = width // 4
        furniture_y = height // 2
        furniture_w = width // 2
        furniture_h = height // 3
        
        # Semi-transparent overlay
        overlay = img.copy()
        cv2.rectangle(overlay, (furniture_x, furniture_y), 
                     (furniture_x + furniture_w, furniture_y + furniture_h), 
                     (0, 255, 0), -1)
        cv2.addWeighted(overlay, 0.3, img, 0.7, 0, img)
        
        # Add border
        cv2.rectangle(img, (furniture_x, furniture_y), 
                     (furniture_x + furniture_w, furniture_y + furniture_h), 
                     (0, 255, 0), 3)
        
        # Save the AR preview
        preview_filename = f"ar_preview_{uuid.uuid4()}.jpg"
        preview_path = ar_previews_path / preview_filename
        cv2.imwrite(str(preview_path), img)
        
        return ARResponse(
            ar_preview_url=f"/static/ar_previews/{preview_filename}",
            message="AR preview generated successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AR generation error: {str(e)}")

@router.get("/furniture-items")
def get_available_furniture():
    """Get list of available furniture items for AR preview"""
    furniture_items = [
        {"id": 1, "name": "Modern Sofa", "category": "Living Room"},
        {"id": 2, "name": "Dining Table", "category": "Dining Room"},
        {"id": 3, "name": "Office Chair", "category": "Office"},
        {"id": 4, "name": "Bookshelf", "category": "Study"},
        {"id": 5, "name": "Coffee Table", "category": "Living Room"},
        {"id": 6, "name": "Bed Frame", "category": "Bedroom"}
    ]
    return {"furniture_items": furniture_items}

@router.get("/ar-preview/{filename}")
def get_ar_preview(filename: str):
    """Serve an AR preview image"""
    file_path = ar_previews_path / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Preview not found")
    return FileResponse(file_path)
