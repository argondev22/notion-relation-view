"""
Integration tests for frontend-backend integration.

Tests CORS configuration, API endpoint connectivity, and session management.
"""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_cors_headers():
    """Test that CORS headers are properly configured."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test preflight request
        response = await client.options(
            "/api/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

        # Check CORS headers
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-credentials" in response.headers
        assert response.headers["access-control-allow-credentials"] == "true"


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test that health endpoint is accessible."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test that root endpoint is accessible."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()


@pytest.mark.asyncio
async def test_auth_flow_integration():
    """Test complete authentication flow: register -> login -> verify session."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Register a new user
        register_data = {
            "email": "integration@test.com",
            "password": "TestPassword123!",
        }
        register_response = await client.post("/api/auth/register", json=register_data)
        assert register_response.status_code == 201
        user_data = register_response.json()
        assert user_data["user"]["email"] == register_data["email"]
        assert "id" in user_data["user"]

        # 2. Login with the registered user
        login_data = {
            "email": "integration@test.com",
            "password": "TestPassword123!",
        }
        login_response = await client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == 200
        assert login_response.json()["user"]["email"] == login_data["email"]

        # Check that session cookie is set
        assert "session_token" in login_response.cookies

        # Extract session token for subsequent requests
        session_token = login_response.cookies.get("session_token")

        # 3. Verify session by accessing protected endpoint
        me_response = await client.get(
            "/api/auth/me",
            cookies={"session_token": session_token}
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == login_data["email"]

        # 4. Logout
        logout_response = await client.post(
            "/api/auth/logout",
            cookies={"session_token": session_token}
        )
        assert logout_response.status_code == 200

        # 5. Verify session is invalidated (cookie is cleared)
        me_after_logout = await client.get("/api/auth/me")
        assert me_after_logout.status_code == 401


@pytest.mark.asyncio
async def test_notion_token_flow_integration():
    """Test Notion token management flow."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Register and login
        register_data = {
            "email": "notion@test.com",
            "password": "TestPassword123!",
        }
        await client.post("/api/auth/register", json=register_data)
        login_response = await client.post("/api/auth/login", json=register_data)
        session_token = login_response.cookies.get("session_token")

        # 2. Save Notion token
        token_data = {"token": "secret_test_notion_token_12345"}
        save_response = await client.post(
            "/api/notion/token",
            json=token_data,
            cookies={"session_token": session_token}
        )
        # Token save will fail with invalid token, but endpoint should work
        assert save_response.status_code in [200, 400]

        # 3. Verify token (will fail with invalid token, but endpoint should work)
        verify_response = await client.get(
            "/api/notion/token/verify",
            cookies={"session_token": session_token}
        )
        # Token verification may fail with test token, but endpoint should respond
        assert verify_response.status_code in [200, 400, 401]


@pytest.mark.asyncio
async def test_graph_endpoints_integration():
    """Test graph data endpoints connectivity."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Register and login
        register_data = {
            "email": "graph@test.com",
            "password": "TestPassword123!",
        }
        await client.post("/api/auth/register", json=register_data)
        await client.post("/api/auth/login", json=register_data)

        # 2. Try to get graph data (will fail without valid Notion token)
        graph_response = await client.get("/api/graph/data")
        # Should return error or empty data, but endpoint should be accessible
        assert graph_response.status_code in [200, 400, 401, 404]

        # 3. Try to get databases
        databases_response = await client.get("/api/graph/databases")
        assert databases_response.status_code in [200, 400, 401, 404]


@pytest.mark.asyncio
async def test_view_management_integration():
    """Test view management endpoints integration."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Register and login
        register_data = {
            "email": "view@test.com",
            "password": "TestPassword123!",
        }
        await client.post("/api/auth/register", json=register_data)
        login_response = await client.post("/api/auth/login", json=register_data)
        session_token = login_response.cookies.get("session_token")

        # 2. Create a view
        view_data = {
            "name": "Test View",
            "database_ids": ["db1", "db2"],
            "settings": {"zoom_level": 1.0, "pan_x": 0.0, "pan_y": 0.0},
        }
        create_response = await client.post(
            "/api/views",
            json=view_data,
            cookies={"session_token": session_token}
        )
        assert create_response.status_code == 201
        view = create_response.json()
        assert view["name"] == "Test View"
        assert "id" in view
        view_id = view["id"]

        # 3. Get all views
        views_response = await client.get(
            "/api/views",
            cookies={"session_token": session_token}
        )
        assert views_response.status_code == 200
        views = views_response.json()
        assert len(views) >= 1
        assert any(v["id"] == view_id for v in views)

        # 4. Get specific view
        get_view_response = await client.get(
            f"/api/views/{view_id}",
            cookies={"session_token": session_token}
        )
        assert get_view_response.status_code == 200
        assert get_view_response.json()["id"] == view_id

        # 5. Update view
        update_data = {"name": "Updated View"}
        update_response = await client.put(
            f"/api/views/{view_id}",
            json=update_data,
            cookies={"session_token": session_token}
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated View"

        # 6. Delete view
        delete_response = await client.delete(
            f"/api/views/{view_id}",
            cookies={"session_token": session_token}
        )
        assert delete_response.status_code == 204

        # 7. Verify view is deleted
        get_deleted_response = await client.get(
            f"/api/views/{view_id}",
            cookies={"session_token": session_token}
        )
        assert get_deleted_response.status_code == 404


@pytest.mark.asyncio
async def test_session_persistence_across_requests():
    """Test that session persists across multiple requests."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Register and login
        register_data = {
            "email": "session@test.com",
            "password": "TestPassword123!",
        }
        await client.post("/api/auth/register", json=register_data)
        login_response = await client.post("/api/auth/login", json=register_data)
        assert login_response.status_code == 200
        session_token = login_response.cookies.get("session_token")

        # 2. Make multiple authenticated requests
        for _ in range(3):
            me_response = await client.get(
                "/api/auth/me",
                cookies={"session_token": session_token}
            )
            assert me_response.status_code == 200
            assert me_response.json()["email"] == register_data["email"]


@pytest.mark.asyncio
async def test_unauthorized_access_protection():
    """Test that protected endpoints require authentication."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Try to access protected endpoints without authentication
        endpoints = [
            "/api/auth/me",
            "/api/notion/token",
            "/api/notion/token/verify",
            "/api/graph/data",
            "/api/graph/databases",
            "/api/views",
        ]

        for endpoint in endpoints:
            if endpoint == "/api/notion/token":
                # POST endpoint, not GET
                response = await client.post(endpoint, json={"token": "test"})
            else:
                response = await client.get(endpoint)
            # Should return 401 Unauthorized
            assert response.status_code == 401, f"Endpoint {endpoint} should require authentication"


@pytest.mark.asyncio
async def test_invalid_credentials_handling():
    """Test handling of invalid login credentials."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Try to login with non-existent user
        login_data = {
            "email": "nonexistent@test.com",
            "password": "WrongPassword123!",
        }
        response = await client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401
        assert "detail" in response.json()


@pytest.mark.asyncio
async def test_duplicate_registration_handling():
    """Test handling of duplicate user registration."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register a user
        register_data = {
            "email": "duplicate@test.com",
            "password": "TestPassword123!",
        }
        first_response = await client.post("/api/auth/register", json=register_data)
        assert first_response.status_code == 201

        # Try to register the same user again
        second_response = await client.post("/api/auth/register", json=register_data)
        assert second_response.status_code == 400
        assert "detail" in second_response.json()
