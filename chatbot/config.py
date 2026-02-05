"""
Chatbot Configuration - Environment-aware settings.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Environment: "local" or "aws"
ENV = os.getenv("ENDURANCE_ENV", "local")

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate keys
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment")

# Paths
BASE_DIR = Path(__file__).parent.parent
CHATBOT_DIR = Path(__file__).parent

if ENV == "local":
    # Local configuration
    VECTOR_STORE_TYPE = "chromadb"
    DOCS_PATH = CHATBOT_DIR / "rag_docs"
    VECTOR_STORE_PATH = CHATBOT_DIR / "vector_store"
    ENDURANCE_URL = "http://localhost:8000"
else:
    # AWS configuration (for future use)
    VECTOR_STORE_TYPE = "faiss_s3"
    DOCS_PATH = os.getenv("S3_DOCS_PATH", "s3://endurance-docs/")
    VECTOR_STORE_PATH = os.getenv("S3_VECTOR_PATH", "s3://endurance-vectors/")
    ENDURANCE_URL = os.getenv("ENDURANCE_LAMBDA_URL", "")

# LLM Settings
LLM_MODEL = "llama-3.3-70b-versatile"  # Groq model
LLM_TEMPERATURE = 0.1  # Low temperature for factual responses
LLM_MAX_TOKENS = 1024

# Reasoning Model Settings (for chain-of-thought analysis)
REASONING_MODEL = "openai/gpt-oss-120b"  # Model with reasoning capability
REASONING_EFFORT = os.getenv("REASONING_EFFORT", "medium")  # low, medium, high

# Embedding Settings
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# RAG Settings
TOP_K_DOCUMENTS = 4  # Number of similar documents to retrieve

# System Prompt for RTI Assistant
SYSTEM_PROMPT = """You are an RTI (Right to Information) Assistant for the Department of Information Technology, Government of India.

Your role is to:
1. Answer queries based ONLY on the provided official documents
2. Cite specific sources (document names, section numbers, page numbers) for all information
3. Provide exact figures and data from the documents - do NOT approximate or round numbers
4. If information is not available in the documents, clearly state: "This information is not available in the provided documents"
5. Be formal, accurate, and helpful

Important guidelines:
- Never invent or hallucinate information
- Always cite the source document for each piece of information
- Use exact numbers from the documents
- If asked about something not in the documents, say so clearly
- Provide the relevant section/table reference when available

Context from official documents:
{context}

User Query: {question}

Provide a detailed, accurate response with proper citations:"""

print(f"[Config] Environment: {ENV}")
print(f"[Config] Documents Path: {DOCS_PATH}")
print(f"[Config] Endurance URL: {ENDURANCE_URL}")
