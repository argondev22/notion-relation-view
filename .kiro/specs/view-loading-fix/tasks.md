# Implementation Plan: View Loading Fix

## Overview

This implementation plan addresses three critical issues: datetime timezone mismatches, Notion API reliability, and user feedback during loading. The approach is to fix the datetime handling first, then add retry logic and per-database caching, and finally implement progressive loading with enhanced frontend feedback.

## Tasks

- [x] 1. Fix datetime timezone handling in cache manager
  - Replace all `datetime.utcnow()` calls with `datetime.now(timezone.utc)`
  - Add validation to ensure all datetime objects are timezone-aware
  - Update cache expiration queries to use timezone-aware comparisons
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ]* 1.1 Write property test for timezone-aware datetime consistency
  - **Property 1: Timezone-Aware DateTime Consistency**
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

- [x] 2. Create database migration for per-database caching
  - Create new `cached_database_data` table with composite primary key (user_id, database_id)
  - Add indexes for efficient lookups (user_id + database_id, expires_at)
  - Include timezone-aware datetime columns
  - _Requirements: 6.1_

- [ ] 3. Implement retry logic with exponential backoff
  - [x] 3.1 Create retry decorator for async functions
    - Implement exponential backoff calculation
    - Handle different error types (timeout, network, rate limit)
    - Add configurable retry parameters (max_retries, base_delay, max_delay)
    - Include comprehensive logging for each retry attempt
    - _Requirements: 2.3, 2.4, 7.3_

  - [ ]* 3.2 Write property test for retry exponential backoff
    - **Property 3: Retry Exponential Backoff**
    - **Validates: Requirements 2.3**

  - [x] 3.3 Apply retry decorator to Notion API methods
    - Add `@with_retry` to `get_databases()` method
    - Add `@with_retry` to `get_pages()` method
    - Configure appropriate retry parameters for each method
    - _Requirements: 2.3_

  - [ ]* 3.4 Write unit tests for retry logic
    - Test retry count is correct (3 attempts)
    - Test exponential backoff timing
    - Test rate limit retry-after handling
    - Test no retry for permanent errors (401, 403)
    - _Requirements: 2.3, 2.4, 2.5_

- [ ] 4. Add configurable timeout support
  - [x] 4.1 Update NotionAPIClient initialization
    - Add timeout configuration from environment variables
    - Set default timeouts: 60s (databases), 90s (pages), 30s (individual pages)
    - Update httpx.Timeout configuration per operation type
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ]* 4.2 Write unit tests for timeout configuration
    - Test default timeout values
    - Test environment variable overrides
    - Test correct timeout is used per operation type
    - _Requirements: 5.1, 5.5_

- [ ] 5. Implement per-database cache manager methods
  - [x] 5.1 Add CachedDatabaseData model
    - Define SQLAlchemy model with composite primary key
    - Add indexes for efficient queries
    - Use timezone-aware DateTime columns
    - _Requirements: 6.1_

  - [x] 5.2 Implement cache_database_data method
    - Store data for individual database
    - Use timezone-aware datetime for cached_at and expires_at
    - Calculate adaptive TTL based on data size
    - _Requirements: 6.1, 6.5_

  - [x] 5.3 Implement get_database_data method
    - Retrieve cached data for specific database
    - Check expiration using timezone-aware comparison
    - Return None if expired or not found
    - _Requirements: 6.1, 6.5_

  - [x] 5.4 Implement get_all_cached_databases method
    - Retrieve all cached databases for a user
    - Filter out expired entries
    - Return dictionary mapping database_id to data
    - _Requirements: 6.1, 6.4_

  - [ ]* 5.5 Write property tests for per-database caching
    - **Property 4: Per-Database Cache Granularity**
    - **Property 5: Cache Fallback on Fetch Failure**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

- [x] 6. Checkpoint - Ensure all tests pass
  - Run all backend tests to verify datetime fixes and retry logic
  - Verify cache operations work correctly
  - Ensure all tests pass, ask the user if questions arise

- [ ] 7. Implement progressive data fetching in graph service
  - [x] 7.1 Create get_graph_data_progressive method
    - Accept progress callback function
    - Return cached data immediately if available
    - Fetch fresh data and yield progress updates
    - _Requirements: 3.1, 3.2_

  - [x] 7.2 Create _fetch_and_transform_data_progressive method
    - Fetch databases and yield progress
    - Iterate through databases with error handling
    - Continue processing on individual database failures
    - Cache successful databases individually
    - Track failed databases with error messages
    - Use cached data as fallback for failed databases
    - Return complete result with metadata
    - _Requirements: 2.1, 2.6, 6.2, 6.3_

  - [ ]* 7.3 Write property test for multi-database fetch resilience
    - **Property 2: Multi-Database Fetch Resilience**
    - **Validates: Requirements 2.1, 2.6**

  - [x] 7.3 Implement _merge_database_data method
    - Merge per-database cached data into complete graph
    - Transform pages to nodes and edges
    - Return unified graph structure
    - _Requirements: 6.4_

  - [ ]* 7.4 Write unit tests for progressive fetching
    - Test partial results when some databases fail
    - Test metadata includes failed databases
    - Test fallback to cache on fetch failure
    - Test progress callbacks are invoked
    - _Requirements: 2.1, 2.6, 6.2_

