# Design Document: View Loading Fix

## Overview

This design addresses three critical issues preventing views from loading in the Notion Relation View application:

1. **DateTime Timezone Mismatch**: The cache_manager.py uses `datetime.utcnow()` which returns timezone-naive datetime objects, but the PostgreSQL column is defined as `DateTime(timezone=True)` which expects timezone-aware objects. This causes comparison failures.

2. **Notion API Reliability**: When fetching data from multiple databases with many pages, requests timeout or fail. Currently, a single database failure causes the entire operation to fail, and there's no retry logic for transient errors.

3. **Poor User Feedback**: Users see only a loading spinner with no progress indication, partial results, or error details when operations take a long time or fail.

The solution implements timezone-aware datetime handling, robust retry logic with exponential backoff, progressive data loading, and enhanced user feedback mechanisms.

## Architecture

### Current Architecture

```
Frontend (ViewPage.tsx)
    ↓ HTTP Request
View Endpoint (/api/views/{id}/data)
    ↓
Graph Service (get_graph_data)
    ↓
Cache Manager (get_graph_data) → Returns cached data or None
    ↓ (if cache miss)
Graph Service (_fetch_and_transform_data)
    ↓
Notion Client (get_databases, get_pages)
    ↓ HTTP Requests
Notion API
```

### Enhanced Architecture

```
Frontend (ViewPage.tsx)
    ↓ HTTP Request (with progress streaming)
View Endpoint (/api/views/{id}/data)
    ↓
Graph Service (get_graph_data_progressive)
    ↓
Cache Manager (get_graph_data_by_database) → Returns per-database cached data
    ↓ (for cache misses)
Graph Service (_fetch_and_transform_data_progressive)
    ↓
Notion Client with Retry Wrapper (get_databases, get_pages_with_retry)
    ↓ HTTP Requests with exponential backoff
Notion API
```

Key architectural changes:
- Per-database caching instead of monolithic cache
- Retry wrapper around Notion API calls
- Progressive data streaming to frontend
- Timezone-aware datetime handling throughout

## Components and Interfaces

### 1. Cache Manager Enhancements

**File**: `app/backend/app/services/cache_manager.py`

**Changes**:
- Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`
- Add per-database cache storage
- Implement cache merging for partial updates

**New Methods**:

```python
async def cache_database_data(
    self,
    db: Session,
    user_id: str,
    database_id: str,
    data: Dict[str, Any]
) -> None:
    """Cache data for a specific database."""
    pass

async def get_database_data(
    self,
    db: Session,
    user_id: str,
    database_id: str
) -> Optional[Dict[str, Any]]:
    """Retrieve cached data for a specific database."""
    pass

async def get_all_cached_databases(
    self,
    db: Session,
    user_id: str
) -> Dict[str, Dict[str, Any]]:
    """Get all cached database data for a user."""
    pass
```

**Updated Methods**:

```python
async def cache_graph_data(
    self,
    db: Session,
    user_id: str,
    data: Dict[str, Any],
    use_adaptive_ttl: bool = True
) -> None:
    """Cache graph data with timezone-aware datetime."""
    # Change: Use datetime.now(timezone.utc) instead of datetime.utcnow()
    now = datetime.now(timezone.utc)
    # ... rest of implementation
```

### 2. Notion Client Retry Logic

**File**: `app/backend/app/services/notion_client.py`

**New Component**: Retry decorator with exponential backoff

```python
from functools import wraps
import asyncio
from typing import TypeVar, Callable

T = TypeVar('T')

