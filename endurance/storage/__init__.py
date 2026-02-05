"""
Storage module - Database engines for Endurance.
"""

from endurance.storage.mongo_engine import MongoEngine, get_mongo_engine

__all__ = ["MongoEngine", "get_mongo_engine"]
