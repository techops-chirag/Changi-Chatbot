import google.generativeai as genai
from typing import List, Dict

class ChangiChatbot:
    def __init__(self, config, embeddings_handler):
        self.config = config
        self.embeddings_handler = embeddings_handler
        # Configure Gemini API
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(config.LLM_MODEL)
        self.system_prompt = """
        You are a helpful assistant for Changi Airport and Jewel Changi Airport.
        You provide accurate information about flights, facilities, shopping, dining, and services.
        Use the provided context to answer questions. If the information is not in the context,
        say so clearly. Always be friendly and helpful.
        Format your responses in a clear, organized manner with relevant details.
        """

    def generate_response(self, query: str) -> Dict:
        """Generate response using RAG with Gemini"""
        # Get relevant context
        context_docs = self.embeddings_handler.search_similar(query, top_k=5)
        if not context_docs:
            return {
                'response': "I don't have specific information about that topic. Please try rephrasing your question or contact Changi Airport directly.",
                'sources': [],
                'context_used': 0   # <-- always include this key!
            }

        # Prepare context
        context = "\n\n".join([
            f"Source: {doc['title']} ({doc['url']})\nContent: {doc['text']}"
            for doc in context_docs
        ])

        # Create prompt
        full_prompt = f"""
        {self.system_prompt}
        Context from Changi Airport and Jewel Changi Airport websites:
        {context}
        Question: {query}
        Please provide a helpful answer based on the context above. If the context doesn't contain relevant information, please say so.
        """

        try:
            # Generate response with Gemini
            response = self.model.generate_content(full_prompt)
            return {
                'response': response.text,
                'sources': [
                    {'title': doc['title'], 'url': doc['url'], 'relevance_score': doc['score']}
                    for doc in context_docs
                ],
                'context_used': len(context_docs)
            }
        except Exception as e:
            return {
                'response': f"Sorry, I encountered an error processing your request: {str(e)}",
                'sources': [],
                'context_used': 0
            }