def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
):
    """
    Decorator for retrying async functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff calculation
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except (httpx.TimeoutException, httpx.NetworkError) as e:
                    last_exception = e

                    if attempt == max_retries:
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    await asyncio.sleep(delay)
                except RateLimitError as e:
                    # Handle rate limiting specially
                    if e.retry_after:
                        delay = e.retry_after
                    else:
                        delay = min(
                            base_delay * (exponential_base ** attempt),
                            max_delay
                        )

                    logger.warning(
                        f"Rate limited. Waiting {delay}s before retry..."
                    )

                    await asyncio.sleep(delay)

                    if attempt == max_retries:
                        raise

            raise last_exception

        return wrapper
    return decorator
```

**Updated Methods**:

```python
@with_retry(max_retries=3, base_delay=1.0)
async def get_databases(self, token: str) -> List[Dict[str, Any]]:
    """Fetch all accessible databases with retry logic."""
    # Existing implementation
    pass

@with_retry(max_retries=3, base_delay=2.0)
async def get_pages(self, token: str, database_id: str) -> List[Dict[str, Any]]:
    """Fetch all pages from a database with retry logic."""
    # Existing implementation
    pass
```

**New Configuration**:

```python
class NotionAPIClient:
    """Client for interacting with the Notion API."""

    BASE_URL = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"

    # Configurable timeouts
    TIMEOUT_DATABASE_LIST = 60.0
    TIMEOUT_DATABASE_QUERY = 90.0
    TIMEOUT_PAGE_FETCH = 30.0

    def __init__(self):
        """Initialize with configurable timeouts from environment."""
        import os

        self.timeout_database_list = float(
            os.getenv("NOTION_TIMEOUT_DATABASE_LIST", self.TIMEOUT_DATABASE_LIST)
        )
        self.timeout_database_query = float(
            os.getenv("NOTION_TIMEOUT_DATABASE_QUERY", self.TIMEOUT_DATABASE_QUERY)
        )
        self.timeout_page_fetch = float(
            os.getenv("NOTION_TIMEOUT_PAGE_FETCH", self.TIMEOUT_PAGE_FETCH)
        )
```

### 3. Graph Service Progressive Loading

**File**: `app/backend/app/services/graph_service.py`

**New Methods**:

```python
async def get_graph_data_progressive(
    self,
    db: Session,
    user_id: Union[str, UUID],
    yield_progress: Callable[[Dict[str, Any]], None]
) -> Dict[str, Any]:
    """
    Get graph data with progressive loading and progress callbacks.

    Args:
        db: Database session
        user_id: User ID
        yield_progress: Callback function to report progress

    Returns:
        Complete graph data with metadata about failures
    """
    # Get cached data first
    cached_databases = await cache_manager.get_all_cached_databases(db, user_id)

    if cached_databases:
        # Yield cached data immediately
        cached_graph = self._merge_database_data(cached_databases)
        yield_progress({
            "type": "cached_data",
            "data": cached_graph,
            "cached_at": max(d.get("cached_at") for d in cached_databases.values())
        })

    # Fetch fresh data
    result = await self._fetch_and_transform_data_progressive(
        db, user_id, yield_progress
    )

    return result

async def _fetch_and_transform_data_progressive(
    self,
    db: Session,
    user_id: Union[str, UUID],
    yield_progress: Callable[[Dict[str, Any]], None]
) -> Dict[str, Any]:
    """
    Fetch data progressively, yielding results as databases complete.

    Returns:
        {
            "nodes": [...],
            "edges": [...],
            "databases": [...],
            "metadata": {
                "total_databases": int,
                "successful_databases": int,
                "failed_databases": [{"id": str, "error": str}, ...],
                "fetched_at": datetime
            }
        }
    """
    # Get token
    stored_token = db.query(NotionToken).filter(
        NotionToken.user_id == user_id
    ).first()

    if not stored_token:
        raise Exception("No Notion token found for user")

    token = auth_service.decrypt_notion_token(stored_token.encrypted_token)

    # Fetch databases
    databases = await notion_client.get_databases(token)
    total_databases = len(databases)

    yield_progress({
        "type": "databases_fetched",
        "total": total_databases
    })

    # Fetch pages from each database
    all_pages = []
    successful_databases = []
    failed_databases = []

    for idx, database in enumerate(databases):
        try:
            pages = await notion_client.get_pages(token, database["id"])
            all_pages.extend(pages)
            successful_databases.append(database)

            # Cache this database's data
            await cache_manager.cache_database_data(
                db, user_id, database["id"],
                {"pages": pages, "database": database}
            )

            # Yield progress
            yield_progress({
                "type": "database_completed",
                "database_id": database["id"],
                "database_name": database["title"],
                "page_count": len(pages),
                "progress": (idx + 1) / total_databases
            })

        except NotionAPIError as e:
            logger.warning(
                f"Failed to fetch pages from database {database['id']}: {str(e)}"
            )
            failed_databases.append({
                "id": database["id"],
                "title": database["title"],
                "error": str(e)
            })

            # Try to use cached data for this database
            cached_db_data = await cache_manager.get_database_data(
                db, user_id, database["id"]
            )
            if cached_db_data:
                all_pages.extend(cached_db_data.get("pages", []))
                successful_databases.append(database)

                yield_progress({
                    "type": "database_from_cache",
                    "database_id": database["id"],
                    "database_name": database["title"],
                    "page_count": len(cached_db_data.get("pages", [])),
                    "progress": (idx + 1) / total_databases
                })

    # Transform data
    nodes = self._transform_pages_to_nodes(all_pages)
    edges = self._transform_relations_to_edges(all_pages)
    database_list = self._transform_databases(successful_databases)

    result = {
        "nodes": nodes,
        "edges": edges,
        "databases": database_list,
        "metadata": {
            "total_databases": total_databases,
            "successful_databases": len(successful_databases),
            "failed_databases": failed_databases,
            "fetched_at": datetime.now(timezone.utc).isoformat()
        }
    }
des(all_pages)
    edges = self._transform_relations_to_edges(all_pages)
    database_list = self._transform_databases(databases)

    return {
        "nodes": nodes,
        "edges": edges,
        "databases": database_list
    }
```

### 4. View Endpoint Streaming

**File**: `app/backend/app/routers/views.py`

**Updated Endpoint**:

```python
from fastapi.responses import StreamingResponse
import json

@router.get("/{view_id}/data")
async def get_view_graph_data(
    view_id: str,
    stream: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get graph data for a view with optional streaming.

    Args:
        view_id: View ID
        stream: If True, stream progress updates (Server-Sent Events)
        db: Database session

    Returns:
        Graph data or streaming response with progress updates
    """
    try:
        view = database_service.get_view(db, view_id)

        if not view:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"View with id {view_id} not found"
            )

        if not view.database_ids or len(view.database_ids) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This view has no databases selected"
            )

        if stream:
            # Return streaming response
            async def generate():
                progress_updates = []

                def yield_progress(update: Dict[str, Any]):
                    progress_updates.append(update)
                    # Send as Server-Sent Event
                    event_data = json.dumps(update)
                    return f"data: {event_data}\n\n"

                # Get data with progress
                graph_data = await graph_service.get_graph_data_progressive(
                    db, str(view.user_id), yield_progress
                )

                # Filter by view's selected databases
                filtered_data = self._filter_graph_data(
                    graph_data, view.database_ids
                )

                # Send final data
                final_event = json.dumps({
                    "type": "complete",
                    "data": filtered_data
                })
                yield f"data: {final_event}\n\n"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
        else:
            # Return complete data (existing behavior)
            graph_data = await graph_service.get_graph_data(db, str(view.user_id))
            filtered_data = self._filter_graph_data(graph_data, view.database_ids)
            return GraphDataResponse(**filtered_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving view graph data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve view graph data: {str(e)}"
        )