- [x] 8. Add response metadata models
  - Create GraphMetadata Pydantic model
  - Create enhanced GraphDataResponse model with metadata field
  - Update view endpoint response type
  - _Requirements: 3.4, 3.5_

- [ ]* 8.1 Write property test for response metadata completeness
  - **Property 6: Response Metadata Completeness**
  - **Validates: Requirements 3.4, 3.5**

- [ ] 9. Implement streaming endpoint for progressive loading
  - [x] 9.1 Add _filter_graph_data helper method
    - Filter nodes by selected database IDs
    - Filter edges to only include visible nodes
    - Filter databases list
    - Return filtered graph with metadata
    - _Requirements: 8.2_

  - [x] 9.2 Update get_view_graph_data endpoint
    - Add optional `stream` query parameter
    - Implement Server-Sent Events streaming
    - Send progress updates as events
    - Send final data as complete event
    - Maintain backward compatibility with non-streaming mode
    - _Requirements: 3.1_

  - [ ] 9.3 Add view configuration validation
    - Validate database_ids is not empty
    - Filter out non-existent database IDs
    - Use default values for invalid zoom/pan
    - Return structured validation errors
    - _Requirements: 8.1, 8.2, 8.3, 8.5_

  - [ ]* 9.4 Write property test for view configuration validation
    - **Property 7: View Configuration Validation**
    - **Validates: Requirements 8.2, 8.3, 8.5**

  - [ ]* 9.5 Write unit tests for view endpoint
    - Test empty database_ids returns 400 error
    - Test non-existent databases are filtered
    - Test invalid zoom/pan values use defaults
    - Test streaming mode sends progress events
    - _Requirements: 8.1, 8.2, 8.3_

- [ ] 10. Checkpoint - Ensure backend implementation is complete
  - Run all backend tests including property tests
  - Verify streaming endpoint works correctly
  - Test with mock Notion API failures
  - Ensure all tests pass, ask the user if questions arise

- [ ] 11. Enhance frontend loading state
  - [x] 11.1 Add LoadingProgress interface
    - Define types for different progress update types
    - Add fields for progress percentage, database name, page count
    - _Requirements: 4.1_

  - [x] 11.2 Implement EventSource for streaming
    - Connect to streaming endpoint with EventSource
    - Handle different event types (cached_data, databases_fetched, database_completed, complete)
    - Update loading progress state based on events
    - Fallback to non-streaming on error
    - _Requirements: 3.1, 4.1_

  - [x] 11.3 Update loadView function
    - Try streaming endpoint first
    - Handle progress updates and update UI state
    - Collect warnings for failed databases
    - Update graph data progressively
    - Close EventSource on completion
    - _Requirements: 4.1, 4.2, 4.4, 4.5_

  - [x] 11.4 Create getLoadingMessage helper
    - Return appropriate message based on progress type
    - Show percentage for fetching progress
    - Show database name and page count during loading
    - _Requirements: 4.1_

- [ ] 12. Add warning banner component
  - [x] 12.1 Create WarningBanner component
    - Display list of warnings
    - Show which databases failed to load
    - Include dismiss functionality
    - Style as non-intrusive banner
    - _Requirements: 4.2_

  - [x] 12.2 Integrate WarningBanner in ViewPage
    - Show warnings when databases fail
    - Display above graph visualization
    - Allow user to dismiss warnings
    - _Requirements: 4.2_

- [x] 13. Update LoadingSpinner component
  - Add optional progress prop for percentage display
  - Show progress bar when progress is available
  - Update message dynamically based on loading state
  - _Requirements: 4.1_

- [ ] 14. Add comprehensive error logging
  - [x] 14.1 Update Notion API error handling
    - Log request URL, method, status code, error message
    - Log timeout with operation type, database ID, elapsed time
    - Include correlation IDs in log entries
    - _Requirements: 7.1, 7.2, 7.5_

  - [x] 14.2 Update graph service logging
    - Log which databases succeeded and failed
    - Log partial results information
    - Include timing information
    - _Requirements: 7.4_

  - [ ]* 14.3 Write unit tests for logging
    - Test API failure logs contain required fields
    - Test timeout logs contain required fields
    - Test retry logs contain attempt number and backoff
    - Test partial results logs contain database lists
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 15. Final integration testing and cleanup
  - [ ] 15.1 Test complete flow with mock failures
    - Test view loading with some databases failing
    - Test cached data is shown immediately
    - Test progress updates are displayed
    - Test warnings are shown for failures
    - _Requirements: 2.1, 3.1, 4.1, 4.2_

  - [ ] 15.2 Test timeout scenarios
    - Test with slow Notion API responses
    - Verify timeouts are respected
    - Verify retry logic works correctly
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 15.3 Update documentation
    - Document new environment variables
    - Document streaming endpoint usage
    - Update API documentation
    - _Requirements: 5.5_

- [-] 16. Final checkpoint - Ensure all tests pass
  - Run complete test suite (backend and frontend)
  - Verify all property tests pass with 100+ iterations
  - Test in Docker environment
  - Ensure all tests pass, ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties with minimum 100 iterations
- Unit tests validate specific examples and edge cases
- All tests must run inside Docker containers using `make test-backend` and `make test-frontend`
