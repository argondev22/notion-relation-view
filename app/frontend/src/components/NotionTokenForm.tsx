import React, { useState } from "react";
import { notionApi } from "../api/client";

interface NotionTokenFormProps {
  onSuccess: () => void;
}

const NotionTokenForm: React.FC<NotionTokenFormProps> = ({ onSuccess }) => {
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await notionApi.saveNotionToken(token);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save token");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="notion-token-form">
      <h2>Connect Notion</h2>
      <p className="form-description">
        Enter your Notion API token to visualize your page relations.
      </p>

      <div className="help-section">
        <h3>How to get your Notion API token:</h3>
        <ol>
          <li>Go to Notion Settings & Members</li>
          <li>Navigate to "Integrations"</li>
          <li>Create a new integration or use an existing one</li>
          <li>Copy the "Internal Integration Token"</li>
          <li>Share your databases with the integration</li>
        </ol>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="token">Notion API Token</label>
          <input
            id="token"
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            required
            disabled={loading}
            placeholder="secret_..."
          />
        </div>

        {error && <div className="error-message">{error}</div>}

        <button type="submit" disabled={loading || !token}>
          {loading ? "Saving..." : "Save Token"}
        </button>
      </form>
    </div>
  );
};

export default NotionTokenForm;
