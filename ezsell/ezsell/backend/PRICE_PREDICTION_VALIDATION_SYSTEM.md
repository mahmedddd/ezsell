# 🎯 Price Prediction System - Strict Validation & Dropdown Configuration

## ✅ Implementation Complete

### **Overview**
The price prediction system now includes **strict title validation** to prevent irrelevant predictions. The model **will NOT predict** prices unless the title contains category-specific required information.

---

## 🚫 Strict Validation Rules

### **Mobile Phones**
**REQUIRED in Title:**
- ✅ Brand name (Samsung, iPhone, Xiaomi, Oppo, Vivo, etc.)
- ✅ Model name/number (optional but recommended: S23, 14 Pro, Redmi 12, etc.)

**Validation Examples:**
- ✅ VALID: "Samsung Galaxy S23 Ultra 12GB RAM 256GB"
- ✅ VALID: "iPhone 14 Pro Max 256GB PTA Approved"
- ❌ INVALID: "Mobile phone for sale" (no brand)
- ❌ INVALID: "Phone 8GB RAM good condition" (no brand/model)

**Why:** Mobile specs (especially iPhones) aren't always clearly mentioned, so we rely on NLP extraction from title/description.

---

### **Laptops**
**REQUIRED in Title:**
- ✅ Brand name (Dell, HP, Lenovo, Apple MacBook, etc.)
- ✅ Processor info OR generation OR RAM (i7, 12th Gen, Ryzen 5, M2, 16GB RAM, etc.)

**Validation Examples:**
- ✅ VALID: "Dell XPS 15 Intel Core i7 12th Gen 16GB RAM"
- ✅ VALID: "MacBook Pro M2 16GB 512GB SSD"
- ✅ VALID: "HP Pavilion Ryzen 5 8GB RAM"
- ❌ INVALID: "Laptop for sale" (no brand)
- ❌ INVALID: "Dell laptop good condition" (no specs)

**Why:** Laptops need specific model/processor info for accurate price prediction.

---

### **Furniture**
**REQUIRED in Title:**
- ✅ Furniture type (Sofa, Chair, Table, Bed, Wardrobe, etc.)
- ✅ Material (Wood, Leather, Fabric, Metal, etc.) - can be in separate field

**Validation Examples:**
- ✅ VALID: "Modern 5 Seater L-Shape Sofa - Premium Fabric"
- ✅ VALID: "Wooden Dining Table 6 Seater with Chairs"
- ✅ VALID: "Leather Recliner Chair" (with material field = "Genuine Leather")
- ❌ INVALID: "Furniture for sale" (no type)
- ❌ INVALID: "5 seater set" (no furniture type)

**Why:** Furniture prices vary drastically based on type and material.

---

## 🎨 Frontend Features

### **New Price Prediction Page: `PricePredictionNew.tsx`**

**Key Features:**
1. **Real-time Title Validation**
   - Validates as you type (debounced 800ms)
   - Shows green checkmark ✓ for valid titles
   - Shows red X with error message for invalid titles
   - Provides example titles

2. **Dropdown Menus for All Fields**
   - **Condition**: New, Used, Refurbished
   - **Brand**: Category-specific brand lists
   - **RAM/Storage**: Predefined options (2/4/6/8/12/16/24GB RAM)
   - **Processors**: Intel i3/i5/i7, AMD Ryzen, Apple M1/M2/M3
   - **Materials**: Wood, Leather, Fabric, Metal, etc.
   - **Boolean Features**: 5G, PTA, AMOLED, SSD, Gaming, Touchscreen, etc.

3. **Required vs Optional Fields**
   - **Required**: Title, Description, Condition
   - **Furniture**: Material is REQUIRED
   - **All others**: Optional (auto-extracted from title/description via NLP)

4. **Disabled Predict Button**
   - Button is disabled if:
     - Title is empty
     - Description is empty
     - Title validation fails
     - Material is missing (furniture only)

---

## 🔧 Backend Implementation

### **1. Title Validator (`utils/title_validator.py`)**

**Features:**
- Category-specific keyword dictionaries
- Brand/model/type extraction
- Detailed validation messages
- Helpful hints for users

**Methods:**
```python
TitleValidator.validate_mobile_title(title, description)
TitleValidator.validate_laptop_title(title, description)
TitleValidator.validate_furniture_title(title, description, material)
TitleValidator.validate_title(category, title, description, **kwargs)
TitleValidator.get_validation_hints(category)
TitleValidator.extract_keywords(category, text)
```

