import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Updated API keys with your values
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCNKTRAE1Zdza40sKB5hQevxJ8fE0nPATw")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "pcsk_4m8GRk_6GveqsGiicKDp3dSBzRtE1bhiVkCAxtpuU5bqwJMrYvybjKdr5C1ErKqLc7XqHq")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
    PINECONE_HOST = "controller.us-east-1.pinecone.io" 
    PINECONE_INDEX_NAME = "changi-chatbot"
    
    # Websites to scrape
    WEBSITES = [
        "https://www.changiairport.com",
        "https://www.jewelchangiairport.com"
    ]
    
    # Updated model configurations for Microsoft multilingual-e5-large
    EMBEDDING_MODEL = "multilingual-e5-large"  # Changed from OpenAI to Microsoft model
    LLM_MODEL = "gemini-1.5-flash"  # Changed to Gemini
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
