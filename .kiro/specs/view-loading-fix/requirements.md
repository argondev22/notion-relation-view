# Requirements Document

## Introduction

This specification addresses critical issues preventing views from loading properly in the Notion Relation View application. Users experience indefinite loading states when accessing views, caused by datetime timezone mismatches, Notion API timeout issues, and lack of user feedback during long-running operations.

## Glossary

- **System**: The Notion Relation View backend application
- **Cache_Manager**: Service responsible for caching graph data with TTL
- **Notion_Client**: Service that interfaces with the Notion API
- **Graph_Service**: Service that orchestrates data fetching and transformation
- **View_Endpoint**: FastAPI endpoint that serves view data
- **Frontend**: React application that displays the graph visualization
- **Database**: PostgreSQL database storing application data
- **Timezone-Aware_DateTime**: Python datetime object with timezone information
- **Timezone-Naive_DateTime**: Python datetime object without timezone information

## Requirements

### Requirement 1: Fix DateTime Timezone Handling

**User Story:** As a developer, I want the cache manager to use timezone-aware datetime objects, so that datetime comparisons work correctly with the PostgreSQL database.

#### Acceptance Criteria

1. WHEN the Cache_Manager creates or updates cache entries, THE System SHALL use timezone-aware datetime objects
2. WHEN the Cache_Manager compares datetime values, THE System SHALL ensure both values are timezone-aware
3. WHEN the Cache_Manager queries expired cache entries, THE System SHALL use timezone-aware datetime for comparison
4. THE Cache_Manager SHALL use UTC timezone for all datetime operations
5. IF a datetime comparison is attempted between timezone-naive and timezone-aware objects, THEN THE System SHALL raise a clear error

### Requirement 2: Improve Notion API Reliability

**User Story:** As a user, I want the system to handle Notion API failures gracefully, so that one failing database doesn't prevent other databases from loading.

#### Acceptance Criteria

1. WHEN fetching pages from multiple databases, THE System SHALL continue processing remaining databases if one database fails
2. WHEN a Notion API request times out, THE System SHALL log the error and continue with other requests
3. WHEN a Notion API request fails with a network error, THE System SHALL retry the request up to 3 times with exponential backoff
4. WHEN a Notion API request fails with a rate limit error, THE System SHALL wait for the retry-after period before retrying
5. WHEN all retry attempts are exhausted, THE System SHALL log the failure and return partial results
6. THE System SHALL track which databases failed to load and include this information in the response

### Requirement 3: Implement Progressive Data Loading

**User Story:** As a user, I want to see partial results as they become available, so that I don't have to wait for all data to load before seeing anything.

#### Acceptance Criteria

1. WHEN fetching data from multiple databases, THE System SHALL return partial results as each database completes
2. WHEN cached data exists, THE System SHALL return cached data immediately while fetching fresh data in the background
3. WHEN fresh data becomes available, THE Frontend SHALL update the display without disrupting user interaction
4. THE System SHALL include metadata indicating whether data is from cache or fresh
5. THE System SHALL include a timestamp indicating when the data was last updated

### Requirement 4: Enhance User Feedback

**User Story:** As a user, I want to see progress information during data loading, so that I understand what the system is doing and can identify issues.

#### Acceptance Criteria

1. WHEN data is being fetched, THE Frontend SHALL display a progress indicator showing the number of databases processed
2. WHEN a database fails to load, THE Frontend SHALL display a warning message identifying which database failed
3. WHEN all databases fail to load, THE Frontend SHALL display a clear error message with retry option
4. WHEN data is loading from cache, THE Frontend SHALL indicate that cached data is being displayed
5. WHEN the System is fetching fresh data in the background, THE Frontend SHALL show a subtle indicator

### Requirement 5: Optimize API Timeout Configuration

**User Story:** As a developer, I want configurable timeout values for Notion API requests, so that the system can handle large workspaces without timing out.

#### Acceptance Criteria

1. THE Notion_Client SHALL support configurable timeout values for different operation types
2. WHEN fetching databases, THE System SHALL use a timeout of 60 seconds
3. WHEN fetching pages from a single database, THE System SHALL use a timeout of 90 seconds
4. WHEN fetching individual pages in batch mode, THE System SHALL use a timeout of 30 seconds per page
5. THE System SHALL allow timeout configuration via environment variables

### Requirement 6: Implement Partial Cache Invalidation

**User Story:** As a developer, I want to cache data per database, so that failures in one database don't invalidate the entire cache.

#### Acceptance Criteria

1. WHEN caching graph data, THE Cache_Manager SHALL store data with database-level granularity
2. WHEN a database fails to fetch, THE System SHALL use cached data for that database if available
3. WHEN updating cached data, THE System SHALL update only the databases that were successfully fetched
4. WHEN retrieving cached data, THE System SHALL merge cached and fresh data appropriately
5. THE Cache_Manager SHALL track cache age per database

### Requirement 7: Add Comprehensive Error Logging

**User Story:** As a developer, I want detailed error logs for API failures, so that I can diagnose and fix issues quickly.

#### Acceptance Criteria

1. WHEN a Notion API request fails, THE System SHALL log the request URL, method, status code, and error message
2. WHEN a timeout occurs, THE System SHALL log the operation type, database ID, and elapsed time
3. WHEN a retry is attempted, THE System SHALL log the retry attempt number and backoff duration
4. WHEN partial results are returned, THE System SHALL log which databases succeeded and which failed
5. THE System SHALL include correlation IDs in logs to trace requests across services

### Requirement 8: Validate View Configuration

**User Story:** As a user, I want clear error messages when a view is misconfigured, so that I can fix the configuration.

#### Acceptance Criteria

1. WHEN a view has no databases selected, THE View_Endpoint SHALL return a 400 error with a descriptive message
2. WHEN a view references non-existent databases, THE System SHALL filter them out and log a warning
3. WHEN a view has invalid zoom or pan values, THE System SHALL use default values and log a warning
4. THE View_Endpoint SHALL validate view configuration before attempting to fetch data
5. THE System SHALL return validation errors in a structured format that the Frontend can display