**Keyword Dictionaries:**
- **Mobile Brands**: 30+ brands (Apple, Samsung, Xiaomi, Oppo, Vivo, Tecno, etc.)
- **Laptop Brands**: 25+ brands (Dell, HP, Lenovo, Asus, Apple, MSI, etc.)
- **Laptop Processors**: 15+ keywords (Intel, Core, i3/i5/i7/i9, AMD, Ryzen, M1/M2/M3)
- **Furniture Types**: 40+ types (Sofa, Chair, Table, Bed, Cabinet, etc.)
- **Furniture Materials**: 30+ materials (Wood, Leather, Fabric, Metal, Glass, etc.)

---

### **2. Updated Prediction Schemas (`schemas/prediction_schemas.py`)**

**Enhanced with Validators:**
```python
class MobilePredictionInput(BaseModel):
    title: str = Field(..., min_length=10)
    description: str = Field(..., min_length=20)
    condition: ConditionEnum
    
    @model_validator(mode='after')
    def validate_mobile_title_content(self):
        is_valid, error_msg, _ = TitleValidator.validate_mobile_title(...)
        if not is_valid:
            raise ValueError(error_msg)
        return self
```

**Same pattern for:**
- `LaptopPredictionInput`
- `FurniturePredictionInput`

---

### **3. API Endpoints (`routers/predictions_advanced.py`)**

#### **A. Prediction Endpoint (Updated)**
```python
POST /api/v1/predict-price
```

**New Features:**
- Validates title BEFORE making prediction
- Returns 422 error with helpful hints if validation fails
- Only predicts if title contains relevant information

**Error Response:**
```json
{
  "detail": {
    "error": "Title validation failed",
    "message": "Mobile title must include a brand name (e.g., Samsung, iPhone, Xiaomi...)",
    "hints": {
      "required": ["Brand name (e.g., Samsung, iPhone, Xiaomi)"],
      "recommended": ["Model number/name", "RAM and storage"],
      "example": "Samsung Galaxy S23 Ultra 12GB RAM 256GB Storage"
    }
  }
}
```

#### **B. Validation Endpoint (New)**
```python
POST /api/v1/validate-title
```

**Parameters:**
- `category`: mobile | laptop | furniture
- `title`: Product title
- `description`: Product description (optional)
- `material`: Material (furniture only, optional)

**Response:**
```json
{
  "is_valid": true,
  "message": "Title is valid and contains relevant information",
  "extracted_info": {
    "brands": ["Samsung"],
    "has_model_info": true
  },
  "hints": { ... }
}
```

#### **C. Dropdown Options Endpoint (New)**
```python
GET /api/v1/dropdown-options/{category}
```

**Returns:**
- Condition options
- Brand lists
- RAM/Storage options
- Processor options (laptops)
- Material options (furniture)
- Boolean feature labels

**Example Response:**
```json
{
  "condition": ["new", "used", "refurbished"],
  "brands": ["Apple", "Samsung", "Xiaomi", ...],
  "ram_options": [2, 4, 6, 8, 12, 16, 24],
  "boolean_features": {
    "has_5g": "5G Support",
    "has_pta": "PTA Approved"
  }
}
```

#### **D. Validation Hints Endpoint (New)**
```python
GET /api/v1/validation-hints/{category}
```

**Returns helpful hints for creating valid titles**

---

## 📊 Dropdown Options Summary

### **Mobile**
- **Brands**: 15 options (Apple, Samsung, Xiaomi, Oppo, Vivo, etc.)
- **RAM**: 9 options (2-24GB)
- **Storage**: 7 options (16GB-1TB)
- **Battery**: 6 options (3000-7000mAh, 0=Unknown)
- **Camera**: 11 options (12-200MP, 0=Unknown)
- **Screen Size**: 8 options (5.5"-7.0", 0=Unknown)
- **Boolean**: 5 features (5G, PTA, AMOLED, Warranty, Box)

### **Laptop**
- **Brands**: 12 options (Dell, HP, Lenovo, Apple, etc.)
- **Processors**: 13 options (i3/i5/i7/i9, Ryzen 3/5/7/9, M1/M2/M3)
- **Generation**: 9 options (6th-14th Gen)
- **RAM**: 7 options (4-64GB)
- **Storage**: 5 options (128GB-2TB)
- **GPU**: 8 options (Integrated, GTX/RTX series)
- **Screen Size**: 5 options (13.3"-17.3")
- **Boolean**: 5 features (SSD, Gaming, Touchscreen, Backlit, Fingerprint)

