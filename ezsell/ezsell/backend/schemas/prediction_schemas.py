"""
Enhanced Price Prediction Schemas with Validation
Ensures all required fields are present for accurate predictions
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from enum import Enum

class CategoryEnum(str, Enum):
    mobile = "mobile"
    laptop = "laptop"
    furniture = "furniture"

class ConditionEnum(str, Enum):
    new = "new"
    used = "used"
    refurbished = "refurbished"

class MobilePredictionInput(BaseModel):
    """Mobile price prediction input with required fields"""
    title: str = Field(..., min_length=10, description="Product title (required, min 10 characters)")
    description: str = Field(..., min_length=20, description="Product description (required, min 20 characters)")
    condition: ConditionEnum = Field(..., description="Product condition (required)")
    
    # Optional fields that will be extracted from title/description if not provided
    brand: Optional[str] = Field(None, description="Mobile brand (optional, will be extracted)")
    ram: Optional[int] = Field(None, ge=1, le=32, description="RAM in GB (optional)")
    storage: Optional[int] = Field(None, ge=4, le=2048, description="Storage in GB (optional)")
    battery: Optional[int] = Field(None, ge=1000, le=10000, description="Battery in mAh (optional)")
    camera: Optional[int] = Field(None, ge=1, le=200, description="Camera in MP (optional)")
    screen_size: Optional[float] = Field(None, ge=3.0, le=8.0, description="Screen size in inches (optional)")
    
    @field_validator('title', 'description')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Samsung Galaxy S23 Ultra 12GB RAM 256GB Storage",
                "description": "Brand new Samsung Galaxy S23 Ultra with 12GB RAM, 256GB storage, 5000mAh battery, 200MP camera, 6.8 inch display. PTA approved with complete box and warranty.",
                "condition": "new"
            }
        }

class LaptopPredictionInput(BaseModel):
    """Laptop price prediction input with required fields"""
    title: str = Field(..., min_length=10, description="Product title (required, min 10 characters)")
    description: str = Field(..., min_length=20, description="Product description (required, min 20 characters)")
    condition: ConditionEnum = Field(..., description="Product condition (required)")
    
    # Optional fields
    brand: Optional[str] = Field(None, description="Laptop brand (optional)")
    processor: Optional[str] = Field(None, description="Processor details (optional)")
    ram: Optional[int] = Field(None, ge=2, le=128, description="RAM in GB (optional)")
    storage: Optional[int] = Field(None, ge=128, le=4096, description="Storage in GB (optional)")
    screen_size: Optional[float] = Field(None, ge=10.0, le=18.0, description="Screen size in inches (optional)")
    
    @field_validator('title', 'description')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Dell XPS 15 i7 12th Gen 16GB RAM 512GB SSD",
                "description": "Dell XPS 15 with Intel Core i7 12th generation processor, 16GB DDR4 RAM, 512GB NVMe SSD, NVIDIA RTX 3050 4GB graphics, 15.6 inch Full HD display. Excellent condition with backlit keyboard.",
                "condition": "used"
            }
        }

class FurniturePredictionInput(BaseModel):
    """Furniture price prediction input with required fields"""
    title: str = Field(..., min_length=10, description="Product title (required, min 10 characters)")
    description: str = Field(..., min_length=20, description="Product description (required, min 20 characters)")
    condition: ConditionEnum = Field(..., description="Product condition (required)")
    material: str = Field(..., min_length=3, description="Material type (required, e.g., wood, metal, leather)")
    
    # Optional fields
    furniture_type: Optional[str] = Field(None, description="Type of furniture (optional)")
    dimensions: Optional[str] = Field(None, description="Dimensions LxWxH in cm (optional)")
    seating_capacity: Optional[int] = Field(None, ge=1, le=20, description="Seating capacity (optional)")
    
    @field_validator('title', 'description', 'material')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Field cannot be empty - this field is critical for price prediction')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Imported Italian Leather 7-Seater Sofa Set",
                "description": "Premium imported 7-seater L-shaped sofa set made from genuine Italian leather. Includes 2 recliners and coffee table. Dimensions: 280x180x85 cm. Excellent condition, barely used. Modern design with dark brown color.",
                "condition": "used",
                "material": "genuine leather"
            }
        }

class PredictionResponse(BaseModel):
    """Price prediction response"""
    success: bool
    category: str
    predicted_price: float
    confidence: str
    price_range: Dict[str, float]
    extracted_features: Dict[str, Any]
    message: str
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "category": "mobile",
                "predicted_price": 285000.0,
                "confidence": "high",
                "price_range": {
                    "min": 282000.0,
                    "max": 288000.0
                },
                "extracted_features": {
                    "brand": "Samsung",
                    "ram": 12,
                    "storage": 256,
                    "is_5g": True,
                    "is_pta": True,
                    "brand_premium": 4
                },
                "message": "Price predicted successfully with high confidence"
            }
        }

class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": "Missing required field: title cannot be empty",
                "details": {
                    "field": "title",
                    "requirement": "minimum 10 characters"
                }
            }
        }
