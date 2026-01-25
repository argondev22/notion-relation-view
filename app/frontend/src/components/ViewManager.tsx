import React, { useState, useEffect } from "react";
import { viewApi, notionApi, graphApi } from "../api/client";
import { View } from "../types";
import LoadingSpinner from "./LoadingSpinner";
import ErrorMessage from "./ErrorMessage";
import NotionTokenForm from "./NotionTokenForm";

interface ViewManagerProps {
  onViewSelect: (view: View) => void;
  currentViewId?: string;
}

const ViewManager: React.FC<ViewManagerProps> = ({
  onViewSelect,
  currentViewId,
}) => {
  const [views, setViews] = useState<View[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [hasNotionToken, setHasNotionToken] = useState(false);
  const [checkingToken, setCheckingToken] = useState(true);

  useEffect(() => {
    checkNotionToken();
    loadViews();
  }, []);

  const checkNotionToken = async () => {
    try {
      setCheckingToken(true);
      const result = await notionApi.verifyNotionToken();
      setHasNotionToken(result.valid);
    } catch (err) {
      setHasNotionToken(false);
    } finally {
      setCheckingToken(false);
    }
  };

  const handleTokenSaved = () => {
    setHasNotionToken(true);
    loadViews();
  };

  const loadViews = async () => {
    try {
      setLoading(true);
      const fetchedViews = await viewApi.getViews();
      setViews(fetchedViews);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load views");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteView = async (viewId: string) => {
    if (!confirm("Are you sure you want to delete this view?")) {
      return;
    }

    try {
      await viewApi.deleteView(viewId);
      await loadViews();
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete view");
    }
  };

  const handleCopyUrl = (view: View) => {
    const url = `${window.location.origin}/view/${view.id}`;
    navigator.clipboard.writeText(url);
    alert("View URL copied to clipboard!");
  };

  if (loading || checkingToken) {
    return <LoadingSpinner message="Loading views..." />;
  }

  // Show Notion Token form if no token is saved
  if (!hasNotionToken) {
    return (
      <div className="view-manager">
        <div className="notion-token-section">
          <h3>Connect to Notion</h3>
          <p>
            Please save your Notion Integration Token to start creating views.
          </p>
          <NotionTokenForm onSuccess={handleTokenSaved} />
        </div>
      </div>
    );
  }

  return (
    <div className="view-manager">
      <div className="view-manager-header">
        <h3>My Views</h3>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="create-view-button"
        >
          {showCreateForm ? "Cancel" : "Create View"}
        </button>
      </div>

      {error && <ErrorMessage message={error} onRetry={loadViews} />}

      {showCreateForm && (
        <CreateViewForm
          onSuccess={(newView) => {
            setViews([...views, newView]);
            setShowCreateForm(false);
            onViewSelect(newView);
          }}
          onCancel={() => setShowCreateForm(false)}
        />
      )}

      <div className="view-list">
        {views.length === 0 ? (
          <p className="empty-message">
            No views yet. Create your first view!
          </p>
        ) : (
          views.map((view) => {
            // Handle both camelCase and snake_case from backend
            const databaseIds = (view as any).database_ids || view.databaseIds || [];

            return (
              <div
                key={view.id}
                className={`view-item ${
                  currentViewId === view.id ? "active" : ""
                }`}
              >
                <div className="view-info">
                  <h4>{view.name}</h4>
                  <p className="view-databases">
                    {databaseIds.length} database(s)
                  </p>
                </div>
                <div className="view-actions">
                  <button
                    onClick={() => onViewSelect(view)}
                    className="select-button"
                  >
                    Open
                  </button>
                  <button
                    onClick={() => handleCopyUrl(view)}
                    className="copy-button"
                  >
                    Copy URL
                  </button>
                  <button
                    onClick={() => handleDeleteView(view.id)}
                    className="delete-button"
                  >
                    Delete
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

interface CreateViewFormProps {
  onSuccess: (view: View) => void;
  onCancel: () => void;
}

const CreateViewForm: React.FC<CreateViewFormProps> = ({
  onSuccess,
  onCancel,
}) => {
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [databases, setDatabases] = useState<any[]>([]);
  const [selectedDatabaseIds, setSelectedDatabaseIds] = useState<string[]>([]);
  const [loadingDatabases, setLoadingDatabases] = useState(true);

  useEffect(() => {
    loadDatabases();
  }, []);

  const loadDatabases = async () => {
    try {
      setLoadingDatabases(true);
      const fetchedDatabases = await graphApi.getDatabases();
      setDatabases(fetchedDatabases);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load databases");
    } finally {
      setLoadingDatabases(false);
    }
  };

  const handleDatabaseToggle = (databaseId: string) => {
    setSelectedDatabaseIds((prev) =>
      prev.includes(databaseId)
        ? prev.filter((id) => id !== databaseId)
        : [...prev, databaseId]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!name.trim()) {
      setError("View name is required");
      return;
    }

    if (selectedDatabaseIds.length === 0) {
      setError("Please select at least one database");
      return;
    }

    setLoading(true);

    try {
      const newView = await viewApi.createView(name, selectedDatabaseIds);
      onSuccess(newView);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create view");
    } finally {
      setLoading(false);
    }
  };

  if (loadingDatabases) {
    return (
      <div className="create-view-form">
        <LoadingSpinner message="Loading databases..." />
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="create-view-form">
      <div className="form-group">
        <label htmlFor="viewName">View Name</label>
        <input
          id="viewName"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="My Graph View"
          disabled={loading}
          required
        />
      </div>

      <div className="form-group">
        <label>Select Databases</label>
        {databases.length === 0 ? (
          <p className="empty-message">
            No databases found. Make sure your Notion integration has access to
            databases.
          </p>
        ) : (
          <div className="database-selection">
            {databases.map((db) => (
              <label key={db.id} className="database-checkbox">
                <input
                  type="checkbox"
                  checked={selectedDatabaseIds.includes(db.id)}
                  onChange={() => handleDatabaseToggle(db.id)}
                  disabled={loading}
                />
                <span>{db.title}</span>
              </label>
            ))}
          </div>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="form-actions">
        <button type="submit" disabled={loading || databases.length === 0}>
          {loading ? "Creating..." : "Create"}
        </button>
        <button type="button" onClick={onCancel} disabled={loading}>
          Cancel
        </button>
      </div>
    </form>
  );
};

export default ViewManager;
