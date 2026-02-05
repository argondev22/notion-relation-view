"""
Unit tests for response metadata models.

Tests cover:
- GraphMetadata model validation
- GraphDataResponse model with metadata
- FailedDatabase model validation
"""
import pytest
from pydantic import ValidationError
from app.routers.views import GraphMetadata, GraphDataResponse, FailedDatabase


class TestResponseMetadataModels:
    """Tests for response metadata Pydantic models"""

    def test_failed_database_model(self):
        """
        Test FailedDatabase model creation and validation.

        Validates: Requirements 3.4, 3.5
        """
        failed_db = FailedDatabase(
            id="db-123",
            title="Test Database",
            error="Connection timeout"
        )

        assert failed_db.id == "db-123"
        assert failed_db.title == "Test Database"
        assert failed_db.error == "Connection timeout"

    def test_failed_database_missing_fields(self):
        """
        Test FailedDatabase model requires all fields.

        Validates: Requirements 3.4, 3.5
        """
        with pytest.raises(ValidationError):
            FailedDatabase(id="db-123", title="Test Database")

    def test_graph_metadata_model(self):
        """
        Test GraphMetadata model creation with all fields.

        Validates: Requirements 3.4, 3.5
        """
        metadata = GraphMetadata(
            total_databases=5,
            successful_databases=4,
            failed_databases=[
                FailedDatabase(
                    id="db-failed",
                    title="Failed DB",
                    error="Timeout"
                )
            ],
            fetched_at="2024-01-15T10:30:00Z",
            from_cache=False
        )

        assert metadata.total_databases == 5
        assert metadata.successful_databases == 4
        assert len(metadata.failed_databases) == 1
        assert metadata.failed_databases[0].id == "db-failed"
        assert metadata.fetched_at == "2024-01-15T10:30:00Z"
        assert metadata.from_cache is False

    def test_graph_metadata_default_from_cache(self):
        """
        Test GraphMetadata model has default from_cache=False.

        Validates: Requirements 3.4, 3.5
        """
        metadata = GraphMetadata(
            total_databases=3,
            successful_databases=3,
            failed_databases=[],
            fetched_at="2024-01-15T10:30:00Z"
        )

        assert metadata.from_cache is False

    def test_graph_metadata_empty_failed_databases(self):
        """
        Test GraphMetadata model with no failed databases.

        Validates: Requirements 3.4, 3.5
        """
        metadata = GraphMetadata(
            total_databases=3,
            successful_databases=3,
            failed_databases=[],
            fetched_at="2024-01-15T10:30:00Z",
            from_cache=True
        )

        assert len(metadata.failed_databases) == 0
        assert metadata.from_cache is True

    def test_graph_data_response_without_metadata(self):
        """
        Test GraphDataResponse model without metadata (backward compatibility).

        Validates: Requirements 3.4, 3.5
        """
        response = GraphDataResponse(
            nodes=[{"id": "node-1", "title": "Test Node"}],
            edges=[{"sourceId": "node-1", "targetId": "node-2"}],
            databases=[{"id": "db-1", "title": "Test DB"}]
        )

        assert len(response.nodes) == 1
        assert len(response.edges) == 1
        assert len(response.databases) == 1
        assert response.metadata is None

    def test_graph_data_response_with_metadata(self):
        """
        Test GraphDataResponse model with metadata.

        Validates: Requirements 3.4, 3.5
        """
        metadata = GraphMetadata(
            total_databases=2,
            successful_databases=2,
            failed_databases=[],
            fetched_at="2024-01-15T10:30:00Z",
            from_cache=False
        )

        response = GraphDataResponse(
            nodes=[{"id": "node-1", "title": "Test Node"}],
            edges=[],
            databases=[{"id": "db-1", "title": "Test DB"}],
            metadata=metadata
        )

        assert response.metadata is not None
        assert response.metadata.total_databases == 2
        assert response.metadata.successful_databases == 2
        assert response.metadata.from_cache is False

    def test_graph_data_response_with_failed_databases(self):
        """
        Test GraphDataResponse model with failed databases in metadata.

        Validates: Requirements 3.4, 3.5
        """
        metadata = GraphMetadata(
            total_databases=3,
            successful_databases=2,
            failed_databases=[
                FailedDatabase(
                    id="db-failed-1",
                    title="Failed Database 1",
                    error="Network timeout"
                ),
                FailedDatabase(
                    id="db-failed-2",
                    title="Failed Database 2",
                    error="Permission denied"
                )
            ],
            fetched_at="2024-01-15T10:30:00Z",
            from_cache=False
        )

        response = GraphDataResponse(
            nodes=[{"id": "node-1"}],
            edges=[],
            databases=[{"id": "db-1"}],
            metadata=metadata
        )

        assert response.metadata is not None
        assert len(response.metadata.failed_databases) == 2
        assert response.metadata.failed_databases[0].error == "Network timeout"
        assert response.metadata.failed_databases[1].error == "Permission denied"

    def test_graph_data_response_empty_collections(self):
        """
        Test GraphDataResponse model with empty nodes, edges, and databases.

        Validates: Requirements 3.4, 3.5
        """
        metadata = GraphMetadata(
            total_databases=0,
            successful_databases=0,
            failed_databases=[],
            fetched_at="2024-01-15T10:30:00Z"
        )

        response = GraphDataResponse(
            nodes=[],
            edges=[],
            databases=[],
            metadata=metadata
        )

        assert len(response.nodes) == 0
        assert len(response.edges) == 0
        assert len(response.databases) == 0
        assert response.metadata.total_databases == 0
