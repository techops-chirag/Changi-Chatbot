from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
from app.config import Config
from app.scraper import WebScraper
from app.embeddings import EmbeddingsHandler
from app.chatbot import ChangiChatbot
import json
import os

app = FastAPI(
    title="Changi Airport Chatbot API",
    description="RAG-based chatbot for Changi Airport and Jewel Changi Airport information",
    version="1.0.0"
)

config = Config()
embeddings_handler = None
chatbot = None

class ChatRequest(BaseModel):
    query: str
    max_sources: Optional[int] = 5

class ChatResponse(BaseModel):
    response: str
    sources: List[Dict]
    context_used: int

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    global embeddings_handler, chatbot
    embeddings_handler = EmbeddingsHandler(config)
    chatbot = ChangiChatbot(config, embeddings_handler)
    if not os.path.exists("data/processed.json"):
        print("No processed data found. Starting data collection...")
        await initialize_data()

async def initialize_data():
    """Scrape websites and process data"""
    scraper = WebScraper()
    documents = scraper.scrape_websites(config.WEBSITES)
    os.makedirs("data", exist_ok=True)
    with open("data/scraped_data.json", "w") as f:
        json.dump(documents, f, indent=2)
    embeddings_handler.process_and_store_documents(documents)
    with open("data/processed.json", "w") as f:
        json.dump({"status": "processed", "documents": len(documents)}, f)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint"""
    try:
        if not chatbot:
            raise HTTPException(status_code=500, detail="Chatbot not initialized")
        result = chatbot.generate_response(request.query)
        # Use .get with defaults to defend against missing keys
        return ChatResponse(
            response=result.get('response', ''),
            sources=result.get('sources', [])[:request.max_sources],
            context_used=result.get('context_used', 0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Changi Chatbot API"}

@app.post("/refresh-data")
async def refresh_data(background_tasks: BackgroundTasks):
    background_tasks.add_task(initialize_data)
    return {"message": "Data refresh started in background"}

@app.get("/stats")
async def get_stats():
    if embeddings_handler:
        index_stats = embeddings_handler.index.describe_index_stats()
        return {
            "total_vectors": index_stats.total_vector_count,
            "index_fullness": index_stats.index_fullness,
            "dimension": index_stats.dimension
        }
    return {"message": "System not initialized"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
