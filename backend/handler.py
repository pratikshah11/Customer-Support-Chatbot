"""
Lambda handler — main entry point for all WebSocket events.

Handles three route types from API Gateway WebSocket:
  - $connect    → client opens a WebSocket connection
  - $disconnect → client closes the connection
  - sendMessage → client sends a chat message (main chat route)
  - $default    → fallback for any unrecognized action
"""
import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

from chat_service import ChatService
from session_store import SessionStore

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize services (outside handler for Lambda warm-start reuse)
chat_service = ChatService()
session_store = SessionStore()


def get_apigw_client(domain_name: str, stage: str):
    """Create API Gateway Management API client to push messages to WebSocket clients."""
    endpoint_url = f"https://{domain_name}/{stage}"
    return boto3.client(
        "apigatewaymanagementapi",
        endpoint_url=endpoint_url,
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    )


def send_message(apigw_client, connection_id: str, message: dict) -> bool:
    """Send a JSON message back to a connected WebSocket client."""
    try:
        apigw_client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message).encode("utf-8"),
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "GoneException":
            logger.warning(f"Connection {connection_id} is gone (client disconnected)")
        else:
            logger.error(f"Failed to send message to {connection_id}: {e}")
        return False


def handle_connect(connection_id: str) -> dict:
    """Handle new WebSocket connection — just log it."""
    logger.info(f"Client connected: {connection_id}")
    return {"statusCode": 200, "body": "Connected"}


def handle_disconnect(connection_id: str) -> dict:
    """Handle WebSocket disconnection — clean up session."""
    logger.info(f"Client disconnected: {connection_id}")
    session_store.delete_session(connection_id)
    return {"statusCode": 200, "body": "Disconnected"}


def handle_message(event: dict, connection_id: str) -> dict:
    """Handle an incoming chat message from a connected client."""
    # Parse the request body
    try:
        body = json.loads(event.get("body", "{}"))
        user_message = body.get("message", "").strip()
        # Allow clients to use a custom session ID (e.g., UUID from frontend)
        # Falls back to connection_id if not provided
        session_id = body.get("session_id", connection_id)
    except (json.JSONDecodeError, AttributeError) as e:
        logger.error(f"Failed to parse message body: {e}")
        return {"statusCode": 400, "body": "Invalid message format"}

    if not user_message:
        return {"statusCode": 400, "body": "Empty message"}

    # Set up API Gateway client to push responses
    request_context = event["requestContext"]
    apigw_client = get_apigw_client(
        domain_name=request_context["domainName"],
        stage=request_context["stage"],
    )

    # Send "typing" indicator to the client
    send_message(apigw_client, connection_id, {"type": "typing", "status": True})

    # Retrieve session history
    history = session_store.get_history(session_id)

    # Get response from Bedrock
    response_text, updated_history = chat_service.get_response(user_message, history)

    # Save updated history
    session_store.update_history(session_id, updated_history)

    # Stop typing indicator and send the actual response
    send_message(apigw_client, connection_id, {"type": "typing", "status": False})
    send_message(apigw_client, connection_id, {
        "type": "message",
        "role": "assistant",
        "content": response_text,
        "session_id": session_id,
    })

    return {"statusCode": 200, "body": "Message processed"}


def lambda_handler(event: dict, context) -> dict:
    """Main Lambda entry point — routes events by WebSocket route key."""
    request_context = event.get("requestContext", {})
    route_key = request_context.get("routeKey", "$default")
    connection_id = request_context.get("connectionId", "unknown")

    logger.info(f"Route: {route_key}, Connection: {connection_id}")

    try:
        if route_key == "$connect":
            return handle_connect(connection_id)
        elif route_key == "$disconnect":
            return handle_disconnect(connection_id)
        elif route_key == "sendMessage":
            return handle_message(event, connection_id)
        else:
            logger.warning(f"Unhandled route: {route_key}")
            return {"statusCode": 400, "body": f"Unknown route: {route_key}"}

    except Exception as e:
        logger.error(f"Unhandled error in lambda_handler: {e}", exc_info=True)
        return {"statusCode": 500, "body": "Internal server error"}
