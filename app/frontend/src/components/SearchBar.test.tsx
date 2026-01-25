import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import SearchBar from "./SearchBar";
import { Node } from "../types";

describe("SearchBar", () => {
  const mockNodes: Node[] = [
    {
      id: "node-1",
      title: "Project Alpha",
      databaseId: "db-1",
      x: 0,
      y: 0,
      visible: true,
    },
    {
      id: "node-2",
      title: "Project Beta",
      databaseId: "db-1",
      x: 100,
      y: 100,
      visible: true,
    },
    {
      id: "node-3",
      title: "Task Gamma",
      databaseId: "db-2",
      x: 200,
      y: 200,
      visible: true,
    },
  ];

  const mockOnSearchResult = jest.fn();
  const mockOnClearSearch = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders search input", () => {
    render(
      <SearchBar
        nodes={mockNodes}
        onSearchResult={mockOnSearchResult}
        onClearSearch={mockOnClearSearch}
      />
    );

    expect(screen.getByPlaceholderText(/search nodes/i)).toBeInTheDocument();
  });

  it("calls onSearchResult with matching nodes", () => {
    render(
      <SearchBar
        nodes={mockNodes}
        onSearchResult={mockOnSearchResult}
        onClearSearch={mockOnClearSearch}
      />
    );

    const input = screen.getByPlaceholderText(/search nodes/i);
    fireEvent.change(input, { target: { value: "Project" } });

    expect(mockOnSearchResult).toHaveBeenCalledWith([
      mockNodes[0],
      mockNodes[1],
    ]);
  });

  it("performs case-insensitive search", () => {
    render(
      <SearchBar
        nodes={mockNodes}
        onSearchResult={mockOnSearchResult}
        onClearSearch={mockOnClearSearch}
      />
    );

    const input = screen.getByPlaceholderText(/search nodes/i);
    fireEvent.change(input, { target: { value: "project" } });

    expect(mockOnSearchResult).toHaveBeenCalledWith([
      mockNodes[0],
      mockNodes[1],
    ]);
  });

  it("calls onClearSearch when input is cleared", () => {
    render(
      <SearchBar
        nodes={mockNodes}
        onSearchResult={mockOnSearchResult}
        onClearSearch={mockOnClearSearch}
      />
    );

    const input = screen.getByPlaceholderText(/search nodes/i);
    fireEvent.change(input, { target: { value: "Project" } });
    fireEvent.change(input, { target: { value: "" } });

    expect(mockOnClearSearch).toHaveBeenCalled();
  });

  it("shows clear button when search query exists", () => {
    render(
      <SearchBar
        nodes={mockNodes}
        onSearchResult={mockOnSearchResult}
        onClearSearch={mockOnClearSearch}
      />
    );

    const input = screen.getByPlaceholderText(/search nodes/i);
    fireEvent.change(input, { target: { value: "Project" } });

    expect(screen.getByText(/clear/i)).toBeInTheDocument();
  });

  it("clears search when clear button is clicked", () => {
    render(
      <SearchBar
        nodes={mockNodes}
        onSearchResult={mockOnSearchResult}
        onClearSearch={mockOnClearSearch}
      />
    );

    const input = screen.getByPlaceholderText(/search nodes/i);
    fireEvent.change(input, { target: { value: "Project" } });

    const clearButton = screen.getByText(/clear/i);
    fireEvent.click(clearButton);

    expect(mockOnClearSearch).toHaveBeenCalled();
    expect(input).toHaveValue("");
  });

  it("handles empty search results", () => {
    render(
      <SearchBar
        nodes={mockNodes}
        onSearchResult={mockOnSearchResult}
        onClearSearch={mockOnClearSearch}
      />
    );

    const input = screen.getByPlaceholderText(/search nodes/i);
    fireEvent.change(input, { target: { value: "NonexistentNode" } });

    expect(mockOnSearchResult).toHaveBeenCalledWith([]);
  });
});
