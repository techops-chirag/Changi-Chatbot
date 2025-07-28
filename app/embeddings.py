import pinecone
from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
import hashlib
from sentence_transformers import SentenceTransformer

class EmbeddingsHandler:
    def __init__(self, config):
        self.config = config
        
        # Initialize local embedding model
        print("Loading local embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight, free model
        
        try:
            # NEW Pinecone API initialization
            self.pc = Pinecone(api_key=config.PINECONE_API_KEY)
            
            # Get list of existing indexes
            existing_indexes = self.pc.list_indexes().names()
            print(f"Existing indexes: {existing_indexes}")
            
            # Create index if it doesn't exist (with correct dimensions for all-MiniLM-L6-v2)
            if config.PINECONE_INDEX_NAME not in existing_indexes:
                print(f"Creating new index: {config.PINECONE_INDEX_NAME}")
                self.pc.create_index(
                    name=config.PINECONE_INDEX_NAME,
                    dimension=384,  # all-MiniLM-L6-v2 dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                print("Index created successfully!")
            else:
                print(f"Using existing index: {config.PINECONE_INDEX_NAME}")
            
            # Connect to the index
            self.index = self.pc.Index(config.PINECONE_INDEX_NAME)
            print("Successfully connected to Pinecone!")
            
        except Exception as e:
            print(f"Pinecone connection failed: {e}")
            print("Running in offline mode")
            self.index = None
        
        # Text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP
        )
    
    def create_embeddings(self, text: str) -> List[float]:
        """Create embeddings using local model"""
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            print(f"Error creating embedding: {e}")
            return None
    
    def process_and_store_documents(self, documents: List[Dict]):
        """Process documents and store in vector database"""
        if not self.index:
            print("No Pinecone connection - skipping document storage")
            return
            
        vectors_to_upsert = []
        
        for doc in documents:
            # Split document into chunks
            chunks = self.text_splitter.split_text(doc['content'])
            
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) < 50:  # Skip very short chunks
                    continue
                
                # Create embedding
                embedding = self.create_embeddings(chunk)
                if embedding is None:
                    continue
                
                # Create unique ID
                doc_id = hashlib.md5(f"{doc['url']}_{i}".encode()).hexdigest()
                
                # Prepare metadata
                metadata = {
                    'text': chunk,
                    'url': doc['url'],
                    'title': doc['title'],
                    'chunk_index': i
                }
                
                vectors_to_upsert.append({
                    'id': doc_id,
                    'values': embedding,  # Now we have actual float vectors
                    'metadata': metadata
                })
        
        # Batch upsert to Pinecone
        batch_size = 100
        for i in range(0, len(vectors_to_upsert), batch_size):
            batch = vectors_to_upsert[i:i + batch_size]
            try:
                self.index.upsert(vectors=batch)
                print(f"Successfully uploaded batch {i//batch_size + 1}")
            except Exception as e:
                print(f"Error uploading batch: {e}")
        
        print(f"Stored {len(vectors_to_upsert)} chunks in vector database")
    
    def search_similar(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for similar content"""
        if not self.index:
            print("No Pinecone connection - returning empty results")
            return []
            
        try:
            # Create embedding for the query
            query_embedding = self.create_embeddings(query)
            if query_embedding is None:
                return []
            
            # Query with actual vector
            results = self.index.query(
                vector=query_embedding,  # Now we pass actual float vectors
                top_k=top_k,
                include_metadata=True
            )
            
            return [
                {
                    'text': match['metadata']['text'],
                    'url': match['metadata']['url'],
                    'title': match['metadata']['title'],
                    'score': match['score']
                }
                for match in results['matches']
            ]
        except Exception as e:
            print(f"Error searching: {e}")
            return []
