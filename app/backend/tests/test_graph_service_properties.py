"""
Property-Based Tests for Graph Service

Feature: notion-relation-view
These tests verify universal properties that should hold across all inputs.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

from app.services.graph_service import GraphService


@pytest.fixture
def graph_service():
    """Create a GraphService instance for testing"""
    return GraphService()


# Strategy for generating page data
def page_strategy(min_pages=0, max_pages=10):
    """Generate a list of mock Notion pages"""
    return st.lists(
        st.fixed_dictionaries({
            "id": st.text(
                alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), min_codepoint=33, max_codepoint=126),
                min_size=10,
                max_size=36
            ),
            "title": st.text(min_size=0, max_size=100),
            "database_id": st.text(
                alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), min_codepoint=33, max_codepoint=126),
                min_size=10,
                max_size=36
            ),
            "properties": st.fixed_dictionaries({})
        }),
        min_size=min_pages,
        max_size=max_pages
    )


# Strategy for generating database data
def database_strategy(min_dbs=0, max_dbs=5):
    """Generate a list of mock Notion databases"""
    return st.lists(
        st.fixed_dictionaries({
            "id": st.text(
                alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), min_codepoint=33, max_codepoint=126),
                min_size=10,
                max_size=36
            ),
            "title": st.text(min_size=0, max_size=100)
        }),
        min_size=min_dbs,
        max_size=max_dbs
    )


class TestProperty5GraphStructureCompleteness:
    """
    Property 5: Graph Structure Completeness

    **Validates: Requirements 3.1, 3.2, 3.3**

    For *any* set of pages and relations, all pages are generated as nodes,
    all relations are generated as edges, and each node contains the correct title.
    """

    @pytest.mark.asyncio
    @given(pages=page_strategy(min_pages=0, max_pages=20))
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_all_pages_become_nodes(self, graph_service, pages):
        """
        Property: For any set of pages, _transform_pages_to_nodes() creates
        exactly one node per page with correct attributes.

        This ensures all pages are represented in the graph.
        """
        # Transform pages to nodes
        nodes = graph_service._transform_pages_to_nodes(pages)

        # Should have one node per page
        assert len(nodes) == len(pages)

        # Verify each node has required fields
        for i, node in enumerate(nodes):
            assert "id" in node
            assert "title" in node
            assert "databaseId" in node
            assert "x" in node
            assert "y" in node
            assert "visible" in node

            # Verify node matches corresponding page
            assert node["id"] == pages[i]["id"]
            assert node["title"] == pages[i]["title"]
            assert node["databaseId"] == pages[i]["database_id"]
            assert node["visible"] is True

            # Coordinates should be initialized to 0
            assert isinstance(node["x"], (int, float))
            assert isinstance(node["y"], (int, float))

    @pytest.mark.asyncio
    @given(
        num_pages=st.integers(min_value=2, max_value=10),
        num_relations_per_page=st.integers(min_value=0, max_value=3)
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_all_relations_become_edges(self, graph_service, num_pages, num_relations_per_page):
        """
        Property: For any set of pages with relations, _transform_relations_to_edges()
        creates exactly one edge per relation.

        This ensures all relations are represented in the graph.
        """
        # Create pages with relations
        pages = []
        expected_edge_count = 0

        for i in range(num_pages):
            page_id = f"page-{i}"
            properties = {
                "Title": {
                    "type": "title",
                    "title": [{"plain_text": f"Page {i}"}]
                }
            }

            # Add relation properties
            for j in range(num_relations_per_page):
                # Only create relations to existing pages
                target_idx = (i + j + 1) % num_pages
                target_id = f"page-{target_idx}"

                prop_name = f"Relation{j}"
                properties[prop_name] = {
                    "type": "relation",
                    "relation": [{"id": target_id}]
                }
                expected_edge_count += 1

            pages.append({
                "id": page_id,
                "title": f"Page {i}",
                "database_id": "db-1",
                "properties": properties
            })

        # Transform relations to edges
        edges = graph_service._transform_relations_to_edges(pages)

        # Should have one edge per relation
        assert len(edges) == expected_edge_count

        # Verify each edge has required fields
        for edge in edges:
            assert "id" in edge
            assert "sourceId" in edge
            assert "targetId" in edge
            assert "relationProperty" in edge
            assert "visible" in edge

            # Verify edge connects valid pages
            assert edge["sourceId"] in [p["id"] for p in pages]
            assert edge["targetId"] in [p["id"] for p in pages]
            assert edge["visible"] is True

    @pytest.mark.asyncio
    @given(databases=database_strategy(min_dbs=0, max_dbs=10))
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_all_databases_are_transformed(self, graph_service, databases):
        """
        Property: For any set of databases, _transform_databases() creates
        exactly one database object per input database.

        This ensures all databases are represented in the graph data.
        """
        # Transform databases
        result = graph_service._transform_databases(databases)

        # Should have one database object per input
        assert len(result) == len(databases)

        # Verify each database has required fields
        for i, db in enumerate(result):
            assert "id" in db
            assert "title" in db
            assert "hidden" in db

            # Verify database matches input
            assert db["id"] == databases[i]["id"]
            assert db["title"] == databases[i]["title"]
            assert db["hidden"] is False
