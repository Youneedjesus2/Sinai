from unittest.mock import MagicMock, patch

from src.services.retrieval_service import RetrievalService


def _make_node(content: str, score: float, file_name: str = 'sample.md') -> MagicMock:
    node = MagicMock()
    node.score = score
    node.node.get_content.return_value = content
    node.node.metadata = {'file_name': file_name}
    return node


def _patch_vector_store(nodes: list) -> MagicMock:
    mock_client = MagicMock()
    mock_index = MagicMock()
    mock_client.get_or_create_index.return_value = mock_index
    mock_client.query.return_value = nodes
    return mock_client


def test_retrieve_returns_context_found_when_confidence_is_high():
    nodes = [
        _make_node('We offer personal care services.', score=0.85),
        _make_node('Consultations are available Mon–Fri.', score=0.80),
    ]

    with patch('src.services.retrieval_service.VectorStoreClient', return_value=_patch_vector_store(nodes)):
        result = RetrievalService().retrieve('What services do you offer?', agency_id='agency-1')

    assert result.context_found is True
    assert result.confidence_score == 0.825
    assert len(result.context_chunks) == 2
    assert len(result.sources) == 2


def test_retrieve_returns_context_not_found_when_confidence_is_low():
    nodes = [
        _make_node('Marginally related content.', score=0.40),
        _make_node('Another weak match.', score=0.35),
    ]

    with patch('src.services.retrieval_service.VectorStoreClient', return_value=_patch_vector_store(nodes)):
        result = RetrievalService().retrieve('Something obscure', agency_id='agency-1')

    assert result.context_found is False
    assert result.confidence_score == 0.375
    assert result.context_chunks == []


def test_retrieve_returns_context_not_found_when_no_nodes_returned():
    with patch('src.services.retrieval_service.VectorStoreClient', return_value=_patch_vector_store([])):
        result = RetrievalService().retrieve('Any question', agency_id='agency-1')

    assert result.context_found is False
    assert result.confidence_score == 0.0
    assert result.context_chunks == []
    assert result.sources == []


def test_retrieve_returns_safe_result_when_vector_store_raises():
    mock_client = MagicMock()
    mock_client.get_or_create_index.side_effect = Exception('DB connection failed')

    with patch('src.services.retrieval_service.VectorStoreClient', return_value=mock_client):
        result = RetrievalService().retrieve('Any question', agency_id='agency-1')

    assert result.context_found is False
    assert result.confidence_score == 0.0
    assert result.context_chunks == []
