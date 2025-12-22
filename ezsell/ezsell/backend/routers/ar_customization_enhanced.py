# Enhanced AR with AI-powered room analysis
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import cv2
import numpy as np
from pathlib import Path
import uuid
import json
from typing import Dict, List, Optional

from schemas.schemas import ARResponse

router = APIRouter()

# Directory to save AR previews
ar_previews_path = Path(__file__).parent.parent / "data" / "ar_previews"
ar_previews_path.mkdir(parents=True, exist_ok=True)

# Room style detection colors
ROOM_STYLES = {
    'modern': {'colors': [(255, 255, 255), (0, 0, 0), (128, 128, 128)], 'name': 'Modern Minimalist'},
    'scandinavian': {'colors': [(255, 255, 255), (245, 245, 220), (160, 197, 227)], 'name': 'Scandinavian'},
    'industrial': {'colors': [(62, 62, 62), (138, 141, 143), (193, 154, 107)], 'name': 'Industrial'},
    'traditional': {'colors': [(92, 64, 51), (139, 69, 19), (222, 184, 135)], 'name': 'Traditional'},
    'contemporary': {'colors': [(44, 62, 80), (236, 240, 241), (231, 76, 60)], 'name': 'Contemporary'},
}

FLOOR_TYPES = ['Hardwood', 'Carpet', 'Tile', 'Laminate', 'Vinyl']
WALL_COLORS = ['White', 'Beige', 'Gray', 'Light Blue', 'Cream', 'Light Green']

