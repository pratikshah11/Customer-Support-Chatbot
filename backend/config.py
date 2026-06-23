"""
Configuration module — loads settings from Lambda environment variables.
"""
import os

# Bedrock model to use (set by Terraform)
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.meta.llama3-1-8b-instruct-v1:0")

# DynamoDB table for session storage
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "chatbot-dev-sessions")

# Session TTL in hours
SESSION_TTL_HOURS = int(os.environ.get("SESSION_TTL_HOURS", "24"))

# AWS region
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

# Model inference parameters
MAX_TOKENS = 1024
TEMPERATURE = 0.7
TOP_P = 0.9

# Max number of conversation turns to keep in memory (to avoid token limits)
# Each turn = 1 user message + 1 assistant message
MAX_CONVERSATION_TURNS = 20

# System prompt — defines the chatbot's persona and behavior
SYSTEM_PROMPT = """You are a friendly, professional, and helpful customer support assistant. 

Your role is to:
- Answer customer questions clearly and concisely
- Help troubleshoot issues step by step
- Provide accurate information and honest guidance
- Be empathetic and patient, especially when customers are frustrated
- If you don't know something, say so honestly and suggest next steps (e.g., escalating to a human agent)

Guidelines:
- Keep responses concise and easy to understand
- Use bullet points or numbered lists when explaining multi-step processes
- Always be polite and professional
- Never make up information you're not sure about
- If asked about something outside your knowledge, acknowledge it and offer to help with what you can

You are ready to assist customers with any questions or issues they may have."""
