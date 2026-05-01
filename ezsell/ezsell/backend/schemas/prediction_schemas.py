"""
Enhanced Price Prediction Schemas with Validation
Title validation is handled by the LLM (via llm_pricing_service.validate_listing_content),
NOT by keyword/regex rules. Schemas here only check that required fields are non-empty.
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
    """Mobile price prediction input – title validation handled by LLM"""
    title: str = Field(..., min_length=3, description="Product title")
    description: str = Field(..., min_length=5, description="Product description")
    condition: ConditionEnum = Field(..., description="Product condition")
    brand: Optional[str] = Field(None)
    ram: Optional[int] = Field(None, ge=1, le=32)
    storage: Optional[int] = Field(None, ge=4, le=2048)
    battery: Optional[int] = Field(None, ge=1000, le=10000)
    camera: Optional[int] = Field(None, ge=1, le=200)
    screen_size: Optional[float] = Field(None, ge=3.0, le=8.0)

    @field_validator('title', 'description')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Samsung Galaxy S23 Ultra 256GB",
                "description": "Brand new Samsung Galaxy S23 Ultra with 12GB RAM, 256GB storage.",
                "condition": "new"
            }
        }

class LaptopPredictionInput(BaseModel):
    """Laptop price prediction input – title validation handled by LLM"""
    title: str = Field(..., min_length=3, description="Product title")
    description: str = Field(..., min_length=5, description="Product description")
    condition: ConditionEnum = Field(..., description="Product condition")
    brand: Optional[str] = Field(None)
    processor: Optional[str] = Field(None)
    ram: Optional[int] = Field(None, ge=2, le=128)
    storage: Optional[int] = Field(None, ge=128, le=4096)
    screen_size: Optional[float] = Field(None, ge=10.0, le=18.0)

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
                "description": "Dell XPS 15 with Intel Core i7 12th generation, 512GB NVMe SSD.",
                "condition": "used"
            }
        }

class FurniturePredictionInput(BaseModel):
    """Furniture price prediction input – title validation handled by LLM"""
    title: str = Field(..., min_length=3, description="Product title")
    description: str = Field(..., min_length=5, description="Product description")
    condition: ConditionEnum = Field(..., description="Product condition")
    material: Optional[str] = Field(None, description="Material type")
    furniture_type: Optional[str] = Field(None)
    dimensions: Optional[str] = Field(None)
    seating_capacity: Optional[int] = Field(None, ge=1, le=20)

    @field_validator('title', 'description', 'material')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Imported Italian Leather 7-Seater Sofa Set",
                "description": "Premium 7-seater L-shaped sofa, genuine Italian leather.",
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

class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None
