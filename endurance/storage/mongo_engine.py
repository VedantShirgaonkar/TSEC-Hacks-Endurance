"""
MongoDB Engine - Persistent storage for Endurance metrics.
"""

from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure, OperationFailure
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

class MongoEngine:
    """MongoDB client for storing sessions and service metrics."""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize MongoDB connection.
        
        Args:
            connection_string: MongoDB connection URI. If None, reads from env.
        """
        self.connection_string = connection_string or os.getenv("MONGO_URI")
        self.client = None
        self.db = None
        self.connected = False
        
        if self.connection_string:
            self._connect()
    
    def _connect(self):
        """Establish MongoDB connection."""
        try:
            # Use ServerApi for MongoDB Atlas compatibility
            server_api = ServerApi(version="1", strict=True, deprecation_errors=True)
            self.client = MongoClient(
                self.connection_string,
                server_api=server_api,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
            )
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client.endurance
            self.connected = True
            print(f"[MongoDB] Connected successfully to Endurance database")
        except ConnectionFailure as e:
            print(f"[MongoDB] Connection failed: {e}")
            self.connected = False
        except Exception as e:
            print(f"[MongoDB] Unexpected error: {e}")
            self.connected = False
    
    def insert_session(self, session_data: Dict[str, Any]) -> Optional[str]:
        """
        Insert a new evaluation session.
        
        Args:
            session_data: Session data including scores, query, response, etc.
            
        Returns:
            Inserted document ID or None if failed
        """
        if not self.connected:
            return None
        
        try:
            # Add timestamp if not present
            if "timestamp" not in session_data:
                session_data["timestamp"] = datetime.now().isoformat()
            
            result = self.db.sessions.insert_one(session_data)
            return str(result.inserted_id)
        except OperationFailure as e:
            print(f"[MongoDB] Insert failed: {e}")
            return None
    
    def get_sessions(
        self,
        limit: int = 50,
        service_id: Optional[str] = None,
        flagged_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve sessions with optional filters.
        
        Args:
            limit: Maximum number of sessions to return
            service_id: Filter by service ID
            flagged_only: Only return flagged sessions
            
        Returns:
            List of session documents
        """
        if not self.connected:
            return []
        
        try:
            query = {}
            if service_id:
                query["service_id"] = service_id
            if flagged_only:
                query["flagged"] = True
            
            cursor = self.db.sessions.find(query).sort("timestamp", -1).limit(limit)
            sessions = []
            for doc in cursor:
                # Convert ObjectId to string
                doc["_id"] = str(doc["_id"])
                sessions.append(doc)
            return sessions
        except Exception as e:
            print(f"[MongoDB] Query failed: {e}")
            return []
    
    def get_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific session by ID."""
        if not self.connected:
            return None
        
        try:
            doc = self.db.sessions.find_one({"session_id": session_id})
            if doc:
                doc["_id"] = str(doc["_id"])
            return doc
        except Exception as e:
            print(f"[MongoDB] Query failed: {e}")
            return None
    
    def update_service_stats(self, service_id: str, session_data: Dict[str, Any]):
        """
        Update aggregate statistics for a service.
        
        Args:
            service_id: Service identifier
            session_data: Session data to aggregate
        """
        if not self.connected:
            return
        
        try:
            # Use upsert to create or update
            self.db.services.update_one(
                {"service_id": service_id},
                {
                    "$inc": {
                        "total_sessions": 1,
                        "flagged_count": 1 if session_data.get("flagged") else 0,
                    },
                    "$push": {
                        "recent_scores": {
                            "$each": [session_data.get("overall_score", 0)],
                            "$slice": -100  # Keep last 100 scores
                        }
                    },
                    "$set": {
                        "last_updated": datetime.now().isoformat()
                    }
                },
                upsert=True
            )
        except Exception as e:
            print(f"[MongoDB] Service stats update failed: {e}")
    
    def get_service_stats(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get aggregate statistics for a service."""
        if not self.connected:
            return None
        
        try:
            doc = self.db.services.find_one({"service_id": service_id})
            if doc:
                doc["_id"] = str(doc["_id"])
                # Calculate average score
                scores = doc.get("recent_scores", [])
                if scores:
                    doc["avg_score"] = sum(scores) / len(scores)
                else:
                    doc["avg_score"] = 0.0
            return doc
        except Exception as e:
            print(f"[MongoDB] Query failed: {e}")
            return None
    
    def get_all_services(self) -> List[Dict[str, Any]]:
        """Get all tracked services with their stats."""
        if not self.connected:
            return []
        
        try:
            cursor = self.db.services.find()
            services = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                scores = doc.get("recent_scores", [])
                doc["avg_score"] = sum(scores) / len(scores) if scores else 0.0
                services.append(doc)
            return services
        except Exception as e:
            print(f"[MongoDB] Query failed: {e}")
            return []
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get overall system metrics."""
        if not self.connected:
            return {
                "total_sessions": 0,
                "flagged_sessions": 0,
                "services_count": 0,
                "connected": False
            }
        
        try:
            total = self.db.sessions.count_documents({})
            flagged = self.db.sessions.count_documents({"flagged": True})
            services = self.db.services.count_documents({})
            
            return {
                "total_sessions": total,
                "flagged_sessions": flagged,
                "flagged_percentage": (flagged / total * 100) if total > 0 else 0,
                "services_count": services,
                "connected": True
            }
        except Exception as e:
            print(f"[MongoDB] Metrics query failed: {e}")
            return {
                "total_sessions": 0,
                "flagged_sessions": 0,
                "services_count": 0,
                "connected": False
            }
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.connected = False
            print("[MongoDB] Connection closed")


# Global instance
_mongo_engine = None

def get_mongo_engine() -> MongoEngine:
    """Get or create the global MongoDB engine instance."""
    global _mongo_engine
    if _mongo_engine is None:
        _mongo_engine = MongoEngine()
    return _mongo_engine
