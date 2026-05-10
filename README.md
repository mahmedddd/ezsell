# EzSell 🛒🤖

![EzSell Platform](https://img.shields.io/badge/Status-Active-success)
![React](https://img.shields.io/badge/React-18.x-blue)
![Vite](https://img.shields.io/badge/Vite-5.x-purple)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-teal)
![Python](https://img.shields.io/badge/Python-3.10+-yellow)

**EzSell** is a next-generation, AI-powered online marketplace exclusively designed for buying and selling Mobiles, Laptops, and Furniture in Pakistan. It integrates advanced machine learning and AI features to provide a highly secure, intuitive, and modern user experience.

---

## 🌟 Key Features

### 🤖 Intelligent In-App AI Assistant
A built-in, context-aware chatbot (powered by **Groq LLaMA-3.1-8b**) that acts as a 24/7 personal consultant:
- Explains the fraud system and helps users fix rejected listings.
- Analyzes live scraped CSV data to provide used market price ranges (Min/Median/Max) vs. new retail prices.
- Suggests furniture design styles, room color combinations, and AR viewing instructions.
- Guides users through navigation and troubleshooting seamlessly via a futuristic glassmorphic UI widget.

### 🛡️ Smart Fraud Protection & Validation System
Listings undergo rigorous automated screening before going live:
- **Duplicate Detection**: Advanced content hashing prevents spam and identical listings.
- **AI Vision Checks**: Uses CLIP models to verify that uploaded images actually match the selected category (no laptops in the mobiles section!).
- **Scam Keyword Detection**: Automatically flags suspicious descriptions ("advance payment", "gift card", etc.).
- **Price Anomaly Detection**: Prevents extreme low-balling or unrealistic pricing by comparing the listing price to AI predictions.

### 💰 AI Price Prediction Engine
- Real-time market value estimation for devices and furniture based on scraped data (OLX Pakistan) and ML benchmarks.
- Helps sellers price their items competitively and buyers know if they're getting a fair deal.

### 🛋️ Augmented Reality (AR) / 3D Viewer
- View furniture directly in your physical space!
- Integrated with 2D-to-3D generation pipelines to allow buyers to accurately visualize furniture scale and style before purchasing.

---

## 🛠️ Technology Stack

**Frontend:**
- [React](https://reactjs.org/) + [TypeScript](https://www.typescriptlang.org/)
- [Vite](https://vitejs.dev/) (Build Tool & Dev Server)
- [Tailwind CSS](https://tailwindcss.com/) & [shadcn/ui](https://ui.shadcn.com/) (Styling & Components)

**Backend:**
- [FastAPI](https://fastapi.tiangolo.com/) (High-performance Python API)
- [PostgreSQL](https://www.postgresql.org/) + [SQLAlchemy](https://www.sqlalchemy.org/) (Database & ORM)
- [Groq API](https://groq.com/) (LLaMA-3.1-8b for the Chatbot and validation services)
- `sentence-transformers`, `scikit-learn` (Local Semantic Embeddings & ML)

---

## 🚀 Getting Started (Local Development)

### 1. Clone the repository
```bash
git clone <YOUR_GIT_URL>
cd ezsell
```

### 2. Frontend Setup
Make sure you have [Node.js](https://nodejs.org/) installed (v18+ recommended).
```bash
# Install dependencies
npm install

# Start the development server
npm run dev
```

### 3. Backend Setup
Make sure you have [Python 3.10+](https://www.python.org/) installed.
```bash
# Navigate to backend directory
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Configure Environment Variables
# Copy .env.example to .env and fill in your keys (Database, Groq, JWT Secret, etc.)
cp .env.example .env

# Start the FastAPI server
uvicorn main:app --reload
```

---

## 🌍 Deployment (EC2 / Production)

The application is configured to run on an Ubuntu EC2 instance utilizing Nginx as a reverse proxy for both the compiled React frontend and the FastAPI backend service.

### Quick Deploy (Backend Services)
To deploy backend changes, run the included setup script:
```bash
bash backend/ec2_chatbot_setup.sh
```
This script automates pulling code, upgrading packages, building the frontend, restarting Nginx, and reloading the `ezsell.service` daemon.

*(Note: Ensure your `.env` secrets, especially `GROQ_CHATBOT_API_KEY`, are properly set on your EC2 instance since they are excluded from version control.)*

---

## 🤝 Contributing
Contributions are welcome! Please ensure you test locally before pushing changes to the main branch. Make sure not to commit any `.env` files or API keys.

## 📄 License
This project is licensed under the MIT License.
