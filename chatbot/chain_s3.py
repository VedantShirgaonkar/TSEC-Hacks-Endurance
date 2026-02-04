"""
RAG Chain for AWS Lambda - S3-based document retrieval without ChromaDB.
Uses in-memory embedding similarity search.
"""

from typing import List, Dict, Any, Optional
import os
import numpy as np

from langchain_openai import OpenAIEmbeddings
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

from chatbot.config import (
    GROQ_API_KEY,
    OPENAI_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K_DOCUMENTS,
    SYSTEM_PROMPT,
)


# S3 Configuration
S3_BUCKET = os.getenv("S3_DOCS_BUCKET", "endurance-docs-1770201946")
S3_DOCS_PREFIX = os.getenv("S3_DOCS_PREFIX", "documents/")


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


class S3RAGChain:
    """RAG Chain using S3 for document storage and in-memory similarity search."""
    
    def __init__(self):
        self.embeddings = None
        self.llm = None
        self.documents: List[Document] = []
        self.document_embeddings: List[np.ndarray] = []
        self._initialized = False
    
    def initialize(self, force_reload: bool = False):
        """Initialize the RAG chain components."""
        if self._initialized and not force_reload:
            return
        
        print("[S3-RAG] Initializing embeddings...")
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_key=OPENAI_API_KEY,
        )
        
        print("[S3-RAG] Initializing LLM (Groq)...")
        self.llm = ChatGroq(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            groq_api_key=GROQ_API_KEY,
        )
        
        # Load and process documents from S3
        print("[S3-RAG] Loading documents from S3...")
        self._load_documents_from_s3()
        
        # Create embeddings for all documents
        print("[S3-RAG] Creating embeddings for documents...")
        self._create_embeddings()
        
        self._initialized = True
        print("[S3-RAG] Initialization complete!")
    
    def _load_documents_from_s3(self):
        """Load documents from S3 bucket."""
        import boto3
        
        s3 = boto3.client('s3')
        
        try:
            # List objects in the bucket
            response = s3.list_objects_v2(
                Bucket=S3_BUCKET,
                Prefix=S3_DOCS_PREFIX
            )
            
            if 'Contents' not in response:
                print(f"[S3-RAG] No documents found in s3://{S3_BUCKET}/{S3_DOCS_PREFIX}")
                return
            
            raw_documents = []
            
            for obj in response['Contents']:
                key = obj['Key']
                if key.endswith('.md'):
                    print(f"[S3-RAG] Loading: {key}")
                    try:
                        file_response = s3.get_object(Bucket=S3_BUCKET, Key=key)
                        content = file_response['Body'].read().decode('utf-8')
                        
                        # Create Document object
                        doc = Document(
                            page_content=content,
                            metadata={
                                "source": key,
                                "source_name": key.split('/')[-1],
                            }
                        )
                        raw_documents.append(doc)
                    except Exception as e:
                        print(f"[S3-RAG] Error loading {key}: {e}")
            
            print(f"[S3-RAG] Loaded {len(raw_documents)} documents from S3")
            
            # Split documents into chunks
            self.documents = self._split_documents(raw_documents)
            
        except Exception as e:
            print(f"[S3-RAG] Error accessing S3: {e}")
            raise
    
    def _split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks."""
        print("[S3-RAG] Splitting documents into chunks...")
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n## ", "\n### ", "\n---", "\n\n", "\n", " "],
        )
        
        chunks = splitter.split_documents(documents)
        print(f"[S3-RAG] Created {len(chunks)} chunks")
        
        return chunks
    
    def _create_embeddings(self):
        """Create embeddings for all document chunks."""
        if not self.documents:
            return
        
        # Get embeddings for all documents
        texts = [doc.page_content for doc in self.documents]
        embeddings = self.embeddings.embed_documents(texts)
        self.document_embeddings = [np.array(emb) for emb in embeddings]
        
        print(f"[S3-RAG] Created {len(self.document_embeddings)} embeddings")
    
    def _get_similar_documents(self, query: str, k: int = None) -> List[tuple]:
        """Find k most similar documents to the query."""
        if k is None:
            k = TOP_K_DOCUMENTS
        
        # Get query embedding
        query_embedding = np.array(self.embeddings.embed_query(query))
        
        # Calculate similarities
        similarities = []
        for i, doc_embedding in enumerate(self.document_embeddings):
            sim = cosine_similarity(query_embedding, doc_embedding)
            similarities.append((sim, i))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        # Return top k
        return [(self.documents[idx], score) for score, idx in similarities[:k]]
    
    def _format_docs(self, docs: List[Document]) -> str:
        """Format documents for the prompt."""
        return "\n\n---\n\n".join(
            f"Source: {doc.metadata.get('source_name', 'Unknown')}\n{doc.page_content}"
            for doc in docs
        )
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Query the RAG chain.
        
        Returns:
            Dict with 'answer', 'source_documents', and metadata
        """
        if not self._initialized:
            self.initialize()
        
        # Get relevant documents with scores
        doc_score_pairs = self._get_similar_documents(question)
        docs = [doc for doc, score in doc_score_pairs]
        scores = [score for doc, score in doc_score_pairs]
        
        # Create prompt
        prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)
        
        # Create chain
        chain = prompt | self.llm | StrOutputParser()
        
        # Run chain
        context = self._format_docs(docs)
        answer = chain.invoke({"context": context, "question": question})
        
        # Format source documents for Endurance
        rag_documents = []
        for i, (doc, score) in enumerate(doc_score_pairs):
            rag_documents.append({
                "id": f"doc_{i}",
                "source": doc.metadata.get("source_name", f"document_{i}"),
                "content": doc.page_content,
                "similarity_score": score,
            })
        
        return {
            "answer": answer,
            "source_documents": docs,
            "rag_documents": rag_documents,
            "query": question,
        }
    
    def get_relevant_documents(self, question: str) -> List[Dict[str, Any]]:
        """Get relevant documents without generating an answer."""
        if not self._initialized:
            self.initialize()
        
        doc_score_pairs = self._get_similar_documents(question)
        
        return [
            {
                "id": f"doc_{i}",
                "source": doc.metadata.get("source_name", f"document_{i}"),
                "content": doc.page_content,
                "similarity_score": score,
            }
            for i, (doc, score) in enumerate(doc_score_pairs)
        ]


# Singleton instance
_rag_chain: Optional[S3RAGChain] = None


def get_rag_chain() -> S3RAGChain:
    """Get or create the S3 RAG chain singleton."""
    global _rag_chain
    if _rag_chain is None:
        _rag_chain = S3RAGChain()
        _rag_chain.initialize()
    return _rag_chain
