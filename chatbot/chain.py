"""
RAG Chain - LangChain RAG pipeline with Groq LLM and OpenAI embeddings.
Updated for LangChain v0.3+
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_groq import ChatGroq
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document

from chatbot.config import (
    GROQ_API_KEY,
    OPENAI_API_KEY,
    DOCS_PATH,
    VECTOR_STORE_PATH,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K_DOCUMENTS,
    SYSTEM_PROMPT,
    REASONING_MODEL,
    REASONING_EFFORT,
)


class RAGChain:
    """RAG Chain for RTI document Q&A."""
    
    def __init__(self):
        self.embeddings = None
        self.llm = None
        self.vectorstore = None
        self.retriever = None
        self._initialized = False
    
    def initialize(self, force_reload: bool = False):
        """Initialize the RAG chain components."""
        if self._initialized and not force_reload:
            return
        
        print("[RAG] Initializing embeddings...")
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_key=OPENAI_API_KEY,
        )
        
        print("[RAG] Initializing LLM (Groq)...")
        self.llm = ChatGroq(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            groq_api_key=GROQ_API_KEY,
        )
        
        # Check if vector store exists
        vector_store_exists = VECTOR_STORE_PATH.exists() and any(VECTOR_STORE_PATH.iterdir())
        
        if vector_store_exists and not force_reload:
            print("[RAG] Loading existing vector store...")
            self.vectorstore = Chroma(
                persist_directory=str(VECTOR_STORE_PATH),
                embedding_function=self.embeddings,
            )
        else:
            print("[RAG] Creating new vector store from documents...")
            self._create_vectorstore()
        
        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": TOP_K_DOCUMENTS},
        )
        
        self._initialized = True
        print("[RAG] Initialization complete!")
    
    def _load_documents(self) -> List[Document]:
        """Load documents from the docs directory."""
        print(f"[RAG] Loading documents from {DOCS_PATH}...")
        
        # Load markdown files
        loader = DirectoryLoader(
            str(DOCS_PATH),
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
        )
        
        documents = loader.load()
        print(f"[RAG] Loaded {len(documents)} documents")
        
        # Add source metadata
        for doc in documents:
            source_path = Path(doc.metadata.get("source", ""))
            doc.metadata["source_name"] = source_path.name
        
        return documents
    
    def _split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks."""
        print("[RAG] Splitting documents into chunks...")
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n## ", "\n### ", "\n---", "\n\n", "\n", " "],
        )
        
        chunks = splitter.split_documents(documents)
        print(f"[RAG] Created {len(chunks)} chunks")
        
        return chunks
    
    def _create_vectorstore(self):
        """Create and persist the vector store."""
        documents = self._load_documents()
        chunks = self._split_documents(documents)
        
        print("[RAG] Creating embeddings and vector store...")
        
        # Create vector store
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=str(VECTOR_STORE_PATH),
        )
        
        print(f"[RAG] Vector store created at {VECTOR_STORE_PATH}")
    
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
        
        # Get relevant documents
        docs = self.retriever.invoke(question)
        
        # Create prompt
        prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)
        
        # Create chain
        chain = prompt | self.llm | StrOutputParser()
        
        # Run chain
        context = self._format_docs(docs)
        answer = chain.invoke({"context": context, "question": question})
        
        # Format source documents for Endurance
        rag_documents = []
        for i, doc in enumerate(docs):
            rag_documents.append({
                "id": f"doc_{i}",
                "source": doc.metadata.get("source_name", f"document_{i}"),
                "content": doc.page_content,
                "similarity_score": 0.9 - (i * 0.1),  # Approximate score
            })
        
        return {
            "answer": answer,
            "source_documents": docs,
            "rag_documents": rag_documents,
            "query": question,
            "model_used": LLM_MODEL,
            "reasoning_trace": None,
        }
    
    def query_with_reasoning(self, question: str, reasoning_effort: str = None) -> Dict[str, Any]:
        """
        Query the RAG chain with reasoning trace enabled.
        Uses Groq SDK directly to get structured reasoning output.
        """
        from groq import Groq
        import time
        
        if not self._initialized:
            self.initialize()
        
        effort = reasoning_effort or REASONING_EFFORT
        
        # Get relevant documents
        docs = self.retriever.invoke(question)
        
        # Format context
        context = self._format_docs(docs)
        
        # Build the full prompt
        full_prompt = SYSTEM_PROMPT.format(context=context, question=question)
        
        # Use Groq SDK directly for reasoning
        client = Groq(api_key=GROQ_API_KEY)
        
        start_time = time.time()
        
        try:
            response = client.chat.completions.create(
                model=REASONING_MODEL,
                messages=[
                    {"role": "user", "content": full_prompt},
                ],
                max_tokens=LLM_MAX_TOKENS,
                temperature=LLM_TEMPERATURE,
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Extract answer and reasoning
            message = response.choices[0].message
            answer = message.content
            
            # Extract reasoning trace
            reasoning_trace = None
            if hasattr(message, 'reasoning') and message.reasoning:
                reasoning_trace = message.reasoning
            elif hasattr(message, 'reasoning_content') and message.reasoning_content:
                reasoning_trace = message.reasoning_content
            
            tokens_used = response.usage.total_tokens if response.usage else None
            
        except Exception as e:
            print(f"[RAG] Reasoning query error: {e}")
            return self.query(question)
        
        # Format source documents for Endurance
        rag_documents = []
        for i, doc in enumerate(docs):
            rag_documents.append({
                "id": f"doc_{i}",
                "source": doc.metadata.get("source_name", f"document_{i}"),
                "content": doc.page_content,
                "similarity_score": 0.9 - (i * 0.1),
            })
        
        return {
            "answer": answer,
            "reasoning_trace": reasoning_trace,
            "source_documents": docs,
            "rag_documents": rag_documents,
            "query": question,
            "model_used": REASONING_MODEL,
            "metadata": {
                "reasoning_effort": effort,
                "tokens_used": tokens_used,
                "latency_ms": latency_ms,
            }
        }
    
    def get_relevant_documents(self, question: str) -> List[Dict[str, Any]]:
        """Get relevant documents without generating an answer."""
        if not self._initialized:
            self.initialize()
        
        docs = self.retriever.invoke(question)
        
        return [
            {
                "id": f"doc_{i}",
                "source": doc.metadata.get("source_name", f"document_{i}"),
                "content": doc.page_content,
            }
            for i, doc in enumerate(docs)
        ]


# Singleton instance
_rag_chain: Optional[RAGChain] = None


def get_rag_chain() -> RAGChain:
    """Get or create the RAG chain singleton."""
    global _rag_chain
    if _rag_chain is None:
        _rag_chain = RAGChain()
        _rag_chain.initialize()
    return _rag_chain
