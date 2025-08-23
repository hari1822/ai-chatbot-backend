import httpx
import asyncio
from typing import List, Dict, AsyncGenerator
from app.config import settings
import json
import logging

logger = logging.getLogger(__name__)

class OpenRouterService:
    """Service for interacting with OpenRouter API for AI responses."""
    
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model
        self.base_url = settings.openrouter_base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": {settings.site_url},  # Your site URL
            "X-Title": "AI Chatbot App"  # Your app name
        }
    
    async def generate_response(self, messages: List[Dict[str, str]], stream: bool = False) -> str:
        """
        Generate AI response using OpenRouter API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            stream: Whether to stream the response or get it all at once
        
        Returns:
            AI response text
        """
        if not self.api_key:
            logger.error("OpenRouter API key is not configured")
            return "I apologize, but I'm not properly configured to respond right now. Please contact the administrator."
        
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 2000,
                "temperature": 0.7,
                "stream": stream
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                if stream:
                    return await self._stream_response(client, payload)
                else:
                    return await self._get_complete_response(client, payload)
                    
        except httpx.TimeoutException:
            logger.error("OpenRouter API request timed out")
            return "I apologize, but I'm taking too long to respond. Please try again."
        except httpx.RequestError as e:
            logger.error(f"OpenRouter API request failed: {e}")
            return "I'm having trouble connecting right now. Please try again in a moment."
        except Exception as e:
            logger.error(f"Unexpected error with OpenRouter API: {e}")
            return "I encountered an unexpected error. Please try again."
    
    async def _get_complete_response(self, client: httpx.AsyncClient, payload: dict) -> str:
        """Get complete response from OpenRouter API."""
        response = await client.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload
        )
        
        response.raise_for_status()
        data = response.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"].strip()
        else:
            logger.error(f"Unexpected OpenRouter response format: {data}")
            return "I received an unexpected response format. Please try again."
    
    async def _stream_response(self, client: httpx.AsyncClient, payload: dict) -> str:
        """Stream response from OpenRouter API and return complete text."""
        full_response = ""
        
        async with client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]  # Remove "data: " prefix
                    
                    if data_str.strip() == "[DONE]":
                        break
                    
                    try:
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                full_response += delta["content"]
                    except json.JSONDecodeError:
                        continue
        
        return full_response.strip() if full_response else "I couldn't generate a response. Please try again."
    
    def format_messages_for_api(self, chat_messages: List) -> List[Dict[str, str]]:
        """
        Convert chat messages to OpenRouter API format.
        
        Args:
            chat_messages: List of ChatMessage objects from database
            
        Returns:
            List of formatted messages for API
        """
        formatted_messages = []
        
        # Add system message to set the AI's behavior
        formatted_messages.append({
            "role": "system",
            "content": "You are a helpful AI assistant. Provide informative, accurate, and engaging responses. Be concise but thorough in your answers."
        })
        
        # Convert chat messages to API format
        for msg in chat_messages:
            role = "user" if msg.sender_type == "user" else "assistant"
            formatted_messages.append({
                "role": role,
                "content": msg.content
            })
        
        return formatted_messages
    
    async def generate_chat_title(self, first_message: str) -> str:
        """
        Generate a concise title for the chat based on the first user message.
        
        Args:
            first_message: The first message from the user
            
        Returns:
            Generated chat title
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": "Generate a concise, descriptive title (max 5 words) for a chat conversation based on the user's first message. Only return the title, nothing else."
                },
                {
                    "role": "user",
                    "content": first_message
                }
            ]
            
            title = await self.generate_response(messages)
            # Ensure title is not too long
            if len(title) > 50:
                title = title[:47] + "..."
            
            return title.strip('"').strip("'")  # Remove quotes if present
            
        except Exception as e:
            logger.error(f"Failed to generate chat title: {e}")
            return "New Chat"

# Global instance
openrouter_service = OpenRouterService()