### **Furniture**
- **Materials**: 27 options (Wood, Leather, Fabric, Metal, etc.)
- **Types**: 16 options (Sofa, Chair, Table, Bed, etc.)
- **Seating**: 11 options (1-12 seater, 0=N/A)
- **Boolean**: 6 features (Imported, Handmade, Storage, Modern, Antique, Foldable)

---

## 🎯 NLP-Based Feature Extraction

**The system uses NLP to extract features from title/description:**

### **For Mobiles:**
- Brand detection
- Model number patterns (S23, 14 Pro, Redmi 12)
- RAM/Storage extraction (8GB RAM, 256GB)
- Camera specs (200MP)
- Battery specs (5000mAh)
- Boolean features (5G, PTA, AMOLED)

### **For Laptops:**
- Brand detection
- Processor extraction (i7, Ryzen 5, M2)
- Generation detection (12th Gen)
- RAM/Storage extraction
- GPU detection (RTX 3050, GTX 1650)
- Boolean features (SSD, Gaming, Touchscreen)

### **For Furniture:**
- Type detection (Sofa, Chair, Table)
- Material detection (Wood, Leather, Fabric)
- Dimensions extraction
- Seating capacity (5 seater)
- Boolean features (Modern, Antique, Imported)

---

## 🚀 How to Use

### **Frontend Integration**

1. **Replace old PricePrediction page** in your routing:
```tsx
// In App.tsx or routing config
import PricePredictionNew from '@/pages/PricePredictionNew';

// Use PricePredictionNew instead of PricePrediction
```

2. **Or test separately:**
```tsx
// Access at /price-prediction-new route
```

### **Backend is Already Configured**
- All endpoints are live in `predictions_advanced.py`
- Validation is automatic in all prediction requests
- No additional setup required

---

## 📝 User Experience Flow

1. **User selects category** (Mobile/Laptop/Furniture)
2. **Dropdown options load** for that category
3. **User types title**
   - Real-time validation starts after 800ms delay
   - Green checkmark ✓ appears if valid
   - Red X with error message if invalid
4. **User fills description** and selects dropdowns
5. **Predict button**
   - Disabled if title invalid
   - Enabled when title valid + required fields filled
6. **Prediction** happens ONLY if validation passes
7. **Result shows:**
   - Predicted price with confidence range
   - Model accuracy information
   - Pricing recommendation

---

## 🛡️ Error Prevention

**The system prevents irrelevant predictions by:**
1. ✅ Frontend validation (UI hints)
2. ✅ API request validation (Pydantic schemas)
3. ✅ Title content validation (TitleValidator)
4. ✅ Category-specific keyword checking
5. ✅ Helpful error messages with examples

**Users CANNOT:**
- ❌ Submit empty titles
- ❌ Submit generic titles ("laptop for sale")
- ❌ Predict without brand/model information
- ❌ Submit furniture without type/material
- ❌ Bypass validation (enforced at API level)

---

## 📊 Model Performance (Unchanged)

- **Laptop**: XGBRegressor - 92.29% R², MAE Rs.1,702
- **Mobile**: XGBRegressor - 99.94% R², MAE Rs.168
- **Furniture**: StackingRegressor - 99.96% R², MAE Rs.109

All models loaded successfully from `models_enhanced/` folder using joblib.

---

## 🔗 API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/predict-price` | POST | Predict price (with validation) |
| `/api/v1/predict-price-with-dropdowns` | POST | Alias for frontend compatibility |
| `/api/v1/validate-title` | POST | Validate title before submission |
| `/api/v1/dropdown-options/{category}` | GET | Get dropdown options for category |
| `/api/v1/validation-hints/{category}` | GET | Get validation hints/examples |
| `/api/v1/model-info/{category}` | GET | Get model metadata |

---

## ✅ Completed Tasks

- [x] Title validation utility with keyword dictionaries
- [x] Category-specific validation rules
- [x] Updated prediction schemas with validators
- [x] API validation endpoints
- [x] Dropdown options endpoint
- [x] Enhanced frontend with real-time validation
- [x] Dropdown menus for all fields
- [x] Boolean feature checkboxes
- [x] Title validation UI (green/red indicators)
- [x] Helpful error messages and examples
- [x] NLP-based feature extraction
- [x] Strict policy enforcement (no irrelevant predictions)

---

## 🎉 System is Production Ready!

All components are configured and tested. The system now:
- ✅ Prevents irrelevant predictions
- ✅ Guides users with helpful hints
- ✅ Provides dropdowns for easy selection
- ✅ Validates titles in real-time
- ✅ Uses NLP for automatic feature extraction
- ✅ Maintains high model accuracy (92-99% R²)
