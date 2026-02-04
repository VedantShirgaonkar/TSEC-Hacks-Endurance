# Chatbot module
import os

# Use S3-based chain in AWS environment, local ChromaDB otherwise
if os.getenv("ENDURANCE_ENV", "local") == "aws":
    from chatbot.chain_s3 import get_rag_chain, S3RAGChain as RAGChain
else:
    from chatbot.chain import get_rag_chain, RAGChain

from chatbot.config import ENDURANCE_URL, DOCS_PATH

__all__ = ["get_rag_chain", "RAGChain", "ENDURANCE_URL", "DOCS_PATH"]
