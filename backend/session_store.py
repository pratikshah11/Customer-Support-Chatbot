"""
Session store — manages conversation history in DynamoDB.

Each session record in DynamoDB has the structure:
{
    "session_id": "abc-123",           # Partition key (from WebSocket connection ID or UUID)
    "messages": [...],                  # List of {"role": "user"/"assistant", "content": "..."}
    "expires_at": 1234567890           # Unix timestamp for TTL auto-deletion
}
"""
import json
import logging
import time
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from config import DYNAMODB_TABLE, SESSION_TTL_HOURS, MAX_CONVERSATION_TURNS

logger = logging.getLogger(__name__)


class SessionStore:
    """Manages chat session history in DynamoDB."""

    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(DYNAMODB_TABLE)

    def _get_expiry_timestamp(self) -> int:
        """Returns a Unix timestamp SESSION_TTL_HOURS from now."""
        return int(time.time()) + (SESSION_TTL_HOURS * 3600)

    def get_history(self, session_id: str) -> list:
        """
        Retrieve conversation history for a session.
        Returns empty list if session doesn't exist.
        """
        try:
            response = self.table.get_item(Key={"session_id": session_id})
            item = response.get("Item")
            if item:
                return item.get("messages", [])
            return []
        except ClientError as e:
            logger.error(f"Failed to get session history for {session_id}: {e}")
            return []

    def update_history(self, session_id: str, messages: list) -> bool:
        """
        Save updated conversation history for a session.
        Trims history if it exceeds MAX_CONVERSATION_TURNS.
        Returns True on success, False on failure.
        """
        # Trim to max turns (keep most recent turns, always keep the system framing)
        if len(messages) > MAX_CONVERSATION_TURNS * 2:
            messages = messages[-(MAX_CONVERSATION_TURNS * 2):]

        try:
            self.table.put_item(
                Item={
                    "session_id": session_id,
                    "messages": messages,
                    "expires_at": self._get_expiry_timestamp(),
                }
            )
            return True
        except ClientError as e:
            logger.error(f"Failed to update session history for {session_id}: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session record from DynamoDB.
        Called on WebSocket $disconnect.
        """
        try:
            self.table.delete_item(Key={"session_id": session_id})
            return True
        except ClientError as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
