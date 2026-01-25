import React, { useState, useEffect } from "react";
import { viewApi } from "../api/client";
import { View } from "../types";

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

  useEffect(() => {
    loadViews();
  }, []);

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

  if (loading) {
    return <div className="view-manager loading">Loading views...</div>;
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

      {error && <div className="error-message">{error}</div>}

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
          views.map((view) => (
            <div
              key={view.id}
              className={`view-item ${
                currentViewId === view.id ? "active" : ""
              }`}
            >
              <div className="view-info">
                <h4>{view.name}</h4>
                <p className="view-databases">
                  {view.databaseIds.length} database(s)
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
          ))
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!name.trim()) {
      setError("View name is required");
      return;
    }

    setLoading(true);

    try {
      const newView = await viewApi.createView(name, []);
      onSuccess(newView);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create view");
    } finally {
      setLoading(false);
    }
  };

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

      {error && <div className="error-message">{error}</div>}

      <div className="form-actions">
        <button type="submit" disabled={loading}>
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
