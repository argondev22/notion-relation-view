# Streaming API Documentation

## Overview

The view-loading-fix feature introduces progressive data loading with Server-Sent Events (SSE) streaming support. This allows the frontend to receive real-time progress updates as data is fetched from multiple Notion databases.

## Streaming Endpoint

### GET `/api/views/{view_id}/data?stream=true`

Fetches graph data for a view with progressive loading and real-time progress updates.

**Parameters:**
- `view_id` (path): View ID
- `stream` (query, optional): Set to `true` to enable streaming mode (default: `false`)

**Response:**
- **Non-streaming mode** (`stream=false` or omitted): Returns complete `GraphDataResponse` JSON
- **Streaming mode** (`stream=true`): Returns Server-Sent Events stream

## Server-Sent Events Format

The streaming endpoint sends events in the following format:

```
data: {"type": "event_type", ...additional_fields}\n\n
```

### Event Types

#### 1. `cached_data`
Sent immediately if cached data is available.

```json
{
  "type": "cached_data",
  "data": {
    "nodes": [...],
    "edges": [...],
    "databases": [...]
  },
  "message": "Showing cached data, fetching updates..."
}
```

#### 2. `databases_fetched`
Sent after the list of databases is retrieved.

```json
{
  "type": "databases_fetched",
  "total": 5
}
```

#### 3. `database_completed`
Sent after each database is successfully fetched.

```json
{
  "type": "database_completed",
  "database_id": "abc123",
  "database_name": "My Database",
  "page_count": 42,
  "progress": 0.6
}
```

#### 4. `database_from_cache`
Sent when a database fetch fails and cached data is used as fallback.

```json
{
  "type": "database_from_cache",
  "database_id": "def456",
  "database_name": "Failed Database",
  "page_count": 15,
  "progress": 0.8
}
```

#### 5. `complete`
Sent when all databases have been processed.

```json
{
  "type": "complete",
  "data": {
    "nodes": [...],
    "edges": [...],
    "databases": [...],
    "metadata": {
      "total_databases": 5,
      "successful_databases": 4,
      "failed_databases": [
        {
          "id": "xyz789",
          "title": "Inaccessible Database",
          "error": "Permission denied"
        }
      ],
      "fetched_at": "2024-01-15T10:30:00Z",
      "from_cache": false
    }
  }
}
```

#### 6. `error`
Sent if a critical error occurs during streaming.

```json
{
  "type": "error",
  "error": "Error message"
}
```

## Frontend Integration

### Using EventSource

```typescript
const eventSource = new EventSource(`/api/views/${viewId}/data?stream=true`);

eventSource.onmessage = (event) => {
  const update = JSON.parse(event.data);

  switch (update.type) {
    case "cached_data":
      // Show cached data immediately
      setGraphData(update.data);
      break;

    case "databases_fetched":
      // Initialize progress tracking
      setTotalDatabases(update.total);
      break;

    case "database_completed":
      // Update progress
      setProgress(update.progress);
      setCurrentDatabase(update.database_name);
      break;

    case "complete":
      // Update with final data
      setGraphData(update.data);
      setLoading(false);
      eventSource.close();
      break;

    case "error":
      // Handle error
      setError(update.error);
      eventSource.close();
      break;
  }
};

eventSource.onerror = () => {
  eventSource.close();
  // Fallback to non-streaming endpoint
};
```

### Fallback Strategy

The frontend should implement a fallback to the non-streaming endpoint if:
- EventSource is not supported by the browser
- The streaming connection fails
- A timeout occurs

```typescript
try {
  await loadViewWithStreaming(viewId);
} catch (error) {
  // Fallback to non-streaming
  const data = await fetch(`/api/views/${viewId}/data`);
  setGraphData(await data.json());
}
```

## Response Metadata

Both streaming and non-streaming modes return metadata about the fetch operation:

```typescript
interface GraphMetadata {
  total_databases: number;
  successful_databases: number;
  failed_databases: FailedDatabase[];
  fetched_at: string;  // ISO 8601 timestamp
  from_cache: boolean;
}

interface FailedDatabase {
  id: string;
  title: string;
  error: string;
}
```

## Error Handling

### View Configuration Errors

**400 Bad Request** - View has no databases selected:
```json
{
  "detail": "This view has no databases selected. Please edit the view and select at least one database to display."
}
```

**404 Not Found** - View not found:
```json
{
  "detail": "View with id {view_id} not found"
}
```

### Partial Failures

When some databases fail to load, the system:
1. Continues processing remaining databases
2. Attempts to use cached data for failed databases
3. Includes failed databases in the metadata
4. Returns partial results with warnings

The frontend should display warnings to users about failed databases.

## Performance Considerations

### Caching Strategy

- **Per-database caching**: Each database is cached independently
- **Adaptive TTL**: Cache duration based on data size (15-30 minutes)
- **Fallback on failure**: Cached data used when fresh fetch fails

### Timeout Configuration

Configure timeouts via environment variables:

```bash
# Timeout for listing databases (default: 60s)
NOTION_TIMEOUT_DATABASE_LIST=60.0

# Timeout for querying database pages (default: 90s)
NOTION_TIMEOUT_DATABASE_QUERY=90.0

# Timeout for fetching individual pages (default: 30s)
NOTION_TIMEOUT_PAGE_FETCH=30.0
```

### Retry Logic

- **Transient errors**: Retried up to 3 times with exponential backoff
- **Rate limits**: Respects `Retry-After` header
- **Permanent errors**: Not retried (401, 403)

## Browser Compatibility

Server-Sent Events are supported in:
- Chrome/Edge 6+
- Firefox 6+
- Safari 5+
- Opera 11+

**Not supported in**: Internet Explorer

For unsupported browsers, the system automatically falls back to non-streaming mode.

## Security

- **Public access**: View data endpoints are publicly accessible via view URL
- **No authentication required**: Designed for embedding in Notion pages
- **Token encryption**: Notion API tokens remain encrypted in the database
- **No token exposure**: Error messages never expose token values

## Monitoring and Logging

All operations are logged with structured context:

```python
logger.info(
    "Progressive fetch complete",
    extra={
        "total_databases": 5,
        "successful_databases": 4,
        "failed_databases_count": 1,
        "node_count": 150,
        "edge_count": 75
    }
)
```

Log fields include:
- Operation type
- Request URL and method
- Status codes
- Error messages
- Database IDs
- Timing information
- Correlation IDs for request tracing