def _filter_graph_data(
    self,
    graph_data: Dict[str, Any],
    selected_db_ids: List[str]
) -> Dict[str, Any]:
    """Filter graph data by selected database IDs."""
    selected_db_ids_set = set(selected_db_ids)

    filtered_nodes = [
        node for node in graph_data["nodes"]
        if node["databaseId"] in selected_db_ids_set
    ]

    filtered_node_ids = {node["id"] for node in filtered_nodes}

    filtered_edges = [
        edge for edge in graph_data["edges"]
        if edge["sourceId"] in filtered_node_ids
        and edge["targetId"] in filtered_node_ids
    ]

    filtered_databases = [
        db for db in graph_data["databases"]
        if db["id"] in selected_db_ids_set
    ]

    return {
        "nodes": filtered_nodes,
        "edges": filtered_edges,
        "databases": filtered_databases,
        "metadata": graph_data.get("metadata", {})
    }
```

### 5. Frontend Progress Display

**File**: `app/frontend/src/components/ViewPage.tsx`

**Enhanced Loading State**:

```typescript
interface LoadingProgress {
  type: string;
  total?: number;
  progress?: number;
  database_name?: string;
  page_count?: number;
  error?: string;
}

const ViewPage: React.FC = () => {
  const [loadingProgress, setLoadingProgress] = useState<LoadingProgress | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);

  const loadView = async (id: string) => {
    try {
      setLoading(true);
      setError("");
      setWarnings([]);

      // Try streaming endpoint first
      const eventSource = new EventSource(
        `/api/views/${id}/data?stream=true`
      );

      eventSource.onmessage = (event) => {
        const update = JSON.parse(event.data);

        switch (update.type) {
          case "cached_data":
            // Show cached data immediately
            setGraphData(update.data);
            setFilteredData(update.data);
            setLoadingProgress({
              type: "cached",
              message: "Showing cached data, fetching updates..."
            });
            break;

          case "databases_fetched":
            setLoadingProgress({
              type: "fetching",
              total: update.total,
              progress: 0
            });
            break;

          case "database_completed":
            setLoadingProgress({
              type: "fetching",
              progress: update.progress,
              database_name: update.database_name,
              page_count: update.page_count
            });
            break;

          case "database_from_cache":
            setWarnings(prev => [
              ...prev,
              `Using cached data for ${update.database_name} (fetch failed)`
            ]);
            break;

          case "complete":
            setGraphData(update.data);
            setFilteredData(update.data);

            // Show warnings for failed databases
            if (update.data.metadata?.failed_databases?.length > 0) {
              const failedNames = update.data.metadata.failed_databases
                .map(db => db.title)
                .join(", ");
              setWarnings(prev => [
                ...prev,
                `Some databases failed to load: ${failedNames}`
              ]);
            }

            setLoading(false);
            eventSource.close();
            break;
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        // Fallback to non-streaming
        loadViewNonStreaming(id);
      };

    } catch (err: any) {
      console.error("Error loading view:", err);
      setError(extractErrorMessage(err));
      setLoading(false);
    }
  };

  // Render loading with progress
  if (loading) {
    return (
      <LoadingSpinner
        message={getLoadingMessage(loadingProgress)}
        progress={loadingProgress?.progress}
      />
    );
  }

  // Render warnings
  if (warnings.length > 0) {
    return (
      <div className="view-page">
        <WarningBanner warnings={warnings} onDismiss={() => setWarnings([])} />
        {/* Rest of view */}
      </div>
    );
  }
};

