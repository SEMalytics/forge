"""
Conversational planning agent using Claude API

This module provides an interactive planning agent that helps users
define their software projects through natural conversation.
"""

from anthropic import Anthropic
from typing import List, Dict, Optional, AsyncIterator, Any
import json
import re
from datetime import datetime

from forge.utils.logger import logger
from forge.utils.errors import ForgeError


class PlanningError(ForgeError):
    """Errors during planning phase"""
    pass


class PlanningAgent:
    """
    Interactive planning agent using Claude API.

    Guides users through project planning via conversational interface,
    extracting requirements, constraints, and technical specifications.
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize planning agent.

        Args:
            api_key: Anthropic API key
            model: Claude model to use

        Raises:
            PlanningError: If initialization fails
        """
        if not api_key:
            raise PlanningError("API key is required")

        try:
            self.client = Anthropic(api_key=api_key)
            self.model = model
            self.conversation_history: List[Dict[str, str]] = []
            self.session_metadata: Dict[str, Any] = {
                "started_at": datetime.now().isoformat(),
                "turns": 0
            }
            logger.info(f"Initialized PlanningAgent with model: {model}")
        except Exception as e:
            raise PlanningError(f"Failed to initialize planning agent: {e}")

    async def chat(self, user_message: str) -> AsyncIterator[str]:
        """
        Engage in conversational planning.

        Args:
            user_message: User's message

        Yields:
            Response text chunks (streaming)

        Raises:
            PlanningError: If chat fails
        """
        if not user_message.strip():
            raise PlanningError("Message cannot be empty")

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        logger.debug(f"User message: {user_message[:100]}...")

        # Create planning system prompt
        system_prompt = self._build_system_prompt()

        try:
            response_text = ""

            # Stream response from Claude
            with self.client.messages.stream(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                system=system_prompt,
                messages=self.conversation_history
            ) as stream:
                for text in stream.text_stream:
                    response_text += text
                    yield text

            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })

            self.session_metadata["turns"] += 1
            logger.debug(f"Assistant response: {response_text[:100]}...")

        except Exception as e:
            logger.error(f"Chat failed: {e}")
            raise PlanningError(f"Failed to get response: {e}")

    def _build_system_prompt(self) -> str:
        """Build system prompt for planning agent."""
        return """You are the Forge Planning Agent, an expert software architect and project planner.

Your role is to help users plan software projects through friendly, professional conversation.

**Your Goals:**
1. Understand the user's project vision and requirements
2. Ask clarifying questions to gather essential details
3. Identify technical stack preferences and constraints
4. Determine success criteria and project scope
5. Extract actionable requirements for implementation

**Guidelines:**
- Be concise and friendly (2-4 sentences per response)
- Ask one or two focused questions at a time
- Listen carefully and build on what the user shares
- Guide the conversation naturally toward complete requirements
- Acknowledge user input before asking follow-up questions
- Use markdown formatting for clarity

**Information to Gather:**
- Project purpose and target users
- Core features and functionality
- Technology stack preferences (languages, frameworks, databases)
- Deployment environment and constraints
- Performance and scalability requirements
- Security and compliance needs
- Timeline and resource constraints
- Success metrics

**Response Style:**
- Professional but approachable
- Clear and organized
- Use bullet points for multiple items
- Highlight key points with **bold**
- Ask thoughtful follow-up questions

Remember: You're helping plan a project that will be built by AI systems, so focus on clear, implementable requirements."""

    def get_project_summary(self) -> Dict[str, Any]:
        """
        Extract structured project summary from conversation.

        Analyzes the conversation history to extract key project details
        including requirements, tech stack, constraints, and goals.

        Returns:
            Dictionary with extracted project information

        Raises:
            PlanningError: If summary extraction fails
        """
        if not self.conversation_history:
            return {
                "error": "No conversation history available",
                "requirements": [],
                "tech_stack": [],
                "constraints": []
            }

        try:
            # Build extraction prompt
            conversation_text = self._format_conversation()

            extraction_prompt = f"""Analyze this project planning conversation and extract structured information.

{conversation_text}

Extract and return a JSON object with:
- project_name: Brief project name
- description: One sentence description
- requirements: List of key requirements
- features: List of main features
- tech_stack: Technologies mentioned (languages, frameworks, databases)
- constraints: Any constraints (timeline, budget, compliance)
- success_criteria: What defines project success
- deployment: Deployment environment/platform
- target_users: Who will use this

Return ONLY valid JSON, no other text."""

            # Get structured extraction
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.3,  # Lower temperature for structured output
                messages=[{
                    "role": "user",
                    "content": extraction_prompt
                }]
            )

            # Parse response
            response_text = response.content[0].text

            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                summary = json.loads(json_match.group(0))
            else:
                # Fallback to basic extraction
                summary = self._basic_extraction()

            # Add metadata
            summary["session_metadata"] = self.session_metadata
            summary["conversation_turns"] = len(self.conversation_history) // 2

            logger.info("Extracted project summary successfully")
            return summary

        except Exception as e:
            logger.error(f"Failed to extract project summary: {e}")
            # Return basic extraction as fallback
            return self._basic_extraction()

    def _format_conversation(self) -> str:
        """Format conversation history as readable text."""
        lines = []
        for msg in self.conversation_history:
            role = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"{role}: {msg['content']}\n")
        return "\n".join(lines)

    def _basic_extraction(self) -> Dict[str, Any]:
        """Basic fallback extraction from conversation text."""
        conversation_text = self._format_conversation().lower()

        # Simple keyword extraction
        tech_keywords = [
            "python", "javascript", "typescript", "react", "vue", "django",
            "flask", "fastapi", "node", "express", "postgresql", "mysql",
            "mongodb", "redis", "docker", "kubernetes", "aws", "gcp", "azure"
        ]

        tech_stack = [
            tech for tech in tech_keywords
            if tech in conversation_text
        ]

        return {
            "project_name": "Extracted Project",
            "description": "Project from planning conversation",
            "requirements": ["Requirements extracted from conversation"],
            "features": [],
            "tech_stack": tech_stack,
            "constraints": [],
            "success_criteria": [],
            "deployment": "Not specified",
            "target_users": "Not specified",
            "extraction_method": "basic_fallback"
        }

    def save_conversation(self, filepath: str):
        """
        Save conversation history to file.

        Args:
            filepath: Path to save conversation JSON

        Raises:
            PlanningError: If save fails
        """
        try:
            from pathlib import Path

            data = {
                "session_metadata": self.session_metadata,
                "model": self.model,
                "conversation": self.conversation_history,
                "saved_at": datetime.now().isoformat()
            }

            Path(filepath).write_text(json.dumps(data, indent=2))
            logger.info(f"Saved conversation to {filepath}")

        except Exception as e:
            raise PlanningError(f"Failed to save conversation: {e}")

    def load_conversation(self, filepath: str):
        """
        Load conversation history from file.

        Args:
            filepath: Path to conversation JSON file

        Raises:
            PlanningError: If load fails
        """
        try:
            from pathlib import Path

            data = json.loads(Path(filepath).read_text())

            self.conversation_history = data["conversation"]
            self.session_metadata = data["session_metadata"]
            self.model = data.get("model", self.model)

            logger.info(f"Loaded conversation from {filepath}")

        except Exception as e:
            raise PlanningError(f"Failed to load conversation: {e}")

    def clear_conversation(self):
        """Clear conversation history and reset session."""
        self.conversation_history.clear()
        self.session_metadata = {
            "started_at": datetime.now().isoformat(),
            "turns": 0
        }
        logger.info("Cleared conversation history")

    def get_conversation_length(self) -> int:
        """Get number of conversation turns."""
        return len(self.conversation_history)

    def get_last_assistant_message(self) -> Optional[str]:
        """Get the last assistant message."""
        for msg in reversed(self.conversation_history):
            if msg["role"] == "assistant":
                return msg["content"]
        return None

    def get_last_user_message(self) -> Optional[str]:
        """Get the last user message."""
        for msg in reversed(self.conversation_history):
            if msg["role"] == "user":
                return msg["content"]
        return None
