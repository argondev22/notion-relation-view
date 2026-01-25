import React, { useState } from "react";
import { Database } from "../types";

interface DatabaseFilterProps {
  databases: Database[];
  selectedDatabaseIds: string[];
  onSelectionChange: (selectedIds: string[]) => void;
}

const DatabaseFilter: React.FC<DatabaseFilterProps> = ({
  databases,
  selectedDatabaseIds,
  onSelectionChange,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleToggleDatabase = (databaseId: string) => {
    const isSelected = selectedDatabaseIds.includes(databaseId);

    if (isSelected) {
      // Remove from selection
      onSelectionChange(
        selectedDatabaseIds.filter((id) => id !== databaseId)
      );
    } else {
      // Add to selection
      onSelectionChange([...selectedDatabaseIds, databaseId]);
    }
  };

  const handleSelectAll = () => {
    onSelectionChange(databases.map((db) => db.id));
  };

  const handleClearAll = () => {
    onSelectionChange([]);
  };

  return (
    <div className="database-filter">
      <div className="filter-header">
        <h3>Databases</h3>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="toggle-button"
        >
          {isExpanded ? "▼" : "▶"}
        </button>
      </div>

      {isExpanded && (
        <div className="filter-content">
          <div className="filter-actions">
            <button onClick={handleSelectAll} className="action-button">
              Select All
            </button>
            <button onClick={handleClearAll} className="action-button">
              Clear All
            </button>
          </div>

          <div className="database-list">
            {databases.map((database) => (
              <label key={database.id} className="database-item">
                <input
                  type="checkbox"
                  checked={selectedDatabaseIds.includes(database.id)}
                  onChange={() => handleToggleDatabase(database.id)}
                />
                <span className="database-title">{database.title}</span>
              </label>
            ))}
          </div>

          {databases.length === 0 && (
            <p className="empty-message">No databases available</p>
          )}
        </div>
      )}
    </div>
  );
};

export default DatabaseFilter;