function getLoadingMessage(progress: LoadingProgress | null): string {
  if (!progress) return "Loading view...";

  switch (progress.type) {
    case "cached":
      return "Showing cached data, fetching updates...";
    case "fetching":
      if (progress.database_name) {
        return `Loading ${progress.database_name} (${progress.page_count} pages)...`;
      }
      return `Loading databases... ${Math.round((progress.progress || 0) * 100)}%`;
    default:
      return "Loading view...";
  }
}
```

## Data Models

### Enhanced Cache Model

**File**: `app/backend/app/services/cache_manager.py`

```python
class CachedDatabaseData(Base):
    """Model for per-database cached data."""
    __tablename__ = "cached_database_data"

    user_id = Column(UUID(as_uuid=True), primary_key=True)
    database_id = Column(String(255), primary_key=True)
    data = Column(JSON, nullable=False)
    cached_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        Index('ix_cached_db_user_db', 'user_id', 'database_id'),
        Index('ix_cached_db_expires', 'expires_at'),
    )
```

### Response Models

**File**: `app/backend/app/routers/views.py`

```python
class GraphMetadata(BaseModel):
    """Metadata about graph data fetch operation."""
    total_databases: int
    successful_databases: int
    failed_databases: List[Dict[str, str]]
    fetched_at: str
    from_cache: bool = False

class GraphDataResponse(BaseModel):
    """Response model for graph data with metadata."""
    nodes: List[dict]
    edges: List[dict]
    databases: List[dict]
    metadata: Optional[GraphMetadata] = None
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Timezone-Aware DateTime Consistency

*For any* cache operation (create, update, query, compare), all datetime objects used SHALL be timezone-aware with UTC timezone.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

### Property 2: Multi-Database Fetch Resilience

*For any* set of databases being fetched, if a subset of databases fail to fetch, the system SHALL successfully return data from all databases that did not fail.

**Validates: Requirements 2.1, 2.6**

### Property 3: Retry Exponential Backoff

*For any* network error during API requests, the system SHALL retry up to 3 times with exponentially increasing delays (base 1s, max 60s).

**Validates: Requirements 2.3**

### Property 4: Per-Database Cache Granularity

*For any* user's graph data, each database's data SHALL be cached independently such that fetching or updating one database does not affect the cache state of other databases.

**Validates: Requirements 6.1, 6.3, 6.5**

