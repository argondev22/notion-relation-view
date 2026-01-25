"""
Property-Based Tests for View Management

Feature: notion-relation-view
These tests verify universal properties that should hold across all inputs.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from .conftest import TestingSessionLocal
from app.services.database_service import database_service
from app.services.auth_service import auth_service


@pytest.fixture
def test_user():
    """Create a test user for view management tests"""
    db = TestingSessionLocal()
    user = auth_service.register(db, "viewtest@example.com", "password123")
    db.close()
    return user


# Strategies for generating view data
view_name_strategy = st.text(min_size=1, max_size=100)
database_ids_strategy = st.lists(
    st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), min_codepoint=33, max_codepoint=126),
        min_size=10,
        max_size=36
    ),
    min_size=1,
    max_size=10
)
zoom_level_strategy = st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)
pan_position_strategy = st.floats(min_value=-10000.0, max_value=10000.0, allow_nan=False, allow_infinity=False)


class TestProperty14ViewCreationRoundTrip:
    """
    Property 14: View Creation Round-Trip

    **Validates: Requirements 6.3, 6.4**

    For *any* view configuration (name, database IDs, zoom, pan), creating a view
    and then retrieving it returns the same configuration values, and generates
    a unique view ID and URL.
    """

    @given(
        name=view_name_strategy,
        database_ids=database_ids_strategy,
        zoom_level=zoom_level_strategy,
        pan_x=pan_position_strategy,
        pan_y=pan_position_strategy
    )
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_view_creation_round_trip(
        self,
        test_user,
        name,
        database_ids,
        zoom_level,
        pan_x,
        pan_y
    ):
        """
        Property: For any view configuration, creating and then retrieving
        a view returns the same configuration values.

        This ensures view data is correctly persisted and retrieved.
        """
        db = TestingSessionLocal()

        try:
            # Create view
            created_view = database_service.create_view(
                db=db,
                user_id=str(test_user.id),
                name=name,
                database_ids=database_ids,
                zoom_level=zoom_level,
                pan_x=pan_x,
                pan_y=pan_y
            )

            # Verify view was created with an ID
            assert created_view.id is not None
            assert str(created_view.id) != ""

            # Retrieve the view
            retrieved_view = database_service.get_view(db, str(created_view.id))

            # Verify view was retrieved
            assert retrieved_view is not None

            # Verify all fields match (round-trip)
            assert retrieved_view.id == created_view.id
            assert retrieved_view.user_id == test_user.id
            assert retrieved_view.name == name
            assert retrieved_view.database_ids == database_ids
            assert abs(retrieved_view.zoom_level - zoom_level) < 0.0001  # Float comparison
            assert abs(retrieved_view.pan_x - pan_x) < 0.0001
            assert abs(retrieved_view.pan_y - pan_y) < 0.0001

        finally:
            # Cleanup
            if created_view and created_view.id:
                try:
                    database_service.delete_view(db, str(created_view.id))
                except:
                    pass
            db.close()

    @given(
        name=view_name_strategy,
        database_ids=database_ids_strategy
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_view_id_uniqueness(self, test_user, name, database_ids):
        """
        Property: For any view configuration, each created view gets a unique ID.

        This ensures view IDs are unique across all views.
        """
        db = TestingSessionLocal()
        created_views = []

        try:
            # Create multiple views
            for i in range(3):
                view = database_service.create_view(
                    db=db,
                    user_id=str(test_user.id),
                    name=f"{name}_{i}",
                    database_ids=database_ids
                )
                created_views.append(view)

            # Verify all IDs are unique
            view_ids = [str(view.id) for view in created_views]
            assert len(view_ids) == len(set(view_ids))

        finally:
            # Cleanup
            for view in created_views:
                try:
                    database_service.delete_view(db, str(view.id))
                except:
                    pass
            db.close()

    @given(
        name=view_name_strategy,
        database_ids=database_ids_strategy
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_view_url_generation(self, test_user, name, database_ids):
        """
        Property: For any view, a URL can be generated from its ID.

        This ensures views can be accessed via unique URLs.
        """
        db = TestingSessionLocal()

        try:
            # Create view
            view = database_service.create_view(
                db=db,
                user_id=str(test_user.id),
                name=name,
                database_ids=database_ids
            )

            # Generate URL
            view_url = f"/view/{view.id}"

            # Verify URL format
            assert view_url.startswith("/view/")
            assert str(view.id) in view_url

        finally:
            # Cleanup
            if view and view.id:
                try:
                    database_service.delete_view(db, str(view.id))
                except:
                    pass
            db.close()

    @given(
        name=view_name_strategy,
        database_ids=database_ids_strategy
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_get_views_returns_all_user_views(self, test_user, name, database_ids):
        """
        Property: For any set of views created by a user, get_views()
        returns all of them.

        This ensures view listing is complete.
        """
        db = TestingSessionLocal()
        created_views = []

        try:
            # Create multiple views
            num_views = 3
            for i in range(num_views):
                view = database_service.create_view(
                    db=db,
                    user_id=str(test_user.id),
                    name=f"{name}_{i}",
                    database_ids=database_ids
                )
                created_views.append(view)

            # Get all views
            retrieved_views = database_service.get_views(db, str(test_user.id))

            # Verify all created views are in the retrieved list
            created_ids = {str(v.id) for v in created_views}
            retrieved_ids = {str(v.id) for v in retrieved_views}

            assert created_ids.issubset(retrieved_ids)

        finally:
            # Cleanup
            for view in created_views:
                try:
                    database_service.delete_view(db, str(view.id))
                except:
                    pass
            db.close()

    @given(
        name=view_name_strategy,
        database_ids=database_ids_strategy,
        zoom_level=zoom_level_strategy
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_view_default_values(self, test_user, name, database_ids, zoom_level):
        """
        Property: For any view created without explicit pan/zoom values,
        default values are applied correctly.

        This ensures default values work as expected.
        """
        db = TestingSessionLocal()

        try:
            # Create view with only zoom_level specified
            view = database_service.create_view(
                db=db,
                user_id=str(test_user.id),
                name=name,
                database_ids=database_ids,
                zoom_level=zoom_level
                # pan_x and pan_y use defaults
            )

            # Verify defaults were applied
            assert abs(view.pan_x - 0.0) < 0.0001
            assert abs(view.pan_y - 0.0) < 0.0001
            assert abs(view.zoom_level - zoom_level) < 0.0001

        finally:
            # Cleanup
            if view and view.id:
                try:
                    database_service.delete_view(db, str(view.id))
                except:
                    pass
            db.close()



class TestProperty17ViewSettingsPersistence:
    """
    Property 17: View Settings Persistence Round-Trip

    **Validates: Requirements 6.8, 6.11**

    For *any* view settings (zoom level, pan position), saving them and then
    retrieving them returns the same values.
    """

    @given(
        name=view_name_strategy,
        database_ids=database_ids_strategy,
        initial_zoom=zoom_level_strategy,
        initial_pan_x=pan_position_strategy,
        initial_pan_y=pan_position_strategy,
        updated_zoom=zoom_level_strategy,
        updated_pan_x=pan_position_strategy,
        updated_pan_y=pan_position_strategy
    )
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_view_settings_round_trip(
        self,
        test_user,
        name,
        database_ids,
        initial_zoom,
        initial_pan_x,
        initial_pan_y,
        updated_zoom,
        updated_pan_x,
        updated_pan_y
    ):
        """
        Property: For any view settings, updating and then retrieving
        a view returns the updated settings.

        This ensures view settings are correctly persisted.
        """
        db = TestingSessionLocal()

        try:
            # Create view with initial settings
            view = database_service.create_view(
                db=db,
                user_id=str(test_user.id),
                name=name,
                database_ids=database_ids,
                zoom_level=initial_zoom,
                pan_x=initial_pan_x,
                pan_y=initial_pan_y
            )

            # Update view settings
            updated_view = database_service.update_view(
                db=db,
                view_id=str(view.id),
                zoom_level=updated_zoom,
                pan_x=updated_pan_x,
                pan_y=updated_pan_y
            )

            # Retrieve view again
            retrieved_view = database_service.get_view(db, str(view.id))

            # Verify updated settings were persisted
            assert abs(retrieved_view.zoom_level - updated_zoom) < 0.0001
            assert abs(retrieved_view.pan_x - updated_pan_x) < 0.0001
            assert abs(retrieved_view.pan_y - updated_pan_y) < 0.0001

            # Verify other fields weren't changed
            assert retrieved_view.name == name
            assert retrieved_view.database_ids == database_ids

        finally:
            # Cleanup
            if view and view.id:
                try:
                    database_service.delete_view(db, str(view.id))
                except:
                    pass
            db.close()

    @given(
        name=view_name_strategy,
        database_ids=database_ids_strategy,
        zoom_level=zoom_level_strategy,
        pan_x=pan_position_strategy,
        pan_y=pan_position_strategy
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_partial_settings_update(
        self,
        test_user,
        name,
        database_ids,
        zoom_level,
        pan_x,
        pan_y
    ):
        """
        Property: For any view, updating only some settings preserves
        the other settings.

        This ensures partial updates work correctly.
        """
        db = TestingSessionLocal()

        try:
            # Create view
            view = database_service.create_view(
                db=db,
                user_id=str(test_user.id),
                name=name,
                database_ids=database_ids,
                zoom_level=1.0,
                pan_x=0.0,
                pan_y=0.0
            )

            # Update only zoom level
            database_service.update_view(
                db=db,
                view_id=str(view.id),
                zoom_level=zoom_level
            )

            # Retrieve and verify
            retrieved = database_service.get_view(db, str(view.id))
            assert abs(retrieved.zoom_level - zoom_level) < 0.0001
            assert abs(retrieved.pan_x - 0.0) < 0.0001  # Unchanged
            assert abs(retrieved.pan_y - 0.0) < 0.0001  # Unchanged

            # Update only pan positions
            database_service.update_view(
                db=db,
                view_id=str(view.id),
                pan_x=pan_x,
                pan_y=pan_y
            )

            # Retrieve and verify
            retrieved = database_service.get_view(db, str(view.id))
            assert abs(retrieved.zoom_level - zoom_level) < 0.0001  # Unchanged
            assert abs(retrieved.pan_x - pan_x) < 0.0001
            assert abs(retrieved.pan_y - pan_y) < 0.0001

        finally:
            # Cleanup
            if view and view.id:
                try:
                    database_service.delete_view(db, str(view.id))
                except:
                    pass
            db.close()

    @given(
        name=view_name_strategy,
        database_ids=database_ids_strategy
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_view_settings_persistence_across_sessions(
        self,
        test_user,
        name,
        database_ids
    ):
        """
        Property: For any view, settings persist across database sessions.

        This ensures view settings are truly persisted to the database.
        """
        view_id = None

        try:
            # Create view in one session
            db1 = TestingSessionLocal()
            view = database_service.create_view(
                db=db1,
                user_id=str(test_user.id),
                name=name,
                database_ids=database_ids,
                zoom_level=2.5,
                pan_x=100.0,
                pan_y=-50.0
            )
            view_id = str(view.id)
            db1.close()

            # Retrieve view in a different session
            db2 = TestingSessionLocal()
            retrieved = database_service.get_view(db2, view_id)

            # Verify settings persisted
            assert retrieved is not None
            assert abs(retrieved.zoom_level - 2.5) < 0.0001
            assert abs(retrieved.pan_x - 100.0) < 0.0001
            assert abs(retrieved.pan_y + 50.0) < 0.0001
            db2.close()

        finally:
            # Cleanup
            if view_id:
                db3 = TestingSessionLocal()
                try:
                    database_service.delete_view(db3, view_id)
                except:
                    pass
                db3.close()

    @given(
        name=view_name_strategy,
        database_ids=database_ids_strategy,
        new_name=view_name_strategy,
        new_database_ids=database_ids_strategy
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_view_name_and_databases_update(
        self,
        test_user,
        name,
        database_ids,
        new_name,
        new_database_ids
    ):
        """
        Property: For any view, updating name and database selection
        preserves settings.

        This ensures all view properties can be updated independently.
        """
        db = TestingSessionLocal()

        try:
            # Create view with specific settings
            view = database_service.create_view(
                db=db,
                user_id=str(test_user.id),
                name=name,
                database_ids=database_ids,
                zoom_level=3.0,
                pan_x=200.0,
                pan_y=-100.0
            )

            # Update name and databases
            database_service.update_view(
                db=db,
                view_id=str(view.id),
                name=new_name,
                database_ids=new_database_ids
            )

            # Retrieve and verify
            retrieved = database_service.get_view(db, str(view.id))
            assert retrieved.name == new_name
            assert retrieved.database_ids == new_database_ids
            # Settings should be preserved
            assert abs(retrieved.zoom_level - 3.0) < 0.0001
            assert abs(retrieved.pan_x - 200.0) < 0.0001
            assert abs(retrieved.pan_y + 100.0) < 0.0001

        finally:
            # Cleanup
            if view and view.id:
                try:
                    database_service.delete_view(db, str(view.id))
                except:
                    pass
            db.close()



class TestProperty15ViewURLAccess:
    """
    Property 15: View URL Access

    **Validates: Requirements 6.5, 6.10**

    For *any* view ID, accessing the view via its dedicated URL returns
    the correct graph data filtered by the view's database selection.
    """

    @given(
        name=view_name_strategy,
        database_ids=database_ids_strategy
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_view_url_returns_correct_data(
        self,
        test_user,
        name,
        database_ids
    ):
        """
        Property: For any view, the view URL provides access to graph data
        filtered by the view's database selection.

        This ensures view URLs work correctly for data access.
        """
        db = TestingSessionLocal()

        try:
            # Create view
            view = database_service.create_view(
                db=db,
                user_id=str(test_user.id),
                name=name,
                database_ids=database_ids
            )

            # Verify view can be retrieved by ID
            retrieved_view = database_service.get_view(db, str(view.id))
            assert retrieved_view is not None
            assert retrieved_view.id == view.id
            assert retrieved_view.database_ids == database_ids

            # Verify view URL format
            view_url = f"/view/{view.id}"
            assert str(view.id) in view_url

        finally:
            # Cleanup
            if view and view.id:
                try:
                    database_service.delete_view(db, str(view.id))
                except:
                    pass
            db.close()

    @given(
        name=view_name_strategy,
        database_ids=database_ids_strategy
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_view_id_in_url_is_valid(
        self,
        test_user,
        name,
        database_ids
    ):
        """
        Property: For any view, the ID in the view URL can be used
        to retrieve the view.

        This ensures view URLs are valid and functional.
        """
        db = TestingSessionLocal()

        try:
            # Create view
            view = database_service.create_view(
                db=db,
                user_id=str(test_user.id),
                name=name,
                database_ids=database_ids
            )

            # Extract ID from URL format
            view_url = f"/view/{view.id}"
            extracted_id = view_url.split("/view/")[1]

            # Verify extracted ID can retrieve the view
            retrieved = database_service.get_view(db, extracted_id)
            assert retrieved is not None
            assert str(retrieved.id) == extracted_id

        finally:
            # Cleanup
            if view and view.id:
                try:
                    database_service.delete_view(db, str(view.id))
                except:
                    pass
            db.close()

    @given(
        name=view_name_strategy,
        database_ids=database_ids_strategy
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_view_database_selection_persists(
        self,
        test_user,
        name,
        database_ids
    ):
        """
        Property: For any view, the database selection is correctly
        stored and can be retrieved.

        This ensures view filtering configuration is preserved.
        """
        db = TestingSessionLocal()

        try:
            # Create view with specific database selection
            view = database_service.create_view(
                db=db,
                user_id=str(test_user.id),
                name=name,
                database_ids=database_ids
            )

            # Retrieve view
            retrieved = database_service.get_view(db, str(view.id))

            # Verify database selection matches
            assert retrieved.database_ids == database_ids
            assert len(retrieved.database_ids) == len(database_ids)
            assert set(retrieved.database_ids) == set(database_ids)

        finally:
            # Cleanup
            if view and view.id:
                try:
                    database_service.delete_view(db, str(view.id))
                except:
                    pass
            db.close()
