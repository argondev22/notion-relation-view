import React, { useState } from "react";
import { Node } from "../types";

interface SearchBarProps {
  nodes: Node[];
  onSearchResult: (matchedNodes: Node[]) => void;
  onClearSearch: () => void;
}

const SearchBar: React.FC<SearchBarProps> = ({
  nodes,
  onSearchResult,
  onClearSearch,
}) => {
  const [searchQuery, setSearchQuery] = useState("");

  const handleSearch = (query: string) => {
    setSearchQuery(query);

    if (!query.trim()) {
      onClearSearch();
      return;
    }

    // Search for nodes matching the query (case-insensitive)
    const lowerQuery = query.toLowerCase();
    const matchedNodes = nodes.filter((node) =>
      node.title.toLowerCase().includes(lowerQuery)
    );

    onSearchResult(matchedNodes);
  };

  const handleClear = () => {
    setSearchQuery("");
    onClearSearch();
  };

  return (
    <div className="search-bar">
      <input
        type="text"
        value={searchQuery}
        onChange={(e) => handleSearch(e.target.value)}
        placeholder="Search nodes..."
        className="search-input"
      />
      {searchQuery && (
        <button onClick={handleClear} className="clear-button">
          Clear
        </button>
      )}
    </div>
  );
};

export default SearchBar;