### Property 5: Cache Fallback on Fetch Failure

*For any* database that fails to fetch, if cached data exists for that database, the system SHALL use the cached data in the final result.

**Validates: Requirements 6.2, 6.4**

### Property 6: Response Metadata Completeness

*For any* graph data response, the metadata SHALL include: total database count, successful database count, list of failed databases with errors, and fetch timestamp.

**Validates: Requirements 3.4, 3.5**

### Property 7: View Configuration Validation

*For any* view with invalid configuration (non-existent database IDs, invalid zoom/pan values), the system SHALL filter invalid values, use defaults where appropriate, and include validation information in the response.

**Validates: Requirements 8.2, 8.3, 8.5**

## Error Handling

### DateTime Timezone Errors

**Error Type**: `TypeError` - "can't compare offset-naive and offset-aware datetimes"

**Current Behavior**: Raised when comparing `datetime.utcnow()` (naive) with database column values (aware)

**Fixed Behavior**:
- All datetime objects use `datetime.now(timezone.utc)` which is timezone-aware
- Comparisons always succeed
- If naive datetime is detected, raise clear `ValueError` with message: "Datetime must be timezone-aware with UTC timezone"

### Notion API Errors

**Error Types**:
- `httpx.TimeoutException` - Request timeout
- `httpx.NetworkError` - Network connectivity issues
- `RateLimitError` - API rate limit exceeded (429)
- `InvalidTokenError` - Invalid API token (401)
- `PermissionError` - Insufficient permissions (403)

**Handling Strategy**:

1. **Transient Errors** (Timeout, NetworkError):
   - Retry up to 3 times with exponential backoff
   - Log each retry attempt
   - If all retries fail, log error and continue with other databases
   - Include failed database in metadata

2. **Rate Limit Errors**:
   - Extract `Retry-After` header from response
   - Wait for specified duration
   - Retry request
   - If retry fails, treat as transient error

3. **Permanent Errors** (InvalidToken, Permission):
   - Do not retry
   - Log error with full context
   - Return error to user immediately
   - Do not attempt to fetch other databases

### Cache Errors

**Error Types**:
- `SQLAlchemyError` - Database operation failures
- `ValueError` - Invalid cache data format

**Handling Strategy**:
- Log error with full context
- Continue operation without cache
- Do not fail the entire request
- Return fresh data without caching

### View Configuration Errors

**Error Type**: `HTTPException` with status 400

**Scenarios**:
1. **No databases selected**: Return 400 with message "This view has no databases selected"
2. **View not found**: Return 404 with message "View with id {id} not found"
3. **Permission denied**: Return 403 with message "You don't have permission to access this view"

## Testing Strategy

### Unit Tests

Unit tests will focus on specific examples, edge cases, and error conditions:

1. **DateTime Handling**:
   - Test cache creation with timezone-aware datetime
   - Test cache expiration check with timezone-aware datetime
   - Test error when naive datetime is used

2. **Retry Logic**:
   - Test retry count is correct (3 attempts)
   - Test exponential backoff timing
   - Test rate limit retry-after handling
   - Test no retry for permanent errors

3. **Cache Operations**:
   - Test per-database cache storage
   - Test cache retrieval by database ID
   - Test cache merging from multiple databases
   - Test cache expiration per database

4. **Error Handling**:
   - Test partial results when some databases fail
   - Test metadata includes failed databases
   - Test fallback to cache on fetch failure
   - Test view configuration validation

### Property-Based Tests

Property-based tests will verify universal properties across all inputs using Hypothesis (Python) and fast-check (TypeScript). Each test will run a minimum of 100 iterations.

**Test Configuration**:
- Library: Hypothesis 6.103.5 (Python)
- Minimum iterations: 100 per property
- Tag format: `# Feature: view-loading-fix, Property {N}: {description}`

**Property Test Cases**:

1. **Property 1: Timezone-Aware DateTime Consistency**
   - Generate random cache operations
   - Verify all datetime objects have tzinfo set to UTC
   - Verify no TypeError exceptions occur during comparisons

2. **Property 2: Multi-Database Fetch Resilience**
   - Generate random sets of databases with random failure patterns
   - Verify successful databases are always included in results
   - Verify failed databases are listed in metadata

