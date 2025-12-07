"""
Tests for planning layer
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json

from forge.layers.planning import PlanningAgent, PlanningError


@pytest.fixture
def mock_api_key():
    """Mock API key for testing"""
    return "test-api-key-12345"


@pytest.fixture
def planning_agent(mock_api_key):
    """Create planning agent with mocked Anthropic client"""
    with patch('forge.layers.planning.Anthropic'):
        agent = PlanningAgent(mock_api_key)
        return agent


def test_planning_agent_initialization(mock_api_key):
    """Test planning agent initialization"""
    with patch('forge.layers.planning.Anthropic') as mock_anthropic:
        agent = PlanningAgent(mock_api_key)

        assert agent.model == "claude-sonnet-4-20250514"
        assert agent.conversation_history == []
        assert "started_at" in agent.session_metadata
        assert agent.session_metadata["turns"] == 0
        mock_anthropic.assert_called_once_with(api_key=mock_api_key)


def test_planning_agent_initialization_no_api_key():
    """Test planning agent initialization without API key"""
    with pytest.raises(PlanningError, match="API key is required"):
        PlanningAgent("")


def test_planning_agent_custom_model(mock_api_key):
    """Test planning agent with custom model"""
    with patch('forge.layers.planning.Anthropic'):
        agent = PlanningAgent(mock_api_key, model="claude-opus-4")
        assert agent.model == "claude-opus-4"


def test_conversation_history(planning_agent):
    """Test conversation history tracking"""
    # Initial state
    assert len(planning_agent.conversation_history) == 0

    # Add messages manually (simulating chat)
    planning_agent.conversation_history.append({
        "role": "user",
        "content": "Test message"
    })
    planning_agent.conversation_history.append({
        "role": "assistant",
        "content": "Test response"
    })

    assert len(planning_agent.conversation_history) == 2
    assert planning_agent.get_conversation_length() == 2


def test_get_last_messages(planning_agent):
    """Test getting last user and assistant messages"""
    # No messages yet
    assert planning_agent.get_last_user_message() is None
    assert planning_agent.get_last_assistant_message() is None

    # Add messages
    planning_agent.conversation_history = [
        {"role": "user", "content": "First user message"},
        {"role": "assistant", "content": "First assistant message"},
        {"role": "user", "content": "Second user message"},
        {"role": "assistant", "content": "Second assistant message"}
    ]

    assert planning_agent.get_last_user_message() == "Second user message"
    assert planning_agent.get_last_assistant_message() == "Second assistant message"


def test_clear_conversation(planning_agent):
    """Test clearing conversation history"""
    # Add some messages
    planning_agent.conversation_history = [
        {"role": "user", "content": "Test"},
        {"role": "assistant", "content": "Response"}
    ]
    planning_agent.session_metadata["turns"] = 5

    # Clear
    planning_agent.clear_conversation()

    assert len(planning_agent.conversation_history) == 0
    assert planning_agent.session_metadata["turns"] == 0
    assert "started_at" in planning_agent.session_metadata


def test_save_conversation(planning_agent, tmp_path):
    """Test saving conversation to file"""
    # Add conversation
    planning_agent.conversation_history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"}
    ]

    # Save to file
    filepath = tmp_path / "conversation.json"
    planning_agent.save_conversation(str(filepath))

    # Verify file exists and contains data
    assert filepath.exists()

    data = json.loads(filepath.read_text())
    assert "conversation" in data
    assert "session_metadata" in data
    assert "model" in data
    assert "saved_at" in data
    assert len(data["conversation"]) == 2


def test_load_conversation(planning_agent, tmp_path):
    """Test loading conversation from file"""
    # Create conversation file
    conversation_data = {
        "session_metadata": {"started_at": "2024-01-01", "turns": 3},
        "model": "claude-sonnet-4-20250514",
        "conversation": [
            {"role": "user", "content": "Test"},
            {"role": "assistant", "content": "Response"}
        ],
        "saved_at": "2024-01-01T12:00:00"
    }

    filepath = tmp_path / "conversation.json"
    filepath.write_text(json.dumps(conversation_data))

    # Load conversation
    planning_agent.load_conversation(str(filepath))

    assert len(planning_agent.conversation_history) == 2
    assert planning_agent.conversation_history[0]["content"] == "Test"
    assert planning_agent.session_metadata["turns"] == 3


def test_basic_extraction(planning_agent):
    """Test basic fallback extraction"""
    # Add conversation with tech keywords
    planning_agent.conversation_history = [
        {"role": "user", "content": "I want to build a Python application using Django and PostgreSQL"},
        {"role": "assistant", "content": "Great! Django and PostgreSQL are excellent choices."}
    ]

    # Get basic extraction
    summary = planning_agent._basic_extraction()

    assert "python" in summary["tech_stack"]
    assert "django" in summary["tech_stack"]
    assert "postgresql" in summary["tech_stack"]
    assert summary["extraction_method"] == "basic_fallback"


def test_format_conversation(planning_agent):
    """Test conversation formatting"""
    planning_agent.conversation_history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
        {"role": "user", "content": "How are you?"}
    ]

    formatted = planning_agent._format_conversation()

    assert "User: Hello" in formatted
    assert "Assistant: Hi there" in formatted
    assert "User: How are you?" in formatted


def test_get_project_summary_empty(planning_agent):
    """Test getting project summary with no conversation"""
    summary = planning_agent.get_project_summary()

    assert "error" in summary or "requirements" in summary
    # Should not crash with empty conversation


def test_get_project_summary_with_conversation(planning_agent):
    """Test getting project summary with conversation"""
    # Add sample conversation
    planning_agent.conversation_history = [
        {"role": "user", "content": "I want to build a REST API using Python and FastAPI"},
        {"role": "assistant", "content": "Great choice! What will the API do?"},
        {"role": "user", "content": "It will manage a todo list with user authentication"}
    ]

    # Mock the Claude API call for extraction
    with patch.object(planning_agent.client.messages, 'create') as mock_create:
        # Mock response
        mock_response = Mock()
        mock_content = Mock()
        mock_content.text = json.dumps({
            "project_name": "Todo API",
            "description": "REST API for todo management",
            "requirements": ["User authentication", "CRUD operations"],
            "tech_stack": ["Python", "FastAPI"],
            "features": ["Todo management"]
        })
        mock_response.content = [mock_content]
        mock_create.return_value = mock_response

        summary = planning_agent.get_project_summary()

        assert "project_name" in summary
        assert "tech_stack" in summary
        assert "session_metadata" in summary
        assert summary.get("conversation_turns") == 1  # 2 messages = 1 turn


def test_build_system_prompt(planning_agent):
    """Test system prompt building"""
    prompt = planning_agent._build_system_prompt()

    assert "Forge Planning Agent" in prompt
    assert "requirements" in prompt.lower()
    assert "technology stack" in prompt.lower()
    assert "success criteria" in prompt.lower()


@pytest.mark.asyncio
async def test_chat_empty_message(planning_agent):
    """Test chat with empty message"""
    with pytest.raises(PlanningError, match="Message cannot be empty"):
        async for _ in planning_agent.chat(""):
            pass


@pytest.mark.asyncio
async def test_chat_adds_to_history(planning_agent):
    """Test that chat adds messages to history"""
    # Mock the streaming response
    with patch.object(planning_agent.client.messages, 'stream') as mock_stream:
        # Create mock stream context manager
        mock_stream_context = MagicMock()
        mock_stream_context.__enter__.return_value.text_stream = iter(["Hello", " ", "there"])
        mock_stream.return_value = mock_stream_context

        # Send message
        response_text = ""
        async for chunk in planning_agent.chat("Test message"):
            response_text += chunk

        # Check history
        assert len(planning_agent.conversation_history) == 2
        assert planning_agent.conversation_history[0]["role"] == "user"
        assert planning_agent.conversation_history[0]["content"] == "Test message"
        assert planning_agent.conversation_history[1]["role"] == "assistant"
        assert planning_agent.session_metadata["turns"] == 1
