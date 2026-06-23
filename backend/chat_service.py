"""
Chat service — handles communication with Amazon Bedrock using the Converse API.

The Bedrock Converse API is model-agnostic and works with Llama, Titan, and others,
making it easy to swap models later by just changing the model ID.
"""
import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from config import (
    BEDROCK_MODEL_ID,
    MAX_TOKENS,
    TEMPERATURE,
    TOP_P,
    SYSTEM_PROMPT,
    AWS_REGION,
)

logger = logging.getLogger(__name__)


class ChatService:
    """Wraps Amazon Bedrock Converse API calls."""

    def __init__(self):
        self.bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)
        self.model_id = BEDROCK_MODEL_ID

    def get_response(self, user_message: str, conversation_history: list) -> tuple[str, list]:
        """
        Send a message to Bedrock and return the assistant's response.

        Args:
            user_message: The latest message from the user
            conversation_history: Previous messages in the format
                                   [{"role": "user"/"assistant", "content": "..."}]

        Returns:
            Tuple of (response_text, updated_history)
        """
        # Append the new user message to history
        updated_history = conversation_history + [
            {"role": "user", "content": [{"text": user_message}]}
        ]

        try:
            response = self.bedrock.converse(
                modelId=self.model_id,
                system=[{"text": SYSTEM_PROMPT}],
                messages=updated_history,
                inferenceConfig={
                    "maxTokens": MAX_TOKENS,
                    "temperature": TEMPERATURE,
                    "topP": TOP_P,
                },
            )

            # Extract the assistant's response text
            assistant_message = response["output"]["message"]
            response_text = assistant_message["content"][0]["text"]

            # Append assistant response to history
            updated_history.append({
                "role": "assistant",
                "content": [{"text": response_text}]
            })

            logger.info(
                f"Bedrock response received. "
                f"Input tokens: {response['usage']['inputTokens']}, "
                f"Output tokens: {response['usage']['outputTokens']}"
            )

            return response_text, updated_history

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error(f"Bedrock API error [{error_code}]: {e}")

            if error_code == "ThrottlingException":
                return (
                    "I'm receiving a lot of requests right now. Please try again in a moment.",
                    conversation_history,
                )
            elif error_code == "ModelNotReadyException":
                return (
                    "The AI model is warming up. Please try again in a few seconds.",
                    conversation_history,
                )
            else:
                return (
                    "I'm having trouble processing your request right now. Please try again.",
                    conversation_history,
                )

        except Exception as e:
            logger.error(f"Unexpected error calling Bedrock: {e}")
            return (
                "An unexpected error occurred. Please try again.",
                conversation_history,
            )