3. **Property 3: Retry Exponential Backoff**
   - Generate random network errors
   - Verify retry count equals 3
   - Verify backoff delays follow exponential pattern

4. **Property 4: Per-Database Cache Granularity**
   - Generate random database data
   - Cache each database independently
   - Verify updating one database doesn't affect others

5. **Property 5: Cache Fallback on Fetch Failure**
   - Generate random database failures with existing cache
   - Verify cached data is used for failed databases
   - Verify fresh data is used for successful databases

6. **Property 6: Response Metadata Completeness**
   - Generate random fetch results
   - Verify metadata contains all required fields
   - Verify failed database list is accurate

7. **Property 7: View Configuration Validation**
   - Generate random invalid view configurations
   - Verify invalid values are filtered/defaulted
   - Verify validation information is in response

### Integration Tests

Integration tests will verify end-to-end behavior:

1. **View Loading with Partial Failures**:
   - Mock Notion API with some databases failing
   - Verify view loads with partial data
   - Verify warnings are displayed

2. **Cache Hit and Miss Scenarios**:
   - Test cold start (no cache)
   - Test warm start (full cache)
   - Test partial cache (some databases cached)

3. **Streaming Progress Updates**:
   - Test Server-Sent Events stream
   - Verify progress updates are sent
   - Verify final data is complete

4. **Timeout Configuration**:
   - Test environment variable overrides
   - Verify correct timeouts are used per operation type

### Test Execution

All tests run inside Docker containers:

```bash
# Run all backend tests
make test-backend

# Run specific test file
docker compose exec backend pytest tests/test_cache_manager.py -v

# Run property-based tests only
docker compose exec backend pytest tests/test_*_properties.py -v

# Run with coverage
docker compose exec backend pytest --cov=app --cov-report=html
```

## Implementation Notes

### Migration Required

A new database table is needed for per-database caching:

```python
# Migration: add_cached_database_data_table.py

def upgrade():
    op.create_table(
        'cached_database_data',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('database_id', sa.String(255), nullable=False),
        sa.Column('data', postgresql.JSON, nullable=False),
        sa.Column('cached_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('user_id', 'database_id')
    )

    op.create_index(
        'ix_cached_db_user_db',
        'cached_database_data',
        ['user_id', 'database_id']
    )

    op.create_index(
        'ix_cached_db_expires',
        'cached_database_data',
        ['expires_at']
    )

def downgrade():
    op.drop_index('ix_cached_db_expires', 'cached_database_data')
    op.drop_index('ix_cached_db_user_db', 'cached_database_data')
    op.drop_table('cached_database_data')
```

### Environment Variables

Add to `.env` file:

```bash
# Notion API Timeouts (seconds)
NOTION_TIMEOUT_DATABASE_LIST=60
NOTION_TIMEOUT_DATABASE_QUERY=90
NOTION_TIMEOUT_PAGE_FETCH=30

# Retry Configuration
NOTION_MAX_RETRIES=3
NOTION_RETRY_BASE_DELAY=1.0
NOTION_RETRY_MAX_DELAY=60.0
```

### Backward Compatibility

The changes maintain backward compatibility:

1. **Existing Cache**: Old monolithic cache entries will continue to work. New per-database cache will be used going forward.

2. **API Endpoints**: The `/api/views/{id}/data` endpoint supports both streaming (`?stream=true`) and non-streaming modes. Existing clients will continue to work.

3. **Frontend**: The frontend gracefully falls back to non-streaming mode if Server-Sent Events are not supported.

### Performance Considerations

1. **Cache Storage**: Per-database caching increases storage requirements but improves cache hit rates and reduces API calls.

2. **Retry Logic**: Exponential backoff prevents overwhelming the Notion API during outages while ensuring transient errors are handled.

3. **Progressive Loading**: Streaming responses reduce perceived latency by showing cached data immediately and updating progressively.

4. **Database Queries**: Indexes on `user_id`, `database_id`, and `expires_at` ensure efficient cache lookups and cleanup.

### Security Considerations

1. **Token Handling**: Notion API tokens remain encrypted in the database. Retry logic does not log tokens.

2. **Error Messages**: Error messages do not expose sensitive information like token values or internal system details.

3. **Rate Limiting**: Proper handling of rate limit errors prevents account suspension.

4. **View Access**: View data endpoint remains public (no auth required) as views are designed to be shareable via URL.
