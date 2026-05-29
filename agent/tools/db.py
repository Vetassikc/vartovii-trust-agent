"""
MongoDB Connection Manager for Vartovii Trust Agent.

Provides a singleton MongoDB client with connection pooling,
automatic retry, and graceful fallback to mock data when
MongoDB is unavailable.
"""

import logging
import os
import threading
from typing import Optional

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import (
    ConnectionFailure,
    ConfigurationError,
    ServerSelectionTimeoutError,
)

logger = logging.getLogger("vartovii.db")

# ---------------------------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------------------------
MONGODB_CONNECTION_STRING: str = os.getenv("MONGODB_CONNECTION_STRING", "")
MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "vartovii")
MONGODB_ENABLED: bool = os.getenv("MONGODB_ENABLED", "true").lower() in (
    "true",
    "1",
    "yes",
)


class MongoDBManager:
    """Singleton MongoDB connection manager.

    Thread-safe singleton that maintains a single ``MongoClient`` with
    connection pooling.  When MongoDB is unreachable the manager degrades
    gracefully — ``available`` is set to ``False`` and every public accessor
    returns ``None`` instead of raising.
    """

    _instance: Optional["MongoDBManager"] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None
    _lock: threading.Lock = threading.Lock()
    available: bool = False

    def __init__(self) -> None:
        """Initialise the manager and attempt to connect.

        This constructor is **not** meant to be called directly — use
        :meth:`get_instance` instead.
        """
        if not MONGODB_ENABLED:
            logger.info("MongoDB integration is disabled via MONGODB_ENABLED env var.")
            return

        if not MONGODB_CONNECTION_STRING:
            logger.warning(
                "MONGODB_CONNECTION_STRING is not set. MongoDB will be unavailable."
            )
            return

        try:
            self._client = MongoClient(
                MONGODB_CONNECTION_STRING,
                maxPoolSize=10,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                retryWrites=True,
                retryReads=True,
            )

            # Force a round-trip to verify the connection is alive.
            self._client.admin.command("ping")

            self._db = self._client[MONGODB_DATABASE]
            self.available = True
            logger.info(
                "Successfully connected to MongoDB (database: %s).", MONGODB_DATABASE
            )
        except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
            logger.warning(
                "MongoDB is unavailable — falling back to mock data. Error: %s", exc
            )
            self._cleanup()
        except ConfigurationError as exc:
            logger.warning(
                "MongoDB configuration error — falling back to mock data. Error: %s",
                exc,
            )
            self._cleanup()

    # ------------------------------------------------------------------
    # Singleton accessor
    # ------------------------------------------------------------------

    @classmethod
    def get_instance(cls) -> "MongoDBManager":
        """Get or create the singleton instance.

        Returns:
            The shared :class:`MongoDBManager` instance.
        """
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking pattern.
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def db(self) -> Optional[Database]:
        """Get the database instance.

        Returns:
            The :class:`~pymongo.database.Database` object, or ``None`` if
            MongoDB is unavailable.
        """
        return self._db

    def get_collection(self, name: str) -> Optional[Collection]:
        """Get a collection by name.

        Args:
            name: The collection name.

        Returns:
            The :class:`~pymongo.collection.Collection`, or ``None`` if
            MongoDB is unavailable.
        """
        if self._db is None:
            logger.debug(
                "Attempted to access collection '%s' but MongoDB is unavailable.", name
            )
            return None
        return self._db[name]

    def is_available(self) -> bool:
        """Check if the MongoDB connection is alive.

        Performs a lightweight ``ping`` against the server.  If the ping
        fails the manager marks itself as unavailable.

        Returns:
            ``True`` if the connection is healthy, ``False`` otherwise.
        """
        if not self.available or self._client is None:
            return False

        try:
            self._client.admin.command("ping")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
            logger.warning("MongoDB health-check failed: %s", exc)
            self.available = False
            return False

    def close(self) -> None:
        """Close the MongoDB connection and release resources."""
        self._cleanup()
        logger.info("MongoDB connection closed.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _cleanup(self) -> None:
        """Close the client and reset internal state."""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:  # noqa: BLE001
                pass
        self._client = None
        self._db = None
        self.available = False


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

def get_db() -> Optional[Database]:
    """Get the database.

    Returns:
        The :class:`~pymongo.database.Database` instance, or ``None`` if
        MongoDB is unavailable.
    """
    return MongoDBManager.get_instance().db


def get_collection(name: str) -> Optional[Collection]:
    """Get a collection by name.

    Args:
        name: The collection name.

    Returns:
        The :class:`~pymongo.collection.Collection`, or ``None`` if
        MongoDB is unavailable.
    """
    return MongoDBManager.get_instance().get_collection(name)


def is_mongodb_available() -> bool:
    """Check if MongoDB is available.

    Returns:
        ``True`` if a working connection exists, ``False`` otherwise.
    """
    return MongoDBManager.get_instance().is_available()
