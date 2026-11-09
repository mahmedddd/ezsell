# EzSell: AI-Powered C2C Marketplace Platform

![Status](https://img.shields.io/badge/Status-Production_Ready-success)
![React](https://img.shields.io/badge/React-18.3-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5.8-blue)
![Vite](https://img.shields.io/badge/Vite-5.4-purple)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-teal)
![Python](https://img.shields.io/badge/Python-3.10%2B-yellow)
![XGBoost](https://img.shields.io/badge/XGBoost-3.0%2B-orange)
![PyTorch](https://img.shields.io/badge/PyTorch-2.9-red)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Data Engineering, Web Scraping, and Regex Cleaning Pipeline](#3-data-engineering-web-scraping-and-regex-cleaning-pipeline)
   - [3.1 Offline Marketplace Scrapers](#31-offline-marketplace-scrapers)
   - [3.2 Real-Time Specification and Live Market Scrapers](#32-real-time-specification-and-live-market-scrapers)
   - [3.3 Regex Feature Extraction and Data Cleaning Pipeline](#33-regex-feature-extraction-and-data-cleaning-pipeline)
4. [Machine Learning Price Prediction, Model Ensembler, and Model Blender](#4-machine-learning-price-prediction-model-ensembler-and-model-blender)
   - [4.1 Category-Specific Production Regression Models](#41-category-specific-production-regression-models)
   - [4.2 Multi-Algorithm Model Ensembler and Stacking Architecture](#42-multi-algorithm-model-ensembler-and-stacking-architecture)
   - [4.3 Real-Time Hybrid LLM-ML Model Blender](#43-real-time-hybrid-llm-ml-model-blender)
   - [4.4 Domain-Specific Structural Valuation Adjustments](#44-domain-specific-structural-valuation-adjustments)
5. [Automated Fraud Protection, Perceptual Hashing, and Scam Detection](#5-automated-fraud-protection-perceptual-hashing-and-scam-detection)
   - [5.1 Perceptual Difference Image Hasher (dHash)](#51-perceptual-difference-image-hasher-dhash)
   - [5.2 Global Content Deduplication Hasher (MD5)](#52-global-content-deduplication-hasher-md5)
   - [5.3 Zero-Shot Computer Vision Category Verification (CLIP)](#53-zero-shot-computer-vision-category-verification-clip)
   - [5.4 Keyboard Gibberish and Nonsense Text Detector](#54-keyboard-gibberish-and-nonsense-text-detector)
   - [5.5 Scam Keyword Scanner and Price Anomaly Gate](#55-scam-keyword-scanner-and-price-anomaly-gate)
6. [3D Augmented Reality (AR) Mobile Visualization and AI Mesh Generation](#6-3d-augmented-reality-ar-mobile-visualization-and-ai-mesh-generation)
   - [6.1 Mobile Native AR Execution (WebXR, ARCore, and ARKit)](#61-mobile-native-ar-execution-webxr-arcore-and-arkit)
   - [6.2 AI 2D-to-3D Mesh Reconstruction Pipeline (Tripo3D V2)](#62-ai-2d-to-3d-mesh-reconstruction-pipeline-tripo3d-v2)
   - [6.3 Procedural Real-Scale 3D GLB Generator and Room Object Detection](#63-procedural-real-scale-3d-glb-generator-and-room-object-detection)
7. [User Profile Creator, Behavioral Analytics, and Semantic Recommendation Engine](#7-user-profile-creator-behavioral-analytics-and-semantic-recommendation-engine)
   - [7.1 Automated User Profile Creator and Time-Decayed Interest Aggregation](#71-automated-user-profile-creator-and-time-decayed-interest-aggregation)
   - [7.2 NLP Keyword Extractor](#72-nlp-keyword-extractor)
   - [7.3 Hybrid Semantic Vector and Behavioral Recommendation Engine](#73-hybrid-semantic-vector-and-behavioral-recommendation-engine)
8. [Context-Aware In-App AI Consultant](#8-context-aware-in-app-ai-consultant)
9. [Authentication, Identity Management, and Core Platform Workflows](#9-authentication-identity-management-and-core-platform-workflows)
   - [9.1 Google OAuth 2.0 and OpenID Connect Integration](#91-google-oauth-20-and-openid-connect-integration)
   - [9.2 Local Authentication, SMTP Verification, and Access Control](#92-local-authentication-smtp-verification-and-access-control)
   - [9.3 Marketplace Operations and Admin Moderation](#93-marketplace-operations-and-admin-moderation)
10. [Database Schema Hierarchy](#10-database-schema-hierarchy)
11. [REST API Endpoint Hierarchy](#11-rest-api-endpoint-hierarchy)
12. [Technology Stack](#12-technology-stack)
13. [Repository Structure](#13-repository-structure)
14. [Installation, Model Training, and Deployment](#14-installation-model-training-and-deployment)
    - [14.1 Local Development Setup](#141-local-development-setup)
    - [14.2 Executing the Scraping and ML Training Pipelines](#142-executing-the-scraping-and-ml-training-pipelines)
    - [14.3 Production Deployment (AWS EC2 and Nginx)](#143-production-deployment-aws-ec2-and-nginx)
15. [License](#15-license)

---

## 1. Executive Summary

**EzSell** is a full-stack, AI-driven consumer-to-consumer (C2C) e-commerce marketplace engineered specifically for the Pakistani market, focusing on three core vertical categories: **Mobile Phones**, **Laptops**, and **Furniture**.

The platform addresses critical limitations in conventional classified portals by integrating automated data scraping, regular-expression feature extraction, ensemble and gradient-boosted price prediction models, real-time LLM market blending, multi-layer fraud and scam detection (combining OpenAI CLIP computer vision, perceptual difference hashing, and information-theoretic gibberish detection), behavioral user profiling with neural semantic recommendations, and mobile 3D Augmented Reality (AR) furniture visualization.

---

## 2. System Architecture

The application follows a decoupled, service-oriented architecture:

```
+-----------------------------------------------------------------------------------+
|                                  CLIENT LAYER                                     |
|  React 18 + TypeScript + Vite | Tailwind CSS + shadcn/ui | Three.js + WebXR       |
|  - Mobile WebAR (<model-viewer> / ARCore / ARKit) & Procedural GLB Engine         |
|  - TF.js COCO-SSD Room Detection | Interactive Analytics & Real-Time Chat         |
+-----------------------------------------+-----------------------------------------+
                                          | REST API / SSE (GZip Compressed)
                                          v
+-----------------------------------------------------------------------------------+
|                              APPLICATION API LAYER                                |
|                         FastAPI + Starlette + SQLAlchemy                          |
|  - JWT & Google OAuth 2.0 (Authlib) | Session & CORS Middleware                   |
|  - Listing Lifecycle, Admin Moderation Queue, Messaging, Notifications            |
+-------------------+-----------------------------+---------------------------------+
                    |                             |
                    v                             v
+-----------------------------------+   +-------------------------------------------+
|      LOCAL ML & VISION CORE       |   |       EXTERNAL AI & WEB SERVICES          |
|  - XGBoost / LightGBM / Sklearn   |   |  - Groq Cloud (LLaMA-3.3-70b & 3.1-8b)    |
|  - OpenAI CLIP (ViT-B/32)         |   |  - Tripo3D V2 API (2D-to-3D Mesh Gen)     |
|  - SentenceTransformers (MiniLM)  |   |  - Live GSMArena & DuckDuckGo Scrapers    |
|  - Perceptual Image Hash (dHash)  |   |  - Cloudinary Media CDN & Gmail SMTP      |
+-----------------------------------+   +-------------------------------------------+
```

---

## 3. Data Engineering, Web Scraping, and Regex Cleaning Pipeline

### 3.1 Offline Marketplace Scrapers
- **Dynamic DOM Extraction (`scrape_olx_selenium.py`, `scrape_olx_production.py`, `scrape_olx_robust.py`)**: Uses headless Chrome with Selenium WebDriver and explicit `WebDriverWait` conditions (`li[data-aut-id='itemBox']`) to scrape JavaScript-rendered listings across OLX Pakistan for mobile phones, laptops, and furniture.
- **Anti-Detection and Resilience**: Implements user-agent rotation, automation-flag suppression (`--disable-blink-features=AutomationControlled`), randomized request throttling, infinite-scroll pagination handling, and dataset deduplication (`scrapers/merge_*.py`).
- **Dataset Scale**: Extracted and consolidated over **11,900 raw marketplace records** (`5,963` mobiles, `4,320` laptops, and `1,691` furniture listings).

### 3.2 Real-Time Specification and Live Market Scrapers
- **GSMArena Direct Specification Scraper (`services/llm_pricing_service.py`)**: Queries GSMArena's quick-search endpoint via asynchronous `httpx`, validates model-number parity against the user's title, and parses HTML specification tables (`data-spec="internalmemory"`, color attributes) to populate exact official RAM, storage, and marketing color dropdown options without hallucination.
- **Parallel Live Market Price Aggregator**: Executes concurrent search queries via `DDGS` (DuckDuckGo Search) and raw HTML fallbacks across Pakistani used-goods portals (OLX Pakistan) and primary retail aggregators (PriceOye, PhoneWorld, HamariWeb, Symbios, NotebookCheck) to gather real-time used and new retail PKR prices.
- **Statistical IQR Filtering**: Applies a strict Interquartile Range fence ($[Q_1 - 1.2 \times \text{IQR}, Q_3 + 1.2 \times \text{IQR}]$) to live-scraped prices in real time, eliminating placeholder prices (e.g., Rs. 1) and fraudulent outliers prior to price estimation.

### 3.3 Regex Feature Extraction and Data Cleaning Pipeline
Raw marketplace text is unstructured and noisy. The preprocessing pipeline (`ml_pipeline/enhanced_preprocessor.py`, `ml_pipeline/advanced_feature_extractor.py`, `advanced_laptop_preprocessor.py`) transforms raw titles and descriptions into structured numerical vectors:

1. **Noise and Accessory Filtering**: Separates genuine product listings ("Featured") from accessory/cable clutter ("Delivery"), eliminating 50% of non-device noise in raw laptop scrapes.
2. **Multi-Pattern Regular Expression Extraction**:
   - **Memory (RAM)**: Matches variations including `(\d+)\s*gb\s*ram`, `ram[\s:]+(\d+)\s*gb`, `memory[\s:]+(\d+)\s*gb`, and context-window capacity patterns within the first 200 characters, constrained to valid hardware bounds (`2 GB - 128 GB` for laptops; `2 GB - 24 GB` for phones).
   - **Storage Capacity and Medium**: Extracts storage via `(\d+)\s*(tb|gb)\s+(ssd|hdd|nvme|m\.2)`, automatically normalizing terabytes to gigabytes ($\times 1024$) and assigning medium premium scores (`SSD/NVMe` vs. `HDD`).
   - **Processor Architecture**: Parses CPU brand (`Intel`, `AMD`, `Apple`), tier (`Core i3/i5/i7/i9`, `Ryzen 3/5/7/9`, `M1/M2/M3`), and generation (`1st - 14th Gen`) both from explicit strings (`11th gen`) and alphanumeric SKU suffixes (e.g., inferring `12th Gen` from `i7-1255U` or `11th Gen` from `1135G7`).
   - **Graphics Processing Unit (GPU)**: Categorizes integrated vs. dedicated GPUs (`NVIDIA RTX 20/30/40 series`, `GTX 10/16 series`, `AMD Radeon RX`), assigning hierarchical performance tiers (`Tier 1 - 10`) and extracting dedicated VRAM (`(\d+)\s*gb\s*(?:vram|gddr)`).
   - **Mobile Telemetry**: Extracts battery capacity (`(\d{4,5})\s*mah`), camera resolution (`(\d+)\s*(?:mp|megapixel)`), display diagonal (`(\d+\.?\d*)\s*(?:inch|\")`), display technology (`AMOLED`, `Super AMOLED`, `OLED`, `LCD`), cellular generation (`5G`, `4G`), and regulatory status (`PTA Approved` vs. `Non-PTA`).
   - **Furniture Attributes**: Extracts 3D spatial dimensions (`L x W x H` in cm/ft/inches), seating capacity (`(\d+)\s*seater`), furniture archetypes (`18` classes), and hierarchical material tiers (`Teak`, `Sheesham/Rosewood`, `Walnut/Oak`, `Solid Wood`, `Genuine Leather`, `Velvet`, `MDF/Plywood`, `Marble`, `Steel/Iron`).
3. **Outlier Removal and Imputation**: Applies Z-score filtering ($|z| < 2.5$), domain-specific price floor/ceiling truncation, median/mode group imputation, and `StandardScaler` / `RobustScaler` normalization.

---

## 4. Machine Learning Price Prediction, Model Ensembler, and Model Blender

### 4.1 Category-Specific Production Regression Models
EzSell deploys three specialized supervised regression models (`backend/models_enhanced/`) trained on engineered domain features:

| Category | Production Algorithm | Engineered Features | Dataset Records | Train $R^2$ | Test $R^2$ | MAE (PKR) | MAPE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Laptops** | `XGBRegressor` (Tuned) | 44 features | 1,269 (cleaned) | 97.78% | **92.29%** | Rs. 1,702 | 3.60% |
| **Mobiles** | `GradientBoostingRegressor` | 24 features | 5,963 | 99.99% | **99.94%** | Rs. 168 | 0.82% |
| **Furniture** | `GradientBoostingRegressor` | 24 features | 1,691 | 99.99% | **99.96%** | Rs. 109 | 1.78% |

- **Engineered Composite Features**: Includes non-linear hardware interaction terms such as `processor_gpu_combo` ($\text{CPU}_{\text{score}} \times \text{GPU}_{\text{score}}$), `ram_storage_ratio`, `total_specs_score`, `specs_per_age`, exponential age depreciation ($e^{-\lambda \cdot \text{age}}$), `capacity_score`, `tech_score`, and `price_per_volume`.
- **Hyperparameter Optimization**: Executed via 5-fold cross-validated `RandomizedSearchCV` (`ml_pipeline/trainer.py`), optimizing `max_depth=10`, `learning_rate=0.1`, `n_estimators=300`, `subsample=0.7`, and `colsample_bytree=0.7` with L1/L2 regularization to prevent overfitting.

### 4.2 Multi-Algorithm Model Ensembler and Stacking Architecture
In addition to single-estimator pipelines, the training suite (`trained_models/` and `ml_pipeline/trainer.py`) implements two ensemble architectures:
1. **Weighted Multi-Regressor Ensembler (`trained_models/*.pkl`)**: Combines predictions across four distinct gradient-boosted and bagging architectures using a static convex combination:
   $$\hat{y}_{\text{ensemble}} = 0.35 \cdot \hat{y}_{\text{XGB}} + 0.35 \cdot \hat{y}_{\text{LGBM}} + 0.15 \cdot \hat{y}_{\text{RF}} + 0.15 \cdot \hat{y}_{\text{GB}}$$
   - **XGBoost**: 2,000 estimators, `max_depth=12` (35% weight)
   - **LightGBM**: 2,000 estimators, `max_depth=15` (35% weight)
   - **Random Forest**: 500 estimators, `max_depth=20` (15% weight)
   - **Gradient Boosting**: 800 estimators, `max_depth=10` (15% weight)
2. **Stacked Generalization (`StackingRegressor`)**: Trains `RandomForestRegressor`, `XGBRegressor`, and `GradientBoostingRegressor` as base level-0 learners and feeds their out-of-fold predictions into a level-1 `Ridge` L2-regularized linear meta-learner via 5-fold cross-validation.

### 4.3 Real-Time Hybrid LLM-ML Model Blender
Static ML models trained on historical snapshots can lag behind rapid currency fluctuations or newly launched hardware (e.g., iPhone 16/17 series, RTX 40/50 series). EzSell solves this via a **Hybrid Model Blender** (`routers/predictions_advanced.py` & `services/llm_pricing_service.py`):

1. **Two-Stage Pre-Prediction Title Gate**:
   - **Stage 1 (Deterministic Rule Pre-Filter)**: Blocks generic/junk titles, numeric-only strings, and cross-brand model conflicts (`utils/title_validator.py` — e.g., rejecting "HP MacBook" or "Samsung iPhone") with zero API latency.
   - **Stage 2 (LLM Semantic Moderator)**: Validates category consistency and model specificity using `llama-3.3-70b-versatile` on Groq (with automatic multi-key rotation on HTTP 429 rate limits).
2. **Condition Depreciation Mapping**: Applies a condition multiplier $M_c \in [0.40, 0.95]$ derived from the seller's $1\text{-}10$ condition rating to the base ML/market reference prediction ($\hat{y}_{\text{ML\_adj}} = \hat{y}_{\text{ML}} \times M_c$).
3. **Confidence-Weighted Blending Formula**: Simultaneously, `LLMPricingService` scrapes live OLX used listings and retail prices, filters outliers via IQR, and prompts `llama-3.3-70b-versatile` to compute a condition-adjusted market appraisal ($\hat{y}_{\text{LLM}}$) with a grounding confidence score $c_{\text{LLM}} \in [0.0, 1.0]$. The final base valuation is blended dynamically:
   $$\hat{y}_{\text{blend}} = \begin{cases} 0.85 \cdot \hat{y}_{\text{LLM}} + 0.15 \cdot \hat{y}_{\text{ML\_adj}} & \text{if } \hat{y}_{\text{LLM}} > 0 \text{ and } c_{\text{LLM}} \ge 0.50 \\ 0.60 \cdot \hat{y}_{\text{LLM}} + 0.40 \cdot \hat{y}_{\text{ML\_adj}} & \text{if } \hat{y}_{\text{LLM}} > 0 \text{ and } c_{\text{LLM}} < 0.50 \\ \hat{y}_{\text{ML\_adj}} & \text{if LLM is offline or rate-limited} \end{cases}$$

### 4.4 Domain-Specific Structural Valuation Adjustments
Following the LLM-ML blend, deterministic structural modifiers are applied (`apply_mobile_price_adjustments`, `apply_laptop_price_adjustments`, `apply_furniture_price_adjustments`) to account for granular Pakistani market premiums:
- **Mobile**: PTA Approved (`+20%`), Non-PTA (`-15%`), 5G capability (`+12%`), AMOLED display (`+8%`), active warranty (`+10%`), original box (`+5%`), and RAM/storage tier deltas.
- **Furniture**: Material tier multipliers (Burma Teak `+40%`, Sheesham/Rosewood `+30%`, Walnut/Oak `+25%`, Genuine Leather `+25%`, Marble Top `+25%`, MDF/Plywood `-15%`, Plastic `-15%`), brand premiums (Interwood `+30%`, Habitt `+25%`, IKEA `+20%`, Chiniot Craftsmanship `+20%`), and subtype features (hydraulic bed storage `+15%`, orthopedic mattress `+35%`, sliding wardrobe doors `+15%`, motorized standing desk `+40%`).

---

## 5. Automated Fraud Protection, Perceptual Hashing, and Scam Detection

Every listing submitted to EzSell passes through `FraudProtectionService` (`backend/core/fraud_protection.py`) before publication:

### 5.1 Perceptual Difference Image Hasher (dHash)
To prevent scammers from reusing product photographs across multiple listings or accounts—even after resizing, aspect-ratio stretching, or JPEG recompression—EzSell computes a **64-bit Perceptual Difference Hash (`dHash`)** for every uploaded image:
1. Converts the image to 8-bit grayscale (`L` mode) using Pillow.
2. Downsamples the image to a $9 \times 8$ pixel grid via Lanczos resampling (`Image.Resampling.LANCZOS`).
3. Evaluates horizontal intensity gradients across each of the $8$ rows ($P[r, c] > P[r, c+1]$ for $c \in [0, 7]$), producing a 64-bit boolean array.
4. Packs the 64 bits into a zero-padded 16-character hexadecimal fingerprint (`image_hash`) and cross-checks it against all active, unsold listings globally.

### 5.2 Global Content Deduplication Hasher (MD5)
- Normalizes whitespace and case across the title and description, rounds the listing price to the nearest `Rs. 100` to defeat minor price-tweaking spam, and generates an MD5 digest (`listing_hash = MD5(clean_title | clean_desc | rounded_price)`).
- Any match on either `listing_hash` or `image_hash` flags the submission with `duplicate_detected` / `duplicate_image` and diverts it to the admin moderation queue.

### 5.3 Zero-Shot Computer Vision Category Verification (CLIP)
- **Model**: OpenAI `openai/clip-vit-base-patch32` (`CLIPModel` and `CLIPProcessor` via HuggingFace `transformers` and `PyTorch`).
- **Execution**: Resizes uploaded images to a $512 \times 512$ thumbnail and computes softmax cosine similarity logits across **42 global candidate text prompts** spanning mobiles, laptops, furniture, vehicles, home appliances, fashion, people, animals, screenshots, and empty backgrounds.
- **Verification Rules**:
  1. **Hard Blacklist Rejection**: Immediately rejects uploads whose top classification is `a person`, `an animal`, `text only`, `a screenshot`, `food`, or `empty space`.
  2. **Category Alignment**: Verifies that the highest-probability label maps to the expected category's valid descriptor dictionary (`VALID_DESCRIPTORS`) with softmax confidence $\ge 0.25$.
  3. **Mirror-Selfie Anti-Spoofing Heuristic**: For furniture listings classified as `a mirror`, inspects the secondary softmax probability of `a person`; if $P(\text{person}) > 0.15$, the image is rejected as a mirror selfie (`HTTP 400`).

### 5.4 Keyboard Gibberish and Nonsense Text Detector
To block keyboard-mashed descriptions and low-effort spam, `FraudProtectionService.is_nonsense()` evaluates four linguistic and information-theoretic heuristics:
1. **Shannon Entropy Analysis**: Computes character-level Shannon entropy:
   $$H(X) = -\sum_{x \in \Sigma} P(x) \log_2 P(x)$$
   Flags strings with $H(X) > 4.5$ bits/char (length $> 40$) as high-entropy random key-mashing, and strings with $H(X) < 1.5$ bits/char (length $> 20$) as low-diversity repetitive spam.
2. **Phonetic Consonant-to-Vowel Ratio**: Inspects alphabetic tokens $> 5$ characters. Flags unpronounceable consonant clusters ($0$ vowels with $> 6$ consonants, e.g., `vnlknvlkfv`) and abnormal vowel distributions ($\frac{V}{V + C} < 0.15$ for words $> 15$ characters, relaxed to $0.10$ when domain furniture keywords are present).
3. **Contiguous Run-Length Encoding**: Uses `itertools.groupby` to reject sequences containing $> 5$ identical consecutive characters (e.g., `aaaaaa` or `!!!!!!`).
4. **Lexical Bounds**: Rejects individual tokens exceeding $25$ characters or texts $> 15$ characters containing fewer than $4$ unique characters.

### 5.5 Scam Keyword Scanner and Price Anomaly Gate
- **Regex Scam Phrase Scanner**: Scans titles and descriptions against high-risk financial solicitation patterns (`advance\s*payment`, `pay\s*first`, `gift\s*card`, `whatsapp\s*only`, `contact\s*on\s*whatsapp`, `bank\s*transfer\s*first`, `courier\s*charges\s*needed`).
- **Price Anomaly Gate**: Compares the seller's asking price against the AI-predicted market value ($\hat{y}$). Listings priced below $0.40 \times \hat{y}$ (`price_suspiciously_low`) or above $3.00 \times \hat{y}$ (`price_suspiciously_high`) are automatically placed into `pending` administrative review.

---

## 6. 3D Augmented Reality (AR) Mobile Visualization and AI Mesh Generation

EzSell provides an end-to-end 3D and Augmented Reality visualization suite for furniture listings (`src/components/ar/WebARViewer.tsx`, `src/components/ar/FurnitureGLBGenerator.ts`, `src/components/AR3DViewer.tsx`, `backend/services/image_to_3d.py`, `backend/routers/ar_assets.py`).

### 6.1 Mobile Native AR Execution (WebXR, ARCore, and ARKit)
- **Runtime Hardware Capability Detection (`src/hooks/useARSupport.ts`)**: Probes `navigator.xr.isSessionSupported('immersive-ar')`, `DeviceMotionEvent` / `DeviceOrientationEvent` IMU availability, `navigator.mediaDevices.enumerateDevices()` video inputs, and user-agent platform signatures.
- **Cross-Platform AR Launch (`@google/model-viewer`)**:
  - **Android Devices**: Launches native surface-tracking AR via **WebXR** or **Google Scene Viewer (ARCore)** (`ar-modes="webxr scene-viewer quick-look"`).
  - **iOS Devices (iPhone/iPad)**: Launches native **Apple AR QuickLook (ARKit)** using `.usdz` or auto-converted `.glb` assets.
  - **Desktop / Non-AR Fallback**: Renders an interactive 3D WebGL viewport with orbit controls, auto-rotation, shadow intensity tuning, and real-time metric/imperial dimension pills (`cm` and `ft`).

### 6.2 AI 2D-to-3D Mesh Reconstruction Pipeline (Tripo3D V2)
- **Single-Image and Multi-View Reconstruction (`services/image_to_3d.py`)**: Sellers and admins can generate textured PBR 3D meshes (`.glb`) directly from 2D listing photographs via the **Tripo3D V2 OpenAPI** (`v2.0-20240919`).
  - Supports `image_to_model` for single photos and `multiview_to_model` (front, left, back, right tokens) when multiple listing images are available.
- **Asynchronous Polling and Local Caching (`routers/ar_assets.py`)**: Tracks generation progress asynchronously, downloads the resulting PBR `.glb` mesh upon completion, stores it under `/uploads/ar_models/` with immutable 1-year `Cache-Control` headers, and supports **Draco lossless mesh compression** (`gltf-transform`) to reduce mobile GPU memory bandwidth.

### 6.3 Procedural Real-Scale 3D GLB Generator and Room Object Detection
When an AI-generated `.glb` is not yet stored for a listing, the frontend synthesizes a bespoke, real-scale 3D model on the fly (`FurnitureGLBGenerator.ts`):
- **18 Parametric Multi-Component Archetypes**: Uses `Three.js` and `GLTFExporter` to construct detailed geometry (cushions, armrests, tapered legs, wardrobe doors, handles, bed headboards, bookshelves, drawers) across 18 distinct types (`sofa`, `armchair`, `chair`, `dining_chair`, `office_chair`, `table`, `dining_table`, `coffee_table`, `desk`, `bed`, `wardrobe`, `bookshelf`, `cabinet`, `dresser`, `ottoman`, `lamp`, `sideboard`, `generic`).
- **1:1 Real-World Metric Scaling**: Infers subtype dimensions (e.g., `3_door` vs. `6_door` wardrobe, `queen` vs. `king` bed, `5_seater` vs. `L_shape` sofa) and converts centimeters to meters ($\div 100$) so the exported `.glb` renders at exact 1:1 physical scale in the buyer's room.
- **Multi-Image Color Profile Extraction & TF.js Room Detection**: Samples dominant, secondary, and accent RGB color profiles from listing photos via HTML5 Canvas (`extractColorProfileMulti`) to texture the procedural mesh, and utilizes **TensorFlow.js (`@tensorflow-models/coco-ssd`)** alongside a 2D/3D room photo customizer (`AR3DViewer.tsx`) for in-room placement previews.

---

## 7. User Profile Creator, Behavioral Analytics, and Semantic Recommendation Engine

### 7.1 Automated User Profile Creator and Time-Decayed Interest Aggregation
The platform continuously constructs and updates a behavioral profile for every user (`backend/core/recommendation_engine.py`, `models/database.py`):
- **Interaction Tracking (`UserActivity`)**: Captures `view`, `search`, `click`, `favorite`, and `message` events along with session UUIDs (supporting anonymous-to-authenticated profile continuity) and listing dwell duration (`duration_seconds`).
- **Weighted Exponential Time-Decay Aggregation (`UserInterest`)**: Each interaction is weighted by intent intensity and decayed exponentially using a **7-day half-life**:
  $$W(a) = w_{\text{type}}(a) \times 0.5^{\frac{t_{\text{now}} - t_a}{7}}, \quad w_{\text{type}} = \{\text{view}: 1.0,\ \text{click}: 1.5,\ \text{search}: 2.0,\ \text{favorite}: 3.0,\ \text{message}: 5.0\}$$
- **Synthesized Profile Attributes**: Aggregates time-decayed frequency maps for `categories`, NLP-extracted `keywords`, preferred `brands`, observed `price_range_min` / `price_range_max`, and computes a **mean-pooled 384-dimensional user semantic embedding vector** ($\bar{\mathbf{e}}_{\text{user}} = \frac{1}{N}\sum_{i=1}^{N} \mathbf{e}_i$).

### 7.2 NLP Keyword Extractor
- Implemented in `backend/core/nlp_service.py` (`KeywordExtractor`).
- Normalizes text, strips 40+ domain stopwords, extracts domain-prioritized unigrams, bigrams, and trigrams (`IMPORTANT_TERMS`), identifies 23+ hardware/vehicle/furniture brand patterns via word-boundary regular expressions, infers product categories, and computes Jaccard keyword similarity ($J(A, B) = \frac{|A \cap B|}{|A \cup B|}$).

### 7.3 Hybrid Semantic Vector and Behavioral Recommendation Engine
- **Neural Semantic Embeddings (`backend/core/semantic_ai.py`)**: Uses `SentenceTransformer('all-MiniLM-L6-v2')` to encode listing titles, brands, categories, and descriptions into L2-normalized 384-dimensional dense vectors, with lazy database backfilling on interaction.
- **Hybrid Scoring Formula (`_calculate_hybrid_score`)**: Candidate listings (excluding user's own and previously viewed items) are ranked via:
  1. **Semantic Cosine Similarity (60% Weight)**: $\cos(\bar{\mathbf{e}}_{\text{user}}, \mathbf{e}_{\text{listing}})$ (falling back to weighted NLP keyword overlap if embeddings are absent).
  2. **Category Dominance & Affinity Boost (40% Weight + 0.15 Top-Category Bonus)**: Proportional to the user's historical category distribution.
  3. **Price Range & Brand Alignment (20% Combined Weight)**: Rewards listings within the user's historical price bounds and preferred brand set.
  4. **Recency Blending**: Blends relevance ($85\%$) with a recency decay bonus ($+0.30$ for $<24\text{h}$, $+0.20$ for $<3\text{d}$, $+0.10$ for $<7\text{d}$).
- **Endpoints & Analytics Dashboard (`routers/recommendations.py`, `routers/analytics.py`)**: Serves personalized feeds, a `70% Personalized / 30% Trending` "For You" feed, deep vector similar-item search (`get_similar_listings`), and a user analytics dashboard tracking engagement scores, activity timelines, and recommendation Click-Through Rates (CTR).

---

## 8. Context-Aware In-App AI Consultant

Implemented in `backend/services/chatbot_service.py` (`routers/chatbot.py`) and rendered via `src/components/EzSellChatbot.tsx`:
- **Model & Streaming**: Powered by **Groq `llama-3.1-8b-instant`**, delivering low-latency token streaming over Server-Sent Events (SSE).
- **Live CSV Market Price Intelligence (`get_olx_price_context`)**: When a user asks a pricing question, the service dynamically queries the local scraped OLX CSV datasets (`backend/scraped_data/`), filters matching rows by product keywords, applies $1.5 \times \text{IQR}$ outlier rejection, and injects live `Min | Median | Max` PKR market statistics directly into the LLM prompt context.
- **Capabilities & Strict Guardrails**: Provides page-aware navigation assistance, step-by-step ad posting instructions, explanations for fraud/moderation flags, mobile AR troubleshooting, and interior design style/color-palette recommendations (Scandinavian, Industrial, Bohemian, Modern Minimalist, Pakistani Traditional/Chinioti, Japandi), while strictly refusing off-topic non-marketplace queries.

---

## 9. Authentication, Identity Management, and Core Platform Workflows

### 9.1 Google OAuth 2.0 and OpenID Connect Integration
- **Implementation (`backend/routers/google_auth.py`, `src/pages/GoogleCallback.tsx`, `src/pages/CompleteProfile.tsx`)**: Built on `Authlib` (`Starlette` OAuth client) using Google's OpenID Connect discovery metadata (`https://accounts.google.com/.well-known/openid-configuration`) with `openid email profile` scopes and a 120-second clock-skew leeway.
- **Account Linking & Provisioning**:
  - Authenticates returning users via `google_id` (`sub` claim).
  - Automatically links existing local email/password accounts to Google OAuth upon verified email match and upgrades `is_verified` to `True`.
  - Provisions new accounts with collision-safe usernames, issues a signed JWT access token, and redirects new users (`is_new=1`) to `/complete-profile` to capture phone and location details.

### 9.2 Local Authentication, SMTP Verification, and Access Control
- **Cryptographic Security (`core/security.py`, `routers/users.py`)**: Passwords hashed via `bcrypt` with per-user salts; stateless session authentication via `HS256` JSON Web Tokens (`python-jose`).
- **Mandatory SMTP Email Verification (`core/email_service.py`)**: Generates a 6-digit numeric OTP with a strict **2-minute expiration window**, delivered via asynchronous Gmail SMTP (`aiosmtplib`) with multipart HTML/plain-text templates. Unverified accounts are blocked at the API level (`HTTP 403`) from creating listings.
- **Phone Normalization**: Deduplicates Pakistani mobile numbers across formats (`03XX-XXXXXXX`, `+92 3XX XXXXXXX`) by matching the canonical 10-digit subscriber suffix.

### 9.3 Marketplace Operations and Admin Moderation
- **Real-Time Buyer-Seller Messaging (`routers/messages.py`)**: Listing- contextualized chat threads with read receipts, user blocking (`BlockedUser`), and user reporting (`UserReport`).
- **Admin Moderation & Approvals (`routers/approvals.py`, `src/pages/AdminDashboard.tsx`)**: Dedicated administrative interface to inspect listings flagged by the fraud engine (`pending` status), review attached `fraud_flags`, and approve or reject submissions with automated user notification dispatch.
- **Support & Notifications (`routers/support.py`, `routers/notifications.py`)**: Bug/support ticket submission with screenshot attachments and real-time in-app notification feeds.

---

## 10. Database Schema Hierarchy

The relational schema (`backend/models/database.py`) is organized into five logical entity domains:

1. **Identity & Access Control**:
   - `User`: Core account entity (`username`, `email`, `hashed_password`, `google_id`, `auth_provider`, `is_verified`, `is_admin`, `phone`, `location`, `avatar_url`).
   - `EmailVerification` & `PasswordReset`: Time-bounded 6-digit OTP verification and password recovery records (`expires_at`, `is_used`).
   - `BlockedUser` & `UserReport`: Trust and safety relational tables for user blocking and misconduct reporting.
2. **Marketplace Listings & Category Specializations**:
   - `Listing`: Master product entity storing pricing (`price`, `predicted_price`, `confidence_score`), fraud metadata (`listing_hash`, `image_hash`, `fraud_flags`, `approval_status`, `rejection_reason`), 3D/AR metadata (`model_glb_url`, `model_usdz_url`, `dimensions_cm`, `polygon_count`), and neural vectors (`semantic_embedding`).
   - `MobilePhone`, `Laptop`, `Furniture`: Category-specific extension tables linked `1:1` via `listing_id`.
3. **Behavioral Profiling & Recommendation Telemetry**:
   - `UserActivity`: Granular interaction log (`search`, `view`, `click`, `favorite`, `message`, `session_id`, `keywords`, `semantic_embedding`, `duration_seconds`).
   - `UserInterest`: Aggregated, time-decayed user profile (`categories`, `keywords`, `brands`, `semantic_embedding`, `price_range_min`, `price_range_max`, `total_activities`).
   - `RecommendationHistory`: Impression and click-through tracking (`recommendation_type`, `score`, `shown_at`, `clicked`, `clicked_at`).
4. **Communications & Engagement**:
   - `Message`: Buyer-seller direct messages linked to users and listings.
   - `Favorite`: User-saved listing bookmarks.
   - `Notification`: System and moderation alerts.
   - `SupportTicket`: User-submitted bug reports and support inquiries.

---

## 11. REST API Endpoint Hierarchy

All endpoints are mounted under `/api/v1` (`backend/main.py`):

- **Authentication & Identity (`users.py`, `google_auth.py`)**:
  - `POST /send-verification-code`, `POST /verify-email-code`, `POST /register`, `POST /login`
  - `GET /auth/google/login`, `GET /auth/google/callback`, `GET /me`, `PUT /me`
- **Listings & Vision Validation (`listings.py`, `approvals.py`)**:
  - `GET /listings`, `POST /listings`, `GET /listings/{id}`, `PUT /listings/{id}`, `DELETE /listings/{id}`
  - `POST /validate-image` (real-time CLIP check), `GET /admin/pending-listings`, `POST /admin/approve-listing/{id}`, `POST /admin/reject-listing/{id}`
- **AI Price Prediction & Dynamic Specs (`predictions_advanced.py`)**:
  - `POST /predict-price`, `GET /dynamic-dropdowns`, `POST /validate-title`, `GET /dropdown-options/{category}`, `GET /model-info/{category}`
- **3D & Augmented Reality (`ar_assets.py`, `ar_customization_enhanced.py`)**:
  - `GET /products/{id}/assets`, `PUT /products/{id}/assets`, `POST /products/{id}/assets/upload-glb`
  - `POST /products/{id}/assets/generate-3d`, `GET /products/{id}/assets/generate-3d/{task_id}`, `POST /ar-preview`
- **Recommendations & Analytics (`recommendations.py`, `analytics.py`)**:
  - `POST /recommendations/track-activity`, `GET /recommendations/personalized`, `GET /recommendations/for-you`, `POST /recommendations/similar`, `GET /recommendations/trending`
  - `GET /analytics/dashboard`, `GET /analytics/interests`, `GET /analytics/activities`, `GET /analytics/recommendation-performance`
- **AI Consultant, Messaging & Support (`chatbot.py`, `messages.py`, `support.py`, `notifications.py`, `favorites.py`)**:
  - `POST /chatbot/stream` (SSE), `GET /messages`, `POST /messages`, `GET /favorites`, `POST /favorites`, `POST /support/tickets`, `GET /notifications`

---

## 12. Technology Stack

### 12.1 Frontend
- **Core Framework**: React 18.3, TypeScript 5.8, Vite 5.4 (SWC)
- **UI & Styling**: Tailwind CSS 3.4, shadcn/ui, Radix UI Primitives, Lucide Icons
- **3D & Augmented Reality**: Three.js (`0.182`), `@react-three/fiber`, `@react-three/drei`, `@google/model-viewer` (`4.1`), `GLTFExporter`
- **Client-Side Computer Vision**: TensorFlow.js (`@tensorflow/tfjs` `4.22`), COCO-SSD (`@tensorflow-models/coco-ssd` `2.2`)
- **State, Routing & Visualization**: TanStack React Query `5.90`, React Router DOM `6.30`, React Hook Form + Zod, Recharts `2.15`, Axios

### 12.2 Backend & API
- **Framework & Server**: FastAPI `0.110`, Uvicorn ASGI, Starlette Session & GZip Middleware
- **Database & ORM**: PostgreSQL (`psycopg2-binary`) / SQLite, SQLAlchemy `2.0`, Pydantic `2.6`
- **Authentication & Security**: Authlib `1.6` (Google OAuth 2.0 / OIDC), `python-jose` (JWT), `bcrypt` / `passlib`
- **Media & Communications**: Cloudinary SDK (cloud image storage with local static fallback), `aiosmtplib` (Async SMTP), `httpx`

### 12.3 Machine Learning, NLP, and Data Pipeline
- **Supervised Regression & Ensembles**: `xgboost` (`3.0+`), `lightgbm` (`4.0+`), `scikit-learn` (`RandomForestRegressor`, `GradientBoostingRegressor`, `StackingRegressor`, `Ridge`, `StandardScaler`, `RobustScaler`), `joblib`
- **Deep Learning & Computer Vision**: `torch` (`2.9` CPU), HuggingFace `transformers` (`openai/clip-vit-base-patch32`), `Pillow`, `opencv-python-headless`
- **Semantic Embeddings & LLM Inference**: `sentence-transformers` (`all-MiniLM-L6-v2`), Groq Cloud SDK (`llama-3.3-70b-versatile` & `llama-3.1-8b-instant`), Tripo3D V2 API
- **Web Scraping & Data Processing**: `selenium` (`4.39`), `beautifulsoup4`, `duckduckgo-search` (`ddgs`), `pandas`, `numpy`, `scipy`

---

## 13. Repository Structure

```text
ezsell/
├── backend/
│   ├── core/
│   │   ├── config.py                     # Environment & application settings
│   │   ├── email_service.py              # Async SMTP 6-digit OTP verification service
│   │   ├── fraud_protection.py           # CLIP vision, dHash, MD5, gibberish & scam engine
│   │   ├── nlp_service.py                # Regex/NLP keyword, brand & price extractor
│   │   ├── recommendation_engine.py      # Time-decayed user profiler & hybrid recommender
│   │   ├── security.py                   # JWT generation & OAuth2 password bearer
│   │   └── semantic_ai.py                # SentenceTransformer (all-MiniLM-L6-v2) service
│   ├── ml_pipeline/
│   │   ├── advanced_feature_extractor.py # Multi-pattern regex extractor for 3 categories
│   │   ├── enhanced_preprocessor.py      # Outlier removal, imputation & feature engineering
│   │   ├── preprocessor.py               # Base data cleaning utilities
│   │   └── trainer.py                    # Multi-model comparison, RandomizedSearchCV & Stacking
│   ├── models/
│   │   └── database.py                   # SQLAlchemy ORM schemas (User, Listing, Activity, etc.)
│   ├── models_enhanced/                  # Production XGBoost & GradientBoosting models + metadata
│   ├── trained_models/                   # 4-model weighted ensemble artifacts & scalers
│   ├── routers/
│   │   ├── analytics.py                  # User engagement & CTR analytics endpoints
│   │   ├── approvals.py                  # Admin moderation queue endpoints
│   │   ├── ar_assets.py                  # 3D GLB/USDZ upload & Tripo3D AI generation routes
│   │   ├── ar_customization_enhanced.py  # Room AR preview endpoints
│   │   ├── chatbot.py                    # SSE streaming AI assistant endpoint
│   │   ├── favorites.py                  # Saved listings management
│   │   ├── google_auth.py                # Google OAuth 2.0 login & callback handler
│   │   ├── listings.py                   # Listing CRUD with integrated fraud & CLIP checks
│   │   ├── messages.py                   # Buyer-seller real-time messaging
│   │   ├── notifications.py              # User notification feed
│   │   ├── predictions_advanced.py       # Hybrid LLM + ML price prediction & dynamic dropdowns
│   │   ├── recommendations.py            # Personalized, trending & similar-item feeds
│   │   ├── support.py                    # Support & bug ticket management
│   │   └── users.py                      # Local auth, OTP verification & profile management
│   ├── scrapers/                         # Dataset merging & deduplication scripts
│   ├── scraped_data/                     # Cleaned & merged OLX Pakistan CSV datasets
│   ├── schemas/                          # Pydantic request/response validation schemas
│   ├── services/
│   │   ├── chatbot_service.py            # Groq LLaMA-3.1-8b assistant + CSV IQR price lookup
│   │   ├── cloud_storage.py              # Cloudinary upload service with local fallback
│   │   ├── image_to_3d.py                # Tripo3D V2 API client & Draco GLB optimizer
│   │   └── llm_pricing_service.py        # GSMArena/DDG live scraper & LLaMA-3.3-70b appraiser
│   ├── utils/
│   │   └── title_validator.py            # Brand-model conflict & category rule validator
│   ├── advanced_laptop_preprocessor.py   # 44-feature laptop engineering pipeline
│   ├── scrape_olx_selenium.py            # Headless Selenium OLX Pakistan scraper
│   ├── main.py                           # FastAPI application entrypoint
│   └── requirements.txt                  # Python dependencies
├── src/
│   ├── components/
│   │   ├── ar/
│   │   │   ├── FurnitureGLBGenerator.ts  # 18-type real-scale Three.js procedural GLB builder
│   │   │   └── WebARViewer.tsx           # Mobile WebXR/ARCore/ARKit & TF.js room viewer
│   │   ├── AR3DViewer.tsx                # Interactive room photo canvas customizer
│   │   ├── CreateListingFormNew.tsx      # AI-assisted listing creation workflow
│   │   ├── EzSellChatbot.tsx             # Floating streaming AI consultant widget
│   │   └── Navigation.tsx                # Responsive application navigation
│   ├── hooks/
│   │   └── useARSupport.ts               # WebXR, ARCore, ARKit & sensor capability hook
│   ├── lib/
│   │   ├── api.ts                        # Axios API client & service wrappers
│   │   └── nlp.ts                        # Client-side NLP utilities
│   └── pages/                            # Application views (Home, Listings, ProductDetail,
│                                         # PricePrediction, Dashboard, AdminDashboard, etc.)
├── package.json                          # Node.js dependencies and build scripts
└── vite.config.ts                        # Vite bundler configuration
```

---

## 14. Installation, Model Training, and Deployment

### 14.1 Local Development Setup

#### Prerequisites
- **Node.js**: v18.0+ and `npm`
- **Python**: v3.10+ and `pip`
- **Database**: PostgreSQL (or SQLite for local development)

#### 1. Clone the Repository
```bash
git clone <REPOSITORY_URL>
cd ezsell
```

#### 2. Configure and Start the Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory with the following configuration:
```env
DATABASE_URL=sqlite:///./ezsell.db
SECRET_KEY=<YOUR_JWT_SECRET_KEY>
GOOGLE_CLIENT_ID=<YOUR_GOOGLE_OAUTH_CLIENT_ID>
GOOGLE_CLIENT_SECRET=<YOUR_GOOGLE_OAUTH_CLIENT_SECRET>
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
FRONTEND_URL=http://localhost:8080
GROQ_API_KEY=<YOUR_GROQ_PRICING_API_KEY>
GROQ_CHATBOT_API_KEY=<YOUR_GROQ_CHATBOT_API_KEY>
TRIPO_API_KEY=<YOUR_TRIPO3D_API_KEY>
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=<YOUR_SMTP_EMAIL>
SMTP_PASSWORD=<YOUR_SMTP_APP_PASSWORD>
SMTP_FROM_EMAIL=<YOUR_SMTP_EMAIL>
CLOUDINARY_CLOUD_NAME=<OPTIONAL_CLOUDINARY_NAME>
CLOUDINARY_API_KEY=<OPTIONAL_CLOUDINARY_KEY>
CLOUDINARY_API_SECRET=<OPTIONAL_CLOUDINARY_SECRET>
```

Launch the FastAPI server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
The interactive OpenAPI documentation is accessible at `http://localhost:8000/docs`.

#### 3. Configure and Start the Frontend
```bash
# From the repository root
npm install
npm run dev
```

### 14.2 Executing the Scraping and ML Training Pipelines

To scrape fresh marketplace data, run the regex preprocessing pipeline, and retrain the regression models:

```bash
cd backend

# 1. Scrape fresh listings from OLX Pakistan (requires Chrome & Selenium)
python scrape_olx_selenium.py --category laptop --max-pages 50

# 2. Run the advanced regex preprocessor and feature engineering pipeline
python advanced_laptop_preprocessor.py

# 3. Train and evaluate the category-specific models (Mobile, Laptop, Furniture)
python run_enhanced_pipeline.py --category all
python train_advanced_laptop_model.py

# 4. Verify model metrics and prediction integrity
python verify_models.py
```

### 14.3 Production Deployment (AWS EC2 and Nginx)

The production environment is architected for Ubuntu on AWS EC2 with Nginx acting as a reverse proxy for the compiled React static bundle (`dist/`) and the Uvicorn/FastAPI systemd service (`ezsell.service`).

To execute an automated production deployment and service reload:
```bash
bash backend/ec2_chatbot_setup.sh
```

This script pulls the latest repository state, installs updated Python and Node.js dependencies, compiles the production frontend bundle (`npm run build`), updates the `systemd` environment configuration, and restarts both `ezsell.service` and `nginx`.

---

## 15. License

This project is licensed under the MIT License.