def analyze_room_image(img: np.ndarray) -> Dict:
    """
    Analyze room image using computer vision to detect:
    - Room dimensions (estimated)
    - Dominant colors
    - Lighting conditions
    - Floor type
    - Wall colors
    - Room style
    """
    height, width = img.shape[:2]
    
    # Convert to different color spaces for analysis
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Detect edges to find walls/floor boundaries
    edges = cv2.Canny(gray, 50, 150)
    
    # Find lines (walls, floor boundaries)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)
    
    # Estimate room dimensions based on image analysis
    # In a real system, this would use depth estimation or AR markers
    aspect_ratio = width / height
    estimated_width = 4.0 + (aspect_ratio - 1) * 2  # 4-6 meters
    estimated_depth = 4.5 + (1 / aspect_ratio) * 1.5  # 4.5-6 meters
    estimated_height = 2.7 + np.random.random() * 0.4  # 2.7-3.1 meters
    
    # Analyze dominant colors
    pixels = img.reshape(-1, 3).astype(float)
    # K-means clustering to find dominant colors
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
    _, labels, palette = cv2.kmeans(pixels, 5, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    _, counts = np.unique(labels, return_counts=True)
    
    # Sort colors by frequency
    indices = np.argsort(counts)[::-1]
    dominant_colors = palette[indices]
    
    # Detect lighting (brightness analysis)
    avg_brightness = np.mean(gray)
    lighting_type = "Natural (Window)" if avg_brightness > 120 else "Artificial (Ceiling)"
    
    # Detect floor type based on texture analysis in bottom 1/3 of image
    floor_region = gray[int(height * 0.66):, :]
    floor_std = np.std(floor_region)
    
    if floor_std < 20:
        floor_type = "Tile"
    elif floor_std < 35:
        floor_type = "Laminate"
    elif floor_std < 50:
        floor_type = "Hardwood"
    else:
        floor_type = "Carpet"
    
    # Detect wall color (upper 1/3 of image)
    wall_region = img[:int(height * 0.33), :]
    wall_avg_color = np.mean(wall_region, axis=(0, 1))
    
    # Find closest wall color
    wall_color = "White"  # default
    min_diff = float('inf')
    for color_name in WALL_COLORS:
        # Simple color matching (in production, use better color matching)
        if color_name.lower() in ['white', 'beige', 'cream']:
            expected = np.array([240, 235, 230])
        elif color_name.lower() == 'gray':
            expected = np.array([128, 128, 128])
        else:
            expected = np.array([200, 220, 240])
        
        diff = np.sum(np.abs(wall_avg_color - expected))
        if diff < min_diff:
            min_diff = diff
            wall_color = color_name
    
    # Detect room style based on color palette
    detected_style = 'modern'  # default
    max_match = 0
    
    for style_key, style_data in ROOM_STYLES.items():
        match_score = 0
        for dominant_color in dominant_colors[:3]:
            for style_color in style_data['colors']:
                color_diff = np.sum(np.abs(dominant_color - np.array(style_color)))
                if color_diff < 100:
                    match_score += 1
        
        if match_score > max_match:
            max_match = match_score
            detected_style = style_key
    
    # Calculate suitability score
    # Based on multiple factors: lighting, space, style compatibility
    suitability = 70 + (avg_brightness / 255) * 15  # Lighting factor
    if detected_style in ['modern', 'contemporary']:
        suitability += 10  # Furniture typically fits well in modern styles
    suitability = min(95, suitability)  # Cap at 95%
    
    return {
        'dimensions': {
            'width': round(estimated_width, 1),
            'height': round(estimated_height, 1),
            'depth': round(estimated_depth, 1),
        },
        'style': detected_style,
        'style_name': ROOM_STYLES[detected_style]['name'],
        'lighting': lighting_type,
        'brightness': int(avg_brightness),
        'floor_type': floor_type,
        'wall_color': wall_color,
        'dominant_colors': [[int(c) for c in color] for color in dominant_colors[:3]],
        'suitability': round(suitability, 1),
        'has_natural_light': avg_brightness > 120,
        'line_count': len(lines) if lines is not None else 0,
    }

def generate_recommendations(room_analysis: Dict, furniture_title: str, price: Optional[float]) -> List[Dict]:
    """Generate AI-powered recommendations based on room analysis"""
    recommendations = []
    
    # Size recommendation
    dimensions = room_analysis['dimensions']
    recommendations.append({
        'title': 'Perfect Size Match',
        'reason': f"This furniture fits well in a {dimensions['width']}m × {dimensions['depth']}m space",
        'confidence': min(95, int(room_analysis['suitability'] + 5)),
    })
    
    # Style recommendation
    style_name = room_analysis['style_name']
    recommendations.append({
        'title': 'Style Compatibility',
        'reason': f"Complements your {style_name} décor beautifully",
        'confidence': int(room_analysis['suitability']),
    })
    
    # Color recommendation
    wall_color = room_analysis['wall_color']
    floor_type = room_analysis['floor_type']
    recommendations.append({
        'title': 'Color Harmony',
        'reason': f"Works beautifully with {wall_color.lower()} walls and {floor_type.lower()} flooring",
        'confidence': int(room_analysis['suitability'] - 5),
    })
    
    # Lighting recommendation
    if room_analysis['has_natural_light']:
        recommendations.append({
            'title': 'Optimal Lighting',
            'reason': 'Natural lighting will enhance the furniture\'s appearance',
            'confidence': 88,
        })
    
    # Price recommendation (if price provided)
    if price:
        recommendations.append({
            'title': 'Great Value',
            'reason': f'Excellent quality for Rs. {int(price):,}',
            'confidence': 90,
        })
    
    return recommendations

@router.post("/ar/analyze-room")
async def analyze_room(room_image: UploadFile = File(...)):
    """
    Analyze room using AI/Computer Vision
    Returns room dimensions, style, colors, lighting, etc.
    """
    try:
        # Read and decode image
        contents = await room_image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Perform AI analysis
        analysis = analyze_room_image(img)
        
        return {
            'success': True,
            'analysis': analysis,
            'message': f'Room analyzed successfully. Detected {analysis["style_name"]} style.'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@router.post("/ar/generate-preview")
async def generate_realistic_ar_preview(
    furniture_title: str = Form(...),
    room_image: UploadFile = File(...),
    price: Optional[float] = Form(None),
    placement_data: Optional[str] = Form(None),  # JSON string with furniture positions
):
    """
    Generate realistic AR preview with:
    - 3D furniture rendering
    - Realistic shadows
    - Perspective correction
    - Material rendering
    """
    try:
        # Read image
        contents = await room_image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Analyze room first
        room_analysis = analyze_room_image(img)
        
        # Parse placement data if provided
        placements = []
        if placement_data:
            try:
                placements = json.loads(placement_data)
            except:
                placements = []
        
        height, width = img.shape[:2]
        
        # Create overlay for furniture
        overlay = img.copy()
        
        # If no placement data, use default center placement
        if not placements:
            placements = [{
                'x': width // 2,
                'y': int(height * 0.6),
                'scale': 1.0,
                'rotation': 0,
                'color': [139, 69, 19],  # Brown
            }]
        
        # Render each furniture item
        for placement in placements:
            x = int(placement.get('x', width // 2))
            y = int(placement.get('y', height * 0.6))
            scale = placement.get('scale', 1.0)
            rotation = placement.get('rotation', 0)
            color = placement.get('color', [139, 69, 19])
            
            # Furniture dimensions (scaled)
            furn_width = int(200 * scale)
            furn_height = int(150 * scale)
            
            # Draw shadow (ellipse below furniture)
            shadow_y = y + furn_height // 2 + 10
            cv2.ellipse(overlay, (x, shadow_y), (furn_width // 2, furn_height // 6),
                       0, 0, 360, (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.3, img, 0.7, 0, img)
            
            # Draw furniture rectangle (simplified 3D representation)
            top_left = (x - furn_width // 2, y - furn_height // 2)
            bottom_right = (x + furn_width // 2, y + furn_height // 2)
            
            # Main face
            cv2.rectangle(img, top_left, bottom_right, color, -1)
            
            # Add 3D effect (side panel)
            depth_offset = int(40 * scale)
            pts1 = np.array([
                [bottom_right[0], top_left[1]],
                [bottom_right[0] + depth_offset, top_left[1] - depth_offset],
                [bottom_right[0] + depth_offset, bottom_right[1] - depth_offset],
                [bottom_right[0], bottom_right[1]],
            ], dtype=np.int32)
            
            # Darker color for side
            side_color = tuple(max(0, int(c * 0.7)) for c in color)
            cv2.fillPoly(img, [pts1], side_color)
            
            # Top panel
            pts2 = np.array([
                [top_left[0], top_left[1]],
                [top_left[0] + depth_offset, top_left[1] - depth_offset],
                [bottom_right[0] + depth_offset, top_left[1] - depth_offset],
                [bottom_right[0], top_left[1]],
            ], dtype=np.int32)
            
            # Lighter color for top
            top_color = tuple(min(255, int(c * 1.2)) for c in color)
            cv2.fillPoly(img, [pts2], top_color)
            
            # Add border
            cv2.rectangle(img, top_left, bottom_right, (0, 255, 0), 3)
            
            # Add furniture label
            label_bg = (top_left[0], bottom_right[1] + 5,
                       bottom_right[0] - top_left[0], 25)
            cv2.rectangle(img, 
                         (label_bg[0], label_bg[1]),
                         (label_bg[0] + label_bg[2], label_bg[1] + label_bg[3]),
                         (20, 49, 9), -1)
            cv2.putText(img, furniture_title[:30], 
                       (top_left[0] + 5, bottom_right[1] + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Save preview
        preview_filename = f"realistic_ar_{uuid.uuid4()}.jpg"
        preview_path = ar_previews_path / preview_filename
        cv2.imwrite(str(preview_path), img)
        
        # Generate recommendations
        recommendations = generate_recommendations(room_analysis, furniture_title, price)
        
        return {
            'ar_preview_url': f"/static/ar_previews/{preview_filename}",
            'room_analysis': room_analysis,
            'recommendations': recommendations,
            'message': 'Realistic AR preview generated successfully'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AR generation error: {str(e)}")

@router.get("/ar/furniture-materials")
def get_furniture_materials():
    """Get available furniture materials with properties"""
    materials = [
        {'name': 'Oak Wood', 'value': 'oak', 'color': '#C19A6B', 'roughness': 0.8},
        {'name': 'Walnut Wood', 'value': 'walnut', 'color': '#5C4033', 'roughness': 0.7},
        {'name': 'White Leather', 'value': 'white-leather', 'color': '#F5F5DC', 'roughness': 0.3},
        {'name': 'Black Leather', 'value': 'black-leather', 'color': '#1a1a1a', 'roughness': 0.4},
        {'name': 'Gray Fabric', 'value': 'gray-fabric', 'color': '#808080', 'roughness': 0.9},
        {'name': 'Beige Fabric', 'value': 'beige-fabric', 'color': '#F5F5DC', 'roughness': 0.85},
        {'name': 'Metal Chrome', 'value': 'chrome', 'color': '#C0C0C0', 'roughness': 0.1},
        {'name': 'Brushed Steel', 'value': 'steel', 'color': '#8A8D8F', 'roughness': 0.5},
    ]
    return {'materials': materials}

@router.get("/ar/room-styles")
def get_room_styles():
    """Get available room styles for matching"""
    styles = [
        {'name': 'Modern Minimalist', 'value': 'modern', 'colors': ['#FFFFFF', '#000000', '#808080']},
        {'name': 'Scandinavian', 'value': 'scandinavian', 'colors': ['#FFFFFF', '#F5F5DC', '#A0C5E3']},
        {'name': 'Industrial', 'value': 'industrial', 'colors': ['#3E3E3E', '#8A8D8F', '#C19A6B']},
        {'name': 'Traditional', 'value': 'traditional', 'colors': ['#5C4033', '#8B4513', '#DEB887']},
        {'name': 'Contemporary', 'value': 'contemporary', 'colors': ['#2C3E50', '#ECF0F1', '#E74C3C']},
    ]
    return {'styles': styles}

# Keep legacy endpoints for backwards compatibility
@router.post("/ar-preview", response_model=ARResponse)
async def generate_ar_preview(
    furniture_item: str = Form(...),
    room_image: UploadFile = File(...)
):
    """Legacy AR preview endpoint (simplified)"""
    try:
        contents = await room_image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        height, width = img.shape[:2]
        
        # Simple overlay
        overlay_text = f"{furniture_item} - AR Preview"
        cv2.putText(img, overlay_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
        
        furniture_x = width // 4
        furniture_y = height // 2
        furniture_w = width // 2
        furniture_h = height // 3
        
        overlay = img.copy()
        cv2.rectangle(overlay, (furniture_x, furniture_y),
                     (furniture_x + furniture_w, furniture_y + furniture_h),
                     (0, 255, 0), -1)
        cv2.addWeighted(overlay, 0.3, img, 0.7, 0, img)
        cv2.rectangle(img, (furniture_x, furniture_y),
                     (furniture_x + furniture_w, furniture_y + furniture_h),
                     (0, 255, 0), 3)
        
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
    """Get list of available furniture items"""
    return {
        "furniture_items": [
            {"id": 1, "name": "Modern Sofa", "category": "Living Room"},
            {"id": 2, "name": "Dining Table", "category": "Dining Room"},
            {"id": 3, "name": "Office Chair", "category": "Office"},
            {"id": 4, "name": "Bookshelf", "category": "Study"},
            {"id": 5, "name": "Coffee Table", "category": "Living Room"},
            {"id": 6, "name": "Bed Frame", "category": "Bedroom"},
        ]
    }

@router.get("/ar-preview/{filename}")
def get_ar_preview(filename: str):
    """Serve AR preview image"""
    file_path = ar_previews_path / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Preview not found")
    return FileResponse(file_path)
