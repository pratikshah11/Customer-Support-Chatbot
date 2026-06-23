"""
Unit tests for chat_service.py — Bedrock interactions.
All Bedrock calls are mocked so these run without AWS credentials.
"""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestChatService(unittest.TestCase):

    def setUp(self):
        """Set up mocks before each test."""
        # Mock boto3 so no real AWS calls are made
        self.mock_bedrock = MagicMock()
        patcher = patch('boto3.client', return_value=self.mock_bedrock)
        self.addCleanup(patcher.stop)
        patcher.start()

        # Import after patching
        from chat_service import ChatService
        self.chat_service = ChatService()

    def _make_bedrock_response(self, text: str, input_tokens: int = 10, output_tokens: int = 20):
        """Helper to construct a mock Bedrock Converse API response."""
        return {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": text}]
                }
            },
            "usage": {
                "inputTokens": input_tokens,
                "outputTokens": output_tokens,
            }
        }

    def test_basic_response(self):
        """Test that a basic message returns a response and updated history."""
        self.mock_bedrock.converse.return_value = self._make_bedrock_response(
            "Hello! How can I help you today?"
        )

        response, history = self.chat_service.get_response("Hi", [])

        self.assertEqual(response, "Hello! How can I help you today?")
        self.assertEqual(len(history), 2)  # user + assistant
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[1]["role"], "assistant")

    def test_system_prompt_included(self):
        """Test that the system prompt is sent with every request."""
        self.mock_bedrock.converse.return_value = self._make_bedrock_response("OK")

        self.chat_service.get_response("Hello", [])

        call_kwargs = self.mock_bedrock.converse.call_args
        # system should be a non-empty list
        self.assertIn("system", call_kwargs.kwargs)
        system = call_kwargs.kwargs["system"]
        self.assertTrue(len(system) > 0)
        self.assertIn("text", system[0])
        self.assertTrue(len(system[0]["text"]) > 0)

    def test_conversation_history_passed(self):
        """Test that existing conversation history is sent to Bedrock.

        Note: The mock captures a reference to the updated_history list.
        Since the assistant message is appended to that same list object
        after the converse() call returns, the captured list will have
        4 items (2 existing + 1 new user + 1 assistant).
        We verify the correct messages are present rather than checking count.
        """
        self.mock_bedrock.converse.return_value = self._make_bedrock_response("Sure!")

        existing_history = [
            {"role": "user", "content": [{"text": "First message"}]},
            {"role": "assistant", "content": [{"text": "First response"}]},
        ]

        self.chat_service.get_response("Follow-up", existing_history)

        call_args = self.mock_bedrock.converse.call_args
        messages = call_args.kwargs["messages"]

        # The first two messages are the existing history
        self.assertEqual(messages[0]["content"][0]["text"], "First message")
        self.assertEqual(messages[1]["content"][0]["text"], "First response")
        # The new user message appears third (index 2)
        self.assertEqual(messages[2]["role"], "user")
        self.assertEqual(messages[2]["content"][0]["text"], "Follow-up")

    def test_history_grows_correctly(self):
        """Test that each call adds exactly user + assistant to history."""
        self.mock_bedrock.converse.return_value = self._make_bedrock_response("Response 1")
        _, history = self.chat_service.get_response("Message 1", [])
        self.assertEqual(len(history), 2)

        self.mock_bedrock.converse.return_value = self._make_bedrock_response("Response 2")
        _, history = self.chat_service.get_response("Message 2", history)
        self.assertEqual(len(history), 4)

    def test_throttling_error_handling(self):
        """Test that ThrottlingException returns a user-friendly message."""
        from botocore.exceptions import ClientError
        self.mock_bedrock.converse.side_effect = ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
            "converse"
        )

        response, history = self.chat_service.get_response("Hello", [])

        self.assertIn("lot of requests", response)
        self.assertEqual(history, [])  # History unchanged on error

    def test_model_not_ready_error_handling(self):
        """Test that ModelNotReadyException returns a user-friendly message."""
        from botocore.exceptions import ClientError
        self.mock_bedrock.converse.side_effect = ClientError(
            {"Error": {"Code": "ModelNotReadyException", "Message": "Model loading"}},
            "converse"
        )

        response, history = self.chat_service.get_response("Hello", [])

        self.assertIn("warming up", response)
        self.assertEqual(history, [])

    def test_unexpected_error_handling(self):
        """Test that unexpected exceptions return a safe fallback message."""
        self.mock_bedrock.converse.side_effect = RuntimeError("Unexpected crash")

        response, history = self.chat_service.get_response("Hello", [])

        self.assertIn("unexpected error", response.lower())
        self.assertEqual(history, [])

    def test_model_id_used(self):
        """Test that the correct model ID is passed to Bedrock."""
        self.mock_bedrock.converse.return_value = self._make_bedrock_response("OK")

        self.chat_service.get_response("Hello", [])

        call_kwargs = self.mock_bedrock.converse.call_args
        self.assertIn("modelId", call_kwargs.kwargs)
        self.assertEqual(call_kwargs.kwargs["modelId"], self.chat_service.model_id)


if __name__ == "__main__":
    unittest.main()
