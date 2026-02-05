import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { viewApi, graphApi } from "../api/client";
import { View, GraphData, ViewSettings } from "../types";
import GraphVisualizer from "./GraphVisualizer";
import SearchBar from "./SearchBar";
import DatabaseFilter from "./DatabaseFilter";
import LoadingSpinner from "./LoadingSpinner";
import ErrorMessage from "./ErrorMessage";

interface LoadingProgress {
  type: string;
  total?: number;
  progress?: number;
  database_name?: string;
  page_count?: number;
  message?: string;
}

interface FailedDatabase {
  id: string;
  title: string;
  error: string;
}

const ViewPage: React.FC = () => {
  const { viewId } = useParams<{ viewId: string }>();
  const [view, setView] = useState<View | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [filteredData, setFilteredData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingProgress, setLoadingProgress] = useState<LoadingProgress | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (viewId) {
      loadView(viewId);
    }
  }, [viewId]);

  const loadView = async (id: string) => {
    console.log("Loading view:", id);
    try {
      setLoading(true);
      setError("");
      setWarnings([]);
      setLoadingProgress(null);

      // Try to fetch view details (requires auth)
      let fetchedView: View | null = null;
      try {
        console.log("Fetching view details...");
        fetchedView = await viewApi.getView(id);
        console.log("View details fetched:", fetchedView);
      } catch (viewErr) {
        console.warn("Could not fetch view details (may not be authenticated):", viewErr);
      }

      // Try streaming endpoint first
      const streamingSupported = typeof EventSource !== 'undefined';

      if (streamingSupported) {
        try {
          console.log("Attempting streaming endpoint...");
          await loadViewWithStreaming(id, fetchedView);
          return;
        } catch (streamErr) {
          console.warn("Streaming failed, falling back to regular endpoint:", streamErr);
        }
      }

      // Fallback to non-streaming endpoint
      console.log("Fetching graph data (non-streaming)...");
      const fetchedData = await viewApi.getViewGraphData(id);
      console.log("Graph data fetched:", fetchedData);

      setView(fetchedView);
      setGraphData(fetchedData);
      setFilteredData(fetchedData);

      // Check for failed databases in metadata
      if (fetchedData.metadata?.failed_databases && fetchedData.metadata.failed_databases.length > 0) {
        const failedNames = fetchedData.metadata.failed_databases
          .map((db: FailedDatabase) => db.title)
          .join(", ");
        setWarnings([`Some databases failed to load: ${failedNames}`]);
      }

      console.log("View loaded successfully");
    } catch (err: any) {
      console.error("Error loading view:", err);
      let errorMessage = "Failed to load view";

      // Extract error message from API response
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
      setLoadingProgress(null);
      console.log("Loading complete, loading state:", false);
    }
  };

  const loadViewWithStreaming = async (id: string, fetchedView: View | null): Promise<void> => {
    return new Promise((resolve, reject) => {
      const eventSource = new EventSource(`/api/views/${id}/data?stream=true`);
      let hasReceivedData = false;

      eventSource.onmessage = (event) => {
        try {
          const update = JSON.parse(event.data);
          console.log("Streaming update:", update);

          switch (update.type) {
            case "cached_data":
              // Show cached data immediately
              setGraphData(update.data);
              setFilteredData(update.data);
              setLoadingProgress({
                type: "cached",
                message: "Showing cached data, fetching updates..."
              });
              hasReceivedData = true;
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
              setLoadingProgress({
                type: "fetching",
                progress: update.progress,
                database_name: update.database_name,
                page_count: update.page_count
              });
              break;

            case "complete":
              setView(fetchedView);
              setGraphData(update.data);
              setFilteredData(update.data);

              // Show warnings for failed databases
              if (update.data.metadata?.failed_databases && update.data.metadata.failed_databases.length > 0) {
                const failedNames = update.data.metadata.failed_databases
                  .map((db: FailedDatabase) => db.title)
                  .join(", ");
                setWarnings(prev => [
                  ...prev,
                  `Some databases failed to load: ${failedNames}`
                ]);
              }

              setLoading(false);
              setLoadingProgress(null);
              eventSource.close();
              hasReceivedData = true;
              resolve();
              break;

            case "error":
              console.error("Streaming error:", update.error);
              eventSource.close();
              reject(new Error(update.error));
              break;
          }
        } catch (parseErr) {
          console.error("Error parsing streaming update:", parseErr);
        }
      };

      eventSource.onerror = (err) => {
        console.error("EventSource error:", err);
        eventSource.close();
        if (!hasReceivedData) {
          reject(new Error("Streaming connection failed"));
        } else {
          // If we already have data, just close gracefully
          setLoading(false);
          setLoadingProgress(null);
          resolve();
        }
      };

      // Timeout after 2 minutes
      setTimeout(() => {
        if (loading) {
          eventSource.close();
          reject(new Error("Streaming timeout"));
        }
      }, 120000);
    });
  };

  const getLoadingMessage = (progress: LoadingProgress | null): string => {
    if (!progress) return "Loading view...";

    switch (progress.type) {
      case "cached":
        return progress.message || "Showing cached data, fetching updates...";
      case "fetching":
        if (progress.database_name) {
          return `Loading ${progress.database_name} (${progress.page_count} pages)...`;
        }
        if (progress.progress !== undefined) {
          return `Loading databases... ${Math.round(progress.progress * 100)}%`;
        }
        return "Loading databases...";
      default:
        return "Loading view...";
    }
  };

  const handleRetry = () => {
    if (viewId) {
      loadView(viewId);
    }
  };

  const handleSaveSettings = async (settings: ViewSettings) => {
    if (!view) return;

    try {
      await viewApi.updateView(view.id, { settings });
      setView({ ...view, settings });
    } catch (err) {
      console.error("Failed to save view settings:", err);
    }
  };

  const handleZoomChange = (zoom: number) => {
    if (view) {
      const newSettings = { ...view.settings, zoomLevel: zoom };
      handleSaveSettings(newSettings);
    }
  };

  const handlePanChange = (pan: { x: number; y: number }) => {
    if (view) {
      const newSettings = { ...view.settings, panX: pan.x, panY: pan.y };
      handleSaveSettings(newSettings);
    }
  };

  const handleSearchResult = (matchedNodes: any[]) => {
    if (!graphData) return;

    const matchedIds = new Set(matchedNodes.map((n) => n.id));
    const updatedData = {
      ...graphData,
      nodes: graphData.nodes.map((node) => ({
        ...node,
        visible: matchedIds.has(node.id),
      })),
    };

    setFilteredData(updatedData);
  };

  const handleClearSearch = () => {
    setFilteredData(graphData);
  };

  const handleDatabaseFilterChange = (selectedIds: string[]) => {
    if (!graphData) return;

    if (selectedIds.length === 0) {
      setFilteredData({ ...graphData, nodes: [], edges: [] });
      return;
    }

    const filteredNodes = graphData.nodes.filter((node) =>
      selectedIds.includes(node.databaseId)
    );

    const visibleNodeIds = new Set(filteredNodes.map((n) => n.id));
    const filteredEdges = graphData.edges.filter(
      (edge) =>
        visibleNodeIds.has(edge.sourceId) && visibleNodeIds.has(edge.targetId)
    );

    setFilteredData({
      ...graphData,
      nodes: filteredNodes,
      edges: filteredEdges,
    });
  };

  if (loading) {
    return (
      <LoadingSpinner
        message={getLoadingMessage(loadingProgress)}
        progress={loadingProgress?.progress}
      />
    );
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={handleRetry} />;
  }

  if (!filteredData) {
    return <ErrorMessage message="View not found" />;
  }

  return (
    <div className="view-page">
      {warnings.length > 0 && (
        <div className="warning-banner">
          <div className="warning-content">
            <strong>⚠️ Warning:</strong>
            <ul>
              {warnings.map((warning, index) => (
                <li key={index}>{warning}</li>
              ))}
            </ul>
          </div>
          <button
            className="warning-dismiss"
            onClick={() => setWarnings([])}
            aria-label="Dismiss warnings"
          >
            ×
          </button>
        </div>
      )}

      <div className="view-header">
        <h2>{view?.name || "Graph View"}</h2>
      </div>

      <div className="view-controls">
        <SearchBar
          nodes={graphData?.nodes || []}
          onSearchResult={handleSearchResult}
          onClearSearch={handleClearSearch}
        />
        <DatabaseFilter
          databases={graphData?.databases || []}
          selectedDatabaseIds={view?.databaseIds || []}
          onSelectionChange={handleDatabaseFilterChange}
        />
      </div>

      <div className="view-canvas">
        <GraphVisualizer
          data={filteredData}
          onZoom={handleZoomChange}
          onPan={handlePanChange}
          initialZoom={view?.settings?.zoomLevel || 1.0}
          initialPan={{ x: view?.settings?.panX || 0, y: view?.settings?.panY || 0 }}
        />
      </div>
    </div>
  );
};

export default ViewPage;
