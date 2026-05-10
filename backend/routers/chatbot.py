"""
EzSell AI Chatbot Router
Endpoints:
  POST /api/v1/chatbot/chat         — SSE streaming chat
  GET  /api/v1/chatbot/suggestions  — context-aware quick-reply chips
"""
import json
from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()


# ─── Request / Response Schemas ────────────────────────────────────────────────
class ChatMessage(BaseModel):
    role: str        # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    current_page: Optional[str] = ""
    # Hint for OLX price lookups — pass category when user asks price questions
    category_hint: Optional[str] = ""       # "mobile" | "laptop" | "furniture"
    search_keywords: Optional[List[str]] = []  # e.g. ["iPhone", "14 Pro"]


# ─── Keyword triggers that warrant injecting OLX price data ────────────────────
PRICE_KEYWORDS = [
    "price", "cost", "rate", "kitna", "how much", "pkr", "rupees",
    "worth", "value", "market", "olx", "used", "second hand", "sasta",
    "budget", "expensive", "cheap", "affordable", "resale",
]


# ─── Main Chat Endpoint ─────────────────────────────────────────────────────────
@router.post("/chat")
async def chat(request: ChatRequest):
    from services.chatbot_service import get_chatbot_service, get_olx_price_context

    service = get_chatbot_service()

    # Build message list for Groq
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    # Inject OLX price context when user is asking about prices
    price_context = ""
    if request.messages:
        last_msg = request.messages[-1].content.lower()
        if any(kw in last_msg for kw in PRICE_KEYWORDS) and request.category_hint:
            price_context = await get_olx_price_context(
                category=request.category_hint,
                keywords=request.search_keywords or [],
            )

    async def event_stream():
        try:
            async for token in service.stream_response(
                messages=messages,
                current_page=request.current_page or "",
                price_context=price_context,
            ):
                yield f"data: {json.dumps({'token': token})}\n\n"

            # Signal completion to the frontend
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",   # critical for Nginx/proxy streaming
        },
    )


# ─── Context-Aware Quick Suggestions ───────────────────────────────────────────
SUGGESTIONS_MAP = {
    "home": [
        "How do I post an ad? 📋",
        "Check mobile prices 📱",
        "How does fraud detection work? 🛡️",
    ],
    "listings": [
        "How are prices determined? 💰",
        "What makes a great listing? ✅",
        "How to filter by price range? 🔍",
    ],
    "product": [
        "How do I view this in AR? 🪑",
        "Is this price fair? 💸",
        "How do I message the seller? 💬",
    ],
    "create-listing": [
        "Why might my listing go to review? 🔍",
        "What photos should I upload? 📷",
        "How is the AI price suggested? 🤖",
    ],
    "dashboard": [
        "Why is my listing under review? 🕐",
        "How to edit my listing? ✏️",
        "How do I mark a listing as sold? ✔️",
    ],
    "messages": [
        "How do I report a scammer? 🚨",
        "Message not sending? 💬",
        "Can I share my phone number? 📞",
    ],
    "profile": [
        "How to verify my account? ✅",
        "How do I improve my rating? ⭐",
        "How to edit my profile? 👤",
    ],
    "favorites": [
        "How do I contact a seller? 💬",
        "How to remove from favorites? 🗑️",
        "Check if price is fair? 💰",
    ],
    "default": [
        "How do I post an ad? 📋",
        "Check prices 💰",
        "AR viewing help 🪑",
        "Fraud system explained 🛡️",
    ],
}


@router.get("/suggestions")
async def get_suggestions(page: str = "home"):
    """Return 3 context-aware quick-reply chip suggestions for the current page."""
    page_lower = page.lower()
    matched_key = "default"
    for key in SUGGESTIONS_MAP:
        if key in page_lower:
            matched_key = key
            break
    return {"suggestions": SUGGESTIONS_MAP[matched_key]}
