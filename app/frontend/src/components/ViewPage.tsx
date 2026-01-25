import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { viewApi, graphApi } from "../api/client";
import { View, GraphData, ViewSettings } from "../types";
import GraphVisualizer from "./GraphVisualizer";
import SearchBar from "./SearchBar";
import DatabaseFilter from "./DatabaseFilter";
import LoadingSpinner from "./LoadingSpinner";
import ErrorMessage from "./ErrorMessage";

const ViewPage: React.FC = () => {
  const { viewId } = useParams<{ viewId: string }>();
  const [view, setView] = useState<View | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [filteredData, setFilteredData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (viewId) {
      loadView(viewId);
    }
  }, [viewId]);

  const loadView = async (id: string) => {
    try {
      setLoading(true);
      setError("");
      const [fetchedView, fetchedData] = await Promise.all([
        viewApi.getView(id),
        viewApi.getViewGraphData(id),
      ]);

      setView(fetchedView);
      setGraphData(fetchedData);
      setFilteredData(fetchedData);
    } catch (err: any) {
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
    return <LoadingSpinner message="Loading view..." />;
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={handleRetry} />;
  }

  if (!view || !filteredData) {
    return <ErrorMessage message="View not found" />;
  }

  return (
    <div className="view-page">
      <div className="view-header">
        <h2>{view.name}</h2>
      </div>

      <div className="view-controls">
        <SearchBar
          nodes={graphData?.nodes || []}
          onSearchResult={handleSearchResult}
          onClearSearch={handleClearSearch}
        />
        <DatabaseFilter
          databases={graphData?.databases || []}
          selectedDatabaseIds={view.databaseIds}
          onSelectionChange={handleDatabaseFilterChange}
        />
      </div>

      <div className="view-canvas">
        <GraphVisualizer
          data={filteredData}
          onZoom={handleZoomChange}
          onPan={handlePanChange}
          initialZoom={view.settings.zoomLevel}
          initialPan={{ x: view.settings.panX, y: view.settings.panY }}
        />
      </div>
    </div>
  );
};

export default ViewPage;
