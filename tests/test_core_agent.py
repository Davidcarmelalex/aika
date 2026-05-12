"""
AIKA Core Agent Tests
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from agents.aika_core.core_agent import AIKACoreAgent, Message, Response


class TestAIKACoreAgent:
    @pytest.mark.asyncio
    async def test_handle_routes_to_ayooni(self):
        mock_ayooni = MagicMock()
        mock_ayooni.process = AsyncMock(return_value={"response": "Hello!"})
        
        agent = AIKACoreAgent(ayooni_client=mock_ayooni)
        msg = Message(user_id="u1", channel="telegram", text="Hello")
        
        response = await agent.handle(msg)
        
        assert isinstance(response, Response)
        assert response.text == "Hello!"
        mock_ayooni.process.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_gracefully_fails_on_ayooni_error(self):
        mock_ayooni = MagicMock()
        mock_ayooni.process = AsyncMock(side_effect=Exception("Connection refused"))
        
        agent = AIKACoreAgent(ayooni_client=mock_ayooni)
        msg = Message(user_id="u1", channel="telegram", text="test")
        
        response = await agent.handle(msg)
        assert "issue" in response.text.lower() or "try again" in response.text.lower()
    
    @pytest.mark.asyncio
    async def test_handle_stores_memory_on_success(self):
        mock_ayooni = MagicMock()
        mock_ayooni.process = AsyncMock(return_value={"response": "Done!"})
        mock_memory = MagicMock()
        mock_memory.store = AsyncMock()
        mock_memory.get_context = AsyncMock(return_value={})
        
        agent = AIKACoreAgent(ayooni_client=mock_ayooni, memory_store=mock_memory)
        msg = Message(user_id="u1", channel="telegram", text="Do something")
        
        await agent.handle(msg)
        mock_memory.store.assert_called_once_with("u1", "Do something", "Done!")
