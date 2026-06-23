"""
Unit tests for session_store.py — DynamoDB session management.
All DynamoDB calls are mocked so these run without AWS credentials.
"""
import sys
import os
import time
import unittest
from unittest.mock import MagicMock, patch

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestSessionStore(unittest.TestCase):

    def setUp(self):
        """Set up DynamoDB mocks before each test."""
        self.mock_table = MagicMock()
        self.mock_dynamodb = MagicMock()
        self.mock_dynamodb.Table.return_value = self.mock_table

        patcher = patch('boto3.resource', return_value=self.mock_dynamodb)
        self.addCleanup(patcher.stop)
        patcher.start()

        from session_store import SessionStore
        self.store = SessionStore()

    # ----------------------------------------------------------
    # get_history
    # ----------------------------------------------------------
    def test_get_history_returns_messages(self):
        """Test that get_history returns messages from an existing session."""
        messages = [
            {"role": "user", "content": [{"text": "Hello"}]},
            {"role": "assistant", "content": [{"text": "Hi there!"}]},
        ]
        self.mock_table.get_item.return_value = {
            "Item": {"session_id": "test-123", "messages": messages}
        }

        result = self.store.get_history("test-123")

        self.assertEqual(result, messages)
        self.mock_table.get_item.assert_called_once_with(Key={"session_id": "test-123"})

    def test_get_history_returns_empty_for_missing_session(self):
        """Test that get_history returns [] when session doesn't exist."""
        self.mock_table.get_item.return_value = {}  # No "Item" key

        result = self.store.get_history("nonexistent-session")

        self.assertEqual(result, [])

    def test_get_history_returns_empty_on_error(self):
        """Test that get_history returns [] on DynamoDB errors (fail-safe)."""
        from botocore.exceptions import ClientError
        self.mock_table.get_item.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "Table not found"}},
            "get_item"
        )

        result = self.store.get_history("test-123")

        self.assertEqual(result, [])

    # ----------------------------------------------------------
    # update_history
    # ----------------------------------------------------------
    def test_update_history_saves_messages(self):
        """Test that update_history calls DynamoDB put_item with correct data."""
        messages = [{"role": "user", "content": [{"text": "Test"}]}]

        result = self.store.update_history("session-abc", messages)

        self.assertTrue(result)
        self.mock_table.put_item.assert_called_once()

        call_item = self.mock_table.put_item.call_args.kwargs["Item"]
        self.assertEqual(call_item["session_id"], "session-abc")
        self.assertEqual(call_item["messages"], messages)
        self.assertIn("expires_at", call_item)

    def test_update_history_sets_future_expiry(self):
        """Test that the TTL is set in the future."""
        messages = []
        now = int(time.time())

        self.store.update_history("session-abc", messages)

        call_item = self.mock_table.put_item.call_args.kwargs["Item"]
        expires_at = call_item["expires_at"]
        self.assertGreater(expires_at, now)

    def test_update_history_trims_long_conversations(self):
        """Test that conversations exceeding MAX_CONVERSATION_TURNS are trimmed."""
        from backend.config import MAX_CONVERSATION_TURNS

        # Create a very long conversation (more than max)
        messages = []
        for i in range(MAX_CONVERSATION_TURNS * 2 + 10):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append({"role": role, "content": [{"text": f"Message {i}"}]})

        self.store.update_history("session-abc", messages)

        call_item = self.mock_table.put_item.call_args.kwargs["Item"]
        saved_messages = call_item["messages"]
        self.assertLessEqual(len(saved_messages), MAX_CONVERSATION_TURNS * 2)

    def test_update_history_returns_false_on_error(self):
        """Test that update_history returns False on DynamoDB errors."""
        from botocore.exceptions import ClientError
        self.mock_table.put_item.side_effect = ClientError(
            {"Error": {"Code": "ProvisionedThroughputExceededException", "Message": "Throttled"}},
            "put_item"
        )

        result = self.store.update_history("session-abc", [])

        self.assertFalse(result)

    # ----------------------------------------------------------
    # delete_session
    # ----------------------------------------------------------
    def test_delete_session_calls_dynamodb(self):
        """Test that delete_session correctly calls DynamoDB delete_item."""
        result = self.store.delete_session("session-xyz")

        self.assertTrue(result)
        self.mock_table.delete_item.assert_called_once_with(
            Key={"session_id": "session-xyz"}
        )

    def test_delete_session_returns_false_on_error(self):
        """Test that delete_session returns False on errors."""
        from botocore.exceptions import ClientError
        self.mock_table.delete_item.side_effect = ClientError(
            {"Error": {"Code": "InternalServerError", "Message": "Error"}},
            "delete_item"
        )

        result = self.store.delete_session("session-xyz")

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
