"""
🏷️ Brand Categorization and Material Encoding System
Comprehensive brand tiers and material quality scores for accurate price prediction
"""

# ================================
# MOBILE BRAND CATEGORIZATION
# ================================
MOBILE_BRANDS = {
    "Premium (9-10)": {
        "Apple": 10,
        "iPhone": 10,
        "Google Pixel": 9,
        "Samsung Galaxy S Series": 9,
        "OnePlus Pro": 9,
    },
    "High-End (7-8)": {
        "Samsung": 8,
        "OnePlus": 8,
        "Huawei": 7,
        "Sony": 7,
    },
    "Mid-Range (5-6)": {
        "Xiaomi": 6,
        "Poco": 6,
        "Oppo": 6,
        "Vivo": 6,
        "Realme": 5,
        "Honor": 6,
        "Nokia": 5,
        "Motorola": 5,
        "LG": 6,
    },
    "Budget (3-4)": {
        "Infinix": 4,
        "Tecno": 4,
        "Itel": 3,
        "Redmi": 5,
    }
}

# Flatten for API
MOBILE_BRAND_SCORES = {
    "Apple": 10,
    "iPhone": 10,
    "Google Pixel": 9,
    "Samsung": 8,
    "OnePlus": 8,
    "Xiaomi": 6,
    "Poco": 6,
    "Oppo": 6,
    "Vivo": 6,
    "Realme": 5,
    "Redmi": 5,
    "Huawei": 7,
    "Honor": 6,
    "Nokia": 5,
    "Motorola": 5,
    "Sony": 7,
    "LG": 6,
    "Infinix": 4,
    "Tecno": 4,
    "Itel": 3,
}

# ================================
# LAPTOP BRAND CATEGORIZATION
# ================================
LAPTOP_BRANDS = {
    "Premium (9-10)": {
        "Apple MacBook": 10,
        "Apple": 10,
        "MacBook": 10,
        "Razer": 9,
        "Alienware": 9,
        "Microsoft Surface": 8,
    },
    "High-End (7-8)": {
        "Dell": 7,
        "HP": 6,
        "Lenovo": 7,
        "Asus": 7,
        "MSI": 8,
        "ThinkPad": 8,
    },
    "Mid-Range (5-6)": {
        "Acer": 5,
        "HP Pavilion": 6,
        "Lenovo IdeaPad": 6,
    },
}

# Flatten for API
LAPTOP_BRAND_SCORES = {
    "Apple": 10,
    "MacBook": 10,
    "Razer": 9,
    "Alienware": 9,
    "Microsoft Surface": 8,
    "MSI": 8,
    "ThinkPad": 8,
    "Dell": 7,
    "Lenovo": 7,
    "Asus": 7,
    "HP": 6,
    "Acer": 5,
}

# ================================
# FURNITURE MATERIAL CATEGORIZATION
# ================================
FURNITURE_MATERIALS = {
    "Premium Wood (8-10)": {
        "Teak": 9,
        "Sheesham": 9,
        "Walnut": 9,
        "Oak": 8,
        "Mahogany": 8,
        "Solid Wood": 8,
        "Cherry": 8,
    },
    "Standard Wood (6-7)": {
        "Wood": 7,
        "Wooden": 7,
        "Pine": 6,
        "Engineered Wood": 6,
    },
    "Budget Materials (3-5)": {
        "MDF": 5,
        "Particle Board": 4,
        "Plywood": 5,
        "Plastic": 3,
        "Foam": 2,
    },
    "Metal & Others (5-7)": {
        "Metal": 6,
        "Steel": 6,
        "Iron": 6,
        "Glass": 5,
        "Leather": 7,
        "Fabric": 5,
        "Velvet": 6,
    }
}

# Flatten for API
MATERIAL_QUALITY_SCORES = {
    "Teak": 9,
    "Sheesham": 9,
    "Walnut": 9,
    "Oak": 8,
    "Mahogany": 8,
    "Solid Wood": 8,
    "Cherry": 8,
    "Wood": 7,
    "Wooden": 7,
    "Leather": 7,
    "Pine": 6,
    "Engineered Wood": 6,
    "Metal": 6,
    "Steel": 6,
    "Iron": 6,
    "Velvet": 6,
    "MDF": 5,
    "Plywood": 5,
    "Glass": 5,
    "Fabric": 5,
    "Particle Board": 4,
    "Plastic": 3,
    "Foam": 2,
}

# ================================
# CONDITION SCORES (All Categories)
# ================================
CONDITION_SCORES = {
    "new": 6,
    "brand new": 6,
    "sealed": 6,
    "excellent": 5,
    "mint": 5,
    "like new": 5,
    "good": 4,
    "very good": 4,
    "fair": 3,
    "used": 3,
    "poor": 2,
    "damaged": 2,
    "faulty": 2,
    "for parts": 1,
}

# ================================
# PROCESSOR TIERS (Laptops)
# ================================
PROCESSOR_TIERS = {
    "i9": 9,
    "Core i9": 9,
    "i7": 7,
    "Core i7": 7,
    "i5": 5,
    "Core i5": 5,
    "i3": 3,
    "Core i3": 3,
    "Ryzen 9": 9,
    "Ryzen 7": 7,
    "Ryzen 5": 5,
    "Ryzen 3": 3,
    "M3": 10,
    "M2": 10,
    "M1": 9,
    "Celeron": 2,
    "Pentium": 2,
}

