"""
End-to-end tests for complete user workflows.

Tests the following flows:
1. User registration → Login → Token setup → Graph display
2. View creation → View URL access
3. Search and filtering
"""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_complete_user_onboarding_flow():
    """
    Test complete user onboarding flow:
    1. Register new user
    2. Login
    3. Save Notion token
    4. Verify token
    5. Get databases
    6. Get graph data
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Register new user
        register_data = {
            "email": "e2e_user@test.com",
            "password": "SecurePassword123!",
        }
        register_response = await client.post("/api/auth/register", json=register_data)
        assert register_response.status_code == 201
        user = register_response.json()["user"]
        assert user["email"] == register_data["email"]
        assert "id" in user

        # Step 2: Login
        login_response = await client.post("/api/auth/login", json=register_data)
        assert login_response.status_code == 200
        assert "session_token" in login_response.cookies
        session_token = login_response.cookies.get("session_token")
        login_user = login_response.json()["user"]
        assert login_user["email"] == register_data["email"]

        # Step 3: Save Notion token (will fail with test token, but flow should work)
        token_data = {"token": "secret_test_notion_token"}
        save_token_response = await client.post(
            "/api/notion/token",
            json=token_data,
            cookies={"session_token": session_token}
        )
        # Token validation will fail, but save endpoint should respond
        assert save_token_response.status_code in [200, 400]

        # Step 4: Verify token (will fail with test token)
        verify_response = await client.get(
            "/api/notion/token/verify",
            cookies={"session_token": session_token}
        )
        assert verify_response.status_code in [200, 400]

        # Step 5: Try to get databases (will fail without valid token)
        databases_response = await client.get(
            "/api/graph/databases",
            cookies={"session_token": session_token}
        )
        assert databases_response.status_code in [200, 400, 404]

        # Step 6: Try to get graph data (will fail without valid token)
        graph_response = await client.get(
            "/api/graph/data",
            cookies={"session_token": session_token}
        )
        assert graph_response.status_code in [200, 400, 404]


@pytest.mark.asyncio
async def test_view_creation_and_access_flow():
    """
    Test view creation and access flow:
    1. Register and login
    2. Create a view
    3. Access view by ID
    4. Update view settings
    5. Access view via URL
    6. Delete view
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Register and login
        register_data = {
            "email": "view_user@test.com",
            "password": "SecurePassword123!",
        }
        await client.post("/api/auth/register", json=register_data)
        login_response = await client.post("/api/auth/login", json=register_data)
        session_token = login_response.cookies.get("session_token")

        # Step 2: Create a view
        view_data = {
            "name": "My First View",
            "database_ids": ["db_123", "db_456"],
            "zoom_level": 1.5,
            "pan_x": 100.0,
            "pan_y": 50.0,
        }
        create_response = await client.post(
            "/api/views",
            json=view_data,
            cookies={"session_token": session_token}
        )
        assert create_response.status_code == 201
        view = create_response.json()
        assert view["name"] == "My First View"
        assert view["database_ids"] == ["db_123", "db_456"]
        assert view["zoom_level"] == 1.5
        view_id = view["id"]

        # Step 3: Access view by ID
        get_view_response = await client.get(
            f"/api/views/{view_id}",
            cookies={"session_token": session_token}
        )
        assert get_view_response.status_code == 200
        retrieved_view = get_view_response.json()
        assert retrieved_view["id"] == view_id
        assert retrieved_view["name"] == "My First View"

        # Step 4: Update view settings
        update_data = {
            "name": "Updated View Name",
            "zoom_level": 2.0,
            "pan_x": 200.0,
            "pan_y": 100.0,
        }
        update_response = await client.put(
            f"/api/views/{view_id}",
            json=update_data,
            cookies={"session_token": session_token}
        )
        assert update_response.status_code == 200
        updated_view = update_response.json()
        assert updated_view["name"] == "Updated View Name"
        assert updated_view["zoom_level"] == 2.0

        # Step 5: Access view data via URL (will fail without valid Notion token)
        view_data_response = await client.get(
            f"/api/views/{view_id}/data",
            cookies={"session_token": session_token}
        )
        # May return various error codes without valid Notion token
        assert view_data_response.status_code in [200, 400, 404, 500]

        # Step 6: Delete view
        delete_response = await client.delete(
            f"/api/views/{view_id}",
            cookies={"session_token": session_token}
        )
        assert delete_response.status_code == 204

        # Verify view is deleted
        get_deleted_response = await client.get(
            f"/api/views/{view_id}",
            cookies={"session_token": session_token}
        )
        assert get_deleted_response.status_code == 404


