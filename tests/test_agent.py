"""Tests for RAG agent."""

from unittest.mock import Mock, patch

import pytest

from agent import NebariAgent


class TestQueryExpansion:
    """Test query expansion functionality."""

    @patch("agent.chromadb.PersistentClient")
    @patch("agent.Anthropic")
    def test_expand_architecture_query(self, mock_anthropic, mock_chroma):
        """Test architecture query expansion."""
        # Mock ChromaDB collection
        mock_collection = Mock()
        mock_chroma.return_value.get_collection.return_value = mock_collection

        agent = NebariAgent(anthropic_api_key="test-key")

        queries = agent.expand_query("Show me the Nebari architecture")

        # Should have original + variations
        assert len(queries) >= 1
        assert any("architecture" in q.lower() for q in queries)

        # Check for technical variation
        expanded = [q.lower() for q in queries]
        assert any("architecture diagram infrastructure" in q for q in expanded)

    @patch("agent.chromadb.PersistentClient")
    @patch("agent.Anthropic")
    def test_expand_deployment_query(self, mock_anthropic, mock_chroma):
        """Test deployment query expansion."""
        mock_collection = Mock()
        mock_chroma.return_value.get_collection.return_value = mock_collection

        agent = NebariAgent(anthropic_api_key="test-key")

        queries = agent.expand_query("How do I deploy on AWS?")

        # Should include AWS-specific terms
        expanded = " ".join(queries).lower()
        assert "aws" in expanded
        assert "deploy" in expanded

    @patch("agent.chromadb.PersistentClient")
    @patch("agent.Anthropic")
    def test_query_limit(self, mock_anthropic, mock_chroma):
        """Test that query expansion is limited to 3 variations."""
        mock_collection = Mock()
        mock_chroma.return_value.get_collection.return_value = mock_collection

        agent = NebariAgent(anthropic_api_key="test-key")

        queries = agent.expand_query("Show me the architecture deployment on AWS")

        # Should not exceed 3 queries
        assert len(queries) <= 3


class TestAgentInitialization:
    """Test agent initialization."""

    @patch("agent.chromadb.PersistentClient")
    @patch("agent.Anthropic")
    def test_init_with_api_key(self, mock_anthropic, mock_chroma):
        """Test initialization with API key."""
        mock_collection = Mock()
        mock_chroma.return_value.get_collection.return_value = mock_collection

        agent = NebariAgent(anthropic_api_key="test-key")

        assert agent is not None
        assert agent.conversation_history == []

    @patch("agent.chromadb.PersistentClient")
    def test_init_missing_collection(self, mock_chroma):
        """Test initialization fails with missing collection."""
        mock_chroma.return_value.get_collection.side_effect = Exception("Not found")

        with pytest.raises(ValueError, match="Collection .* not found"):
            NebariAgent(anthropic_api_key="test-key")

    def test_init_missing_api_key(self):
        """Test initialization fails without API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not found"):
                NebariAgent()