# ================================
# GPU TIERS (Laptops)
# ================================
GPU_TIERS = {
    "None": 0,
    "Intel UHD": 0,
    "Intel HD": 0,
    "MX150": 2,
    "MX250": 2,
    "MX350": 3,
    "MX450": 3,
    "GTX 1050": 4,
    "GTX 1650": 5,
    "GTX 1660": 5,
    "RTX 2060": 6,
    "RTX 3050": 6,
    "RTX 3060": 7,
    "RTX 3070": 8,
    "RTX 4050": 7,
    "RTX 4060": 8,
    "RTX 4070": 9,
}


def get_brand_score(brand: str, category: str) -> int:
    """Get brand premium score based on category"""
    brand_lower = brand.lower()
    
    if category == "mobile":
        for brand_name, score in MOBILE_BRAND_SCORES.items():
            if brand_name.lower() in brand_lower:
                return score
        return 5  # Default mid-range
    
    elif category == "laptop":
        for brand_name, score in LAPTOP_BRAND_SCORES.items():
            if brand_name.lower() in brand_lower:
                return score
        return 6  # Default mid-range
    
    return 5


def get_material_score(material: str) -> int:
    """Get material quality score"""
    material_lower = material.lower()
    
    for material_name, score in MATERIAL_QUALITY_SCORES.items():
        if material_name.lower() in material_lower:
            return score
    
    return 5  # Default mid-range


def get_condition_score(condition: str) -> int:
    """Get condition score"""
    condition_lower = condition.lower()
    
    for cond_name, score in CONDITION_SCORES.items():
        if cond_name in condition_lower:
            return score
    
    return 4  # Default good condition


def get_processor_tier(processor: str) -> int:
    """Get processor tier score"""
    processor_lower = processor.lower()
    
    for proc_name, tier in PROCESSOR_TIERS.items():
        if proc_name.lower() in processor_lower:
            return tier
    
    return 5  # Default mid-tier


def get_gpu_tier(gpu: str) -> int:
    """Get GPU tier score"""
    gpu_lower = gpu.lower()
    
    for gpu_name, tier in GPU_TIERS.items():
        if gpu_name.lower() in gpu_lower:
            return tier
    
    return 0  # Default no GPU


# ================================
# API DROPDOWN OPTIONS
# ================================
def get_dropdown_options(category: str):
    """Get organized dropdown options for frontend"""
    
    if category == "mobile":
        return {
            "brands": {
                "Premium": list(MOBILE_BRANDS["Premium (9-10)"].keys()),
                "High-End": list(MOBILE_BRANDS["High-End (7-8)"].keys()),
                "Mid-Range": list(MOBILE_BRANDS["Mid-Range (5-6)"].keys()),
                "Budget": list(MOBILE_BRANDS["Budget (3-4)"].keys()),
            },
            "flat_brands": sorted(MOBILE_BRAND_SCORES.keys()),
            "ram": [2, 3, 4, 6, 8, 12, 16],
            "storage": [16, 32, 64, 128, 256, 512, 1024],
            "camera": [0, 12, 13, 16, 48, 50, 64, 108, 200],
            "battery": [0, 3000, 4000, 4500, 5000, 5500, 6000],
            "screen_size": [0, 5.5, 6.0, 6.1, 6.4, 6.5, 6.7, 6.8],
            "condition": list(CONDITION_SCORES.keys())[:9],
            "age_months": [0, 3, 6, 12, 18, 24, 36, 48],
        }
    
    elif category == "laptop":
        return {
            "brands": {
                "Premium": list(LAPTOP_BRANDS["Premium (9-10)"].keys()),
                "High-End": list(LAPTOP_BRANDS["High-End (7-8)"].keys()),
                "Mid-Range": list(LAPTOP_BRANDS["Mid-Range (5-6)"].keys()),
            },
            "flat_brands": sorted(LAPTOP_BRAND_SCORES.keys()),
            "processors": {
                "Intel": ["i3", "i5", "i7", "i9", "Celeron", "Pentium"],
                "AMD": ["Ryzen 3", "Ryzen 5", "Ryzen 7", "Ryzen 9"],
                "Apple": ["M1", "M2", "M3"],
            },
            "flat_processors": sorted(PROCESSOR_TIERS.keys()),
            "generation": [6, 7, 8, 9, 10, 11, 12, 13, 14],
            "ram": [4, 8, 16, 32, 64],
            "storage": [128, 256, 512, 1024, 2048],
            "gpu": list(GPU_TIERS.keys()),
            "screen_size": [11.6, 13.3, 14.0, 15.6, 17.3],
            "condition": list(CONDITION_SCORES.keys())[:9],
            "age_months": [0, 3, 6, 12, 18, 24, 36, 48, 60],
        }
    
    elif category == "furniture":
        return {
            "materials": {
                "Premium Wood": list(FURNITURE_MATERIALS["Premium Wood (8-10)"].keys()),
                "Standard Wood": list(FURNITURE_MATERIALS["Standard Wood (6-7)"].keys()),
                "Budget Materials": list(FURNITURE_MATERIALS["Budget Materials (3-5)"].keys()),
                "Metal & Others": list(FURNITURE_MATERIALS["Metal & Others (5-7)"].keys()),
            },
            "flat_materials": sorted(MATERIAL_QUALITY_SCORES.keys()),
            "seating_capacity": [0, 1, 2, 3, 4, 5, 6, 7, 8],
            "length_cm": [50, 80, 100, 120, 150, 180, 200, 250, 300],
            "width_cm": [40, 50, 60, 80, 100, 120, 150],
            "height_cm": [40, 50, 70, 85, 95, 100, 120, 150],
            "condition": list(CONDITION_SCORES.keys())[:9],
        }
    
    return {}