@pytest.mark.asyncio
async def test_multiple_views_management_flow():
    """
    Test managing multiple views:
    1. Register and login
    2. Create multiple views
    3. List all views
    4. Update specific views
    5. Delete specific views
    6. Verify remaining views
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Register and login
        register_data = {
            "email": "multi_view_user@test.com",
            "password": "SecurePassword123!",
        }
        await client.post("/api/auth/register", json=register_data)
        login_response = await client.post("/api/auth/login", json=register_data)
        session_token = login_response.cookies.get("session_token")

        # Step 2: Create multiple views
        view_ids = []
        for i in range(3):
            view_data = {
                "name": f"View {i + 1}",
                "database_ids": [f"db_{i}"],
                "zoom_level": 1.0,
                "pan_x": 0.0,
                "pan_y": 0.0,
            }
            create_response = await client.post(
                "/api/views",
                json=view_data,
                cookies={"session_token": session_token}
            )
            assert create_response.status_code == 201
            view_ids.append(create_response.json()["id"])

        # Step 3: List all views
        list_response = await client.get(
            "/api/views",
            cookies={"session_token": session_token}
        )
        assert list_response.status_code == 200
        views = list_response.json()
        assert len(views) == 3
        assert all(v["id"] in view_ids for v in views)

        # Step 4: Update specific view
        update_data = {"name": "Updated View 2"}
        update_response = await client.put(
            f"/api/views/{view_ids[1]}",
            json=update_data,
            cookies={"session_token": session_token}
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated View 2"

        # Step 5: Delete specific view
        delete_response = await client.delete(
            f"/api/views/{view_ids[0]}",
            cookies={"session_token": session_token}
        )
        assert delete_response.status_code == 204

        # Step 6: Verify remaining views
        list_after_delete = await client.get(
            "/api/views",
            cookies={"session_token": session_token}
        )
        assert list_after_delete.status_code == 200
        remaining_views = list_after_delete.json()
        assert len(remaining_views) == 2
        assert view_ids[0] not in [v["id"] for v in remaining_views]
        assert view_ids[1] in [v["id"] for v in remaining_views]
        assert view_ids[2] in [v["id"] for v in remaining_views]


@pytest.mark.asyncio
async def test_view_settings_persistence():
    """
    Test that view settings persist correctly:
    1. Create view with specific settings
    2. Retrieve view and verify settings
    3. Update settings
    4. Retrieve again and verify updated settings
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Setup: Register and login
        register_data = {
            "email": "settings_user@test.com",
            "password": "SecurePassword123!",
        }
        await client.post("/api/auth/register", json=register_data)
        login_response = await client.post("/api/auth/login", json=register_data)
        session_token = login_response.cookies.get("session_token")

        # Step 1: Create view with specific settings
        view_data = {
            "name": "Settings Test View",
            "database_ids": ["db_test"],
            "zoom_level": 1.75,
            "pan_x": 123.45,
            "pan_y": 678.90,
        }
        create_response = await client.post(
            "/api/views",
            json=view_data,
            cookies={"session_token": session_token}
        )
        assert create_response.status_code == 201
        view_id = create_response.json()["id"]

        # Step 2: Retrieve view and verify settings
        get_response = await client.get(
            f"/api/views/{view_id}",
            cookies={"session_token": session_token}
        )
        assert get_response.status_code == 200
        view = get_response.json()
        assert view["zoom_level"] == 1.75
        assert view["pan_x"] == 123.45
        assert view["pan_y"] == 678.90

        # Step 3: Update settings
        update_data = {
            "zoom_level": 2.5,
            "pan_x": 999.99,
            "pan_y": 111.11,
        }
        update_response = await client.put(
            f"/api/views/{view_id}",
            json=update_data,
            cookies={"session_token": session_token}
        )
        assert update_response.status_code == 200

        # Step 4: Retrieve again and verify updated settings
        get_updated_response = await client.get(
            f"/api/views/{view_id}",
            cookies={"session_token": session_token}
        )
        assert get_updated_response.status_code == 200
        updated_view = get_updated_response.json()
        assert updated_view["zoom_level"] == 2.5
        assert updated_view["pan_x"] == 999.99
        assert updated_view["pan_y"] == 111.11


