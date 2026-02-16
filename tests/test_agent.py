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


class TestStreamingGeneration:
    """Test streaming answer generation."""

    @patch("agent.chromadb.PersistentClient")
    @patch("agent.Anthropic")
    def test_generate_answer_stream_yields_text(self, mock_anthropic, mock_chroma):
        """Test that streaming generator yields text chunks."""
        mock_collection = Mock()
        mock_chroma.return_value.get_collection.return_value = mock_collection

        # Mock the streaming context manager
        mock_stream = Mock()
        mock_stream.text_stream = iter(["Hello", " world", "!"])
        mock_final = Mock()
        mock_final.usage.input_tokens = 100
        mock_final.usage.output_tokens = 10
        mock_stream.get_final_message.return_value = mock_final

        mock_stream_ctx = Mock()
        mock_stream_ctx.__enter__ = Mock(return_value=mock_stream)
        mock_stream_ctx.__exit__ = Mock(return_value=False)
        mock_anthropic.return_value.messages.stream.return_value = mock_stream_ctx

        agent = NebariAgent(anthropic_api_key="test-key")

        context = [{"text": "doc content", "metadata": {"file_path": "test.md"}, "relevance": 0.8}]
        chunks = list(agent.generate_answer_stream("test query", context))

        assert chunks == ["Hello", " world", "!"]

    @patch("agent.chromadb.PersistentClient")
    @patch("agent.Anthropic")
    def test_stream_metadata_available_after_consumption(self, mock_anthropic, mock_chroma):
        """Test that metadata is available after generator is consumed."""
        mock_collection = Mock()
        mock_chroma.return_value.get_collection.return_value = mock_collection

        mock_stream = Mock()
        mock_stream.text_stream = iter(["answer text"])
        mock_final = Mock()
        mock_final.usage.input_tokens = 150
        mock_final.usage.output_tokens = 20
        mock_stream.get_final_message.return_value = mock_final

        mock_stream_ctx = Mock()
        mock_stream_ctx.__enter__ = Mock(return_value=mock_stream)
        mock_stream_ctx.__exit__ = Mock(return_value=False)
        mock_anthropic.return_value.messages.stream.return_value = mock_stream_ctx

        agent = NebariAgent(anthropic_api_key="test-key")

        context = [{"text": "doc", "metadata": {"file_path": "x.md"}, "relevance": 0.9}]
        list(agent.generate_answer_stream("q", context))

        meta = agent.get_last_stream_metadata()
        assert meta["tokens"]["input"] == 150
        assert meta["tokens"]["output"] == 20
        assert meta["tokens"]["total"] == 170
        assert "cost" in meta
        assert "llm_time" in meta
        assert "sources" in meta

    @patch("agent.chromadb.PersistentClient")
    @patch("agent.Anthropic")
    def test_get_last_stream_metadata_empty_before_streaming(self, mock_anthropic, mock_chroma):
        """Test that metadata is empty dict before any streaming."""
        mock_collection = Mock()
        mock_chroma.return_value.get_collection.return_value = mock_collection

        agent = NebariAgent(anthropic_api_key="test-key")
        assert agent.get_last_stream_metadata() == {}
