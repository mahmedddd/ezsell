# Pydantic schemas for request/response validation
from pydantic import BaseModel, EmailStr
from typing import Optional, Union, Dict, List, Any
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str
    phone: str  # Mandatory for creation

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    is_active: bool
    is_verified: bool
    is_admin: bool
    created_at: datetime
    last_seen: Optional[datetime] = None
    is_online: Optional[bool] = False
    phone: Optional[str] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Category-Specific Detail Schemas
class MobilePhoneDetails(BaseModel):
    brand: Optional[str] = None

class LaptopDetails(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None

class FurnitureDetails(BaseModel):
    type: Optional[str] = None
    material: Optional[str] = None

# Listing Schemas
class ListingBase(BaseModel):
    title: str
    description: str
    price: float
    category: str
    condition: str
    location: Optional[str] = None
    images: Optional[str] = None  # JSON array of image URLs
    brand: Optional[str] = None
    furniture_type: Optional[str] = None
    material: Optional[str] = None
    furniture_subtype: Optional[str] = None  # e.g. "3_door", "4_door", "sliding"
    # Furniture enhancements
    furniture_brand: Optional[str] = None
    is_sliding_door: Optional[bool] = False
    has_mattress: Optional[bool] = False
    mattress_type: Optional[str] = None
    color: Optional[str] = None

class ListingCreate(ListingBase):
    # Category-specific details
    mobile_details: Optional[MobilePhoneDetails] = None
    laptop_details: Optional[LaptopDetails] = None
    furniture_details: Optional[FurnitureDetails] = None

class ListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    condition: Optional[str] = None
    location: Optional[str] = None
    images: Optional[str] = None  # JSON array of image URLs
    is_sold: Optional[bool] = None
    is_active: Optional[bool] = None
    # Furniture enhancements
    furniture_type: Optional[str] = None
    material: Optional[str] = None
    furniture_subtype: Optional[str] = None
    furniture_brand: Optional[str] = None
    is_sliding_door: Optional[bool] = None
    has_mattress: Optional[bool] = None
    mattress_type: Optional[str] = None

class OwnerInfo(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    
    class Config:
        from_attributes = True

class ListingResponse(ListingBase):
    id: int
    is_sold: bool
    is_active: bool
    views: int
    created_at: datetime
    updated_at: datetime
    owner_id: int
    owner: Optional[OwnerInfo] = None
    approval_status: Optional[str] = "approved"
    predicted_price: Optional[float] = None
    fraud_flags: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    class Config:
        from_attributes = True

# Price Prediction Schemas
class PricePredictionRequest(BaseModel):
    category: str
    title: str
    description: Optional[str] = ""
    condition: Optional[str] = "used"
    # Mobile fields
    brand: Optional[str] = ""
    ram: Optional[int] = 0
    storage: Optional[int] = 0
    camera: Optional[int] = 0
    battery: Optional[int] = 0
    screen_size: Optional[float] = 0
    has_5g: Optional[bool] = False
    has_pta: Optional[bool] = False
    has_amoled: Optional[bool] = False
    has_warranty: Optional[bool] = False
    has_box: Optional[bool] = False
    # Laptop fields
    processor: Optional[str] = ""
    generation: Optional[Union[str, int]] = ""  # Accept both string and int
    gpu: Optional[str] = ""
    has_ssd: Optional[bool] = False
    is_gaming: Optional[bool] = False
    is_touchscreen: Optional[bool] = False
    # Furniture fields
    material: Optional[str] = ""
    frame_material: Optional[str] = ""
    furniture_style: Optional[str] = ""
    storage_type: Optional[str] = ""
    furniture_type: Optional[str] = ""
    furniture_subtype: Optional[str] = ""  # e.g., king_size, queen_size for bed; dining, coffee for table
    seating_capacity: Optional[int] = 0
    is_imported: Optional[bool] = False
    is_handmade: Optional[bool] = False
    has_storage: Optional[bool] = False
    is_modern: Optional[bool] = False
    is_antique: Optional[bool] = False
    is_sliding_door: Optional[bool] = False
    has_mattress: Optional[bool] = False
    mattress_type: Optional[str] = ""
    furniture_brand: Optional[str] = ""
    # Dynamic LLM generated specs from frontend
    dynamic_specs: Optional[Dict[str, str]] = None

class PricePredictionResponse(BaseModel):
    predicted_price: float
    confidence_score: Optional[float] = 0.95
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None
    price_range_min: Optional[float] = None
    price_range_max: Optional[float] = None
    recommendation: Optional[str] = None
    extracted_features: Optional[dict] = None
    llm_price: Optional[float] = None
    ml_price: Optional[float] = None
    data_source: Optional[str] = None
    reasoning: Optional[str] = None
    simulated_market_data: Optional[List[Dict[str, Any]]] = None

class DynamicDropdownResponse(BaseModel):
    dropdowns: dict

# AR Customization Schemas
class ARRequest(BaseModel):
    furniture_item: str
    room_image_url: str

class ARResponse(BaseModel):
    ar_preview_url: str
    message: str

# Message/Chat Schemas
class MessageCreate(BaseModel):
    content: str
    receiver_id: int
    listing_id: Optional[int] = None

class MessageResponse(BaseModel):
    id: int
    content: str
    sender_id: int
    receiver_id: int
    listing_id: Optional[int] = None
    is_read: bool
    created_at: datetime
    sender_username: Optional[str] = None
    receiver_username: Optional[str] = None
    listing_title: Optional[str] = None
    listing_image: Optional[str] = None
    
    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    user_id: int
    username: str
    avatar_url: Optional[str] = None
    listing_id: Optional[int] = None
    listing_title: Optional[str] = None
    listing_image: Optional[str] = None
    listing_price: Optional[float] = None
    last_message: str
    last_message_time: datetime
    unread_count: int
    last_seen: Optional[datetime] = None
    is_online: bool = False

class ImageValidationResponse(BaseModel):
    is_match: bool
    confidence: float
    best_label: str

# Support Ticket Schemas
class SupportTicketBase(BaseModel):
    ticket_type: str  # 'support' or 'bug'
    subject: str
    description: str
    attachment_url: Optional[str] = None

class SupportTicketCreate(SupportTicketBase):
    pass

class TicketOwnerInfo(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True

class SupportTicketResponse(SupportTicketBase):
    id: int
    user_id: int
    user: Optional[TicketOwnerInfo] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class TicketStatusUpdate(BaseModel):
    status: str

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    link: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