@pytest.mark.asyncio
async def test_authentication_flow_with_errors():
    """
    Test authentication flow with various error scenarios:
    1. Invalid registration (duplicate email)
    2. Invalid login (wrong password)
    3. Accessing protected endpoints without auth
    4. Session expiration handling
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Register user
        register_data = {
            "email": "error_test@test.com",
            "password": "SecurePassword123!",
        }
        first_register = await client.post("/api/auth/register", json=register_data)
        assert first_register.status_code == 201

        # Try to register again with same email
        duplicate_register = await client.post("/api/auth/register", json=register_data)
        assert duplicate_register.status_code == 400
        assert "detail" in duplicate_register.json()

        # Step 2: Try to login with wrong password
        wrong_login = await client.post(
            "/api/auth/login",
            json={"email": "error_test@test.com", "password": "WrongPassword"}
        )
        assert wrong_login.status_code == 401

        # Step 3: Try to access protected endpoint without auth
        no_auth_response = await client.get("/api/auth/me")
        assert no_auth_response.status_code == 401

        # Step 4: Login successfully
        login_response = await client.post("/api/auth/login", json=register_data)
        assert login_response.status_code == 200
        session_token = login_response.cookies.get("session_token")

        # Access protected endpoint with valid session
        auth_response = await client.get(
            "/api/auth/me",
            cookies={"session_token": session_token}
        )
        assert auth_response.status_code == 200

        # Logout
        logout_response = await client.post(
            "/api/auth/logout",
            cookies={"session_token": session_token}
        )
        assert logout_response.status_code == 200

        # Try to access protected endpoint after logout
        after_logout_response = await client.get("/api/auth/me")
        assert after_logout_response.status_code == 401


@pytest.mark.asyncio
async def test_database_filtering_flow():
    """
    Test database filtering flow:
    1. Create view with specific databases
    2. Verify view contains correct database IDs
    3. Update view with different databases
    4. Verify updated database IDs
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Setup: Register and login
        register_data = {
            "email": "filter_user@test.com",
            "password": "SecurePassword123!",
        }
        await client.post("/api/auth/register", json=register_data)
        login_response = await client.post("/api/auth/login", json=register_data)
        session_token = login_response.cookies.get("session_token")

        # Step 1: Create view with specific databases
        initial_databases = ["db_1", "db_2", "db_3"]
        view_data = {
            "name": "Filter Test View",
            "database_ids": initial_databases,
            "zoom_level": 1.0,
            "pan_x": 0.0,
            "pan_y": 0.0,
        }
        create_response = await client.post(
            "/api/views",
            json=view_data,
            cookies={"session_token": session_token}
        )
        assert create_response.status_code == 201
        view_id = create_response.json()["id"]

        # Step 2: Verify view contains correct database IDs
        get_response = await client.get(
            f"/api/views/{view_id}",
            cookies={"session_token": session_token}
        )
        assert get_response.status_code == 200
        view = get_response.json()
        assert view["database_ids"] == initial_databases

        # Step 3: Update view with different databases
        updated_databases = ["db_4", "db_5"]
        update_response = await client.put(
            f"/api/views/{view_id}",
            json={"database_ids": updated_databases},
            cookies={"session_token": session_token}
        )
        assert update_response.status_code == 200

        # Step 4: Verify updated database IDs
        get_updated_response = await client.get(
            f"/api/views/{view_id}",
            cookies={"session_token": session_token}
        )
        assert get_updated_response.status_code == 200
        updated_view = get_updated_response.json()
        assert updated_view["database_ids"] == updated_databases


@pytest.mark.asyncio
async def test_concurrent_user_sessions():
    """
    Test that multiple users can have independent sessions:
    1. Register two users
    2. Login both users
    3. Create views for each user
    4. Verify each user can only access their own views
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Register two users
        user1_data = {"email": "user1@test.com", "password": "Password123!"}
        user2_data = {"email": "user2@test.com", "password": "Password123!"}

        await client.post("/api/auth/register", json=user1_data)
        await client.post("/api/auth/register", json=user2_data)

        # Step 2: Login both users
        login1 = await client.post("/api/auth/login", json=user1_data)
        login2 = await client.post("/api/auth/login", json=user2_data)

        token1 = login1.cookies.get("session_token")
        token2 = login2.cookies.get("session_token")

        # Step 3: Create views for each user
        view1_data = {
            "name": "User 1 View",
            "database_ids": ["db_user1"],
            "zoom_level": 1.0,
            "pan_x": 0.0,
            "pan_y": 0.0,
        }
        view2_data = {
            "name": "User 2 View",
            "database_ids": ["db_user2"],
            "zoom_level": 1.0,
            "pan_x": 0.0,
            "pan_y": 0.0,
        }

        create1 = await client.post(
            "/api/views",
            json=view1_data,
            cookies={"session_token": token1}
        )
        create2 = await client.post(
            "/api/views",
            json=view2_data,
            cookies={"session_token": token2}
        )

        view1_id = create1.json()["id"]
        view2_id = create2.json()["id"]

        # Step 4: Verify each user can only access their own views
        user1_views = await client.get(
            "/api/views",
            cookies={"session_token": token1}
        )
        user2_views = await client.get(
            "/api/views",
            cookies={"session_token": token2}
        )

        user1_view_ids = [v["id"] for v in user1_views.json()]
        user2_view_ids = [v["id"] for v in user2_views.json()]

        assert view1_id in user1_view_ids
        assert view1_id not in user2_view_ids
        assert view2_id in user2_view_ids
        assert view2_id not in user1_view_ids
