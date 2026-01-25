import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import DatabaseFilter from "./DatabaseFilter";
import { Database } from "../types";

describe("DatabaseFilter", () => {
  const mockDatabases: Database[] = [
    { id: "db-1", title: "Projects", hidden: false },
    { id: "db-2", title: "Tasks", hidden: false },
    { id: "db-3", title: "Notes", hidden: false },
  ];

  const mockOnSelectionChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders database filter header", () => {
    render(
      <DatabaseFilter
        databases={mockDatabases}
        selectedDatabaseIds={[]}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    expect(screen.getByText(/databases/i)).toBeInTheDocument();
  });

  it("expands when toggle button is clicked", () => {
    render(
      <DatabaseFilter
        databases={mockDatabases}
        selectedDatabaseIds={[]}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    const toggleButton = screen.getByRole("button", { name: /▶/ });
    fireEvent.click(toggleButton);

    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(screen.getByText("Tasks")).toBeInTheDocument();
    expect(screen.getByText("Notes")).toBeInTheDocument();
  });

  it("shows all databases when expanded", () => {
    render(
      <DatabaseFilter
        databases={mockDatabases}
        selectedDatabaseIds={[]}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    const toggleButton = screen.getByRole("button", { name: /▶/ });
    fireEvent.click(toggleButton);

    mockDatabases.forEach((db) => {
      expect(screen.getByText(db.title)).toBeInTheDocument();
    });
  });

  it("calls onSelectionChange when database is selected", () => {
    render(
      <DatabaseFilter
        databases={mockDatabases}
        selectedDatabaseIds={[]}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    const toggleButton = screen.getByRole("button", { name: /▶/ });
    fireEvent.click(toggleButton);

    const checkbox = screen.getByLabelText(/projects/i);
    fireEvent.click(checkbox);

    expect(mockOnSelectionChange).toHaveBeenCalledWith(["db-1"]);
  });

  it("calls onSelectionChange when database is deselected", () => {
    render(
      <DatabaseFilter
        databases={mockDatabases}
        selectedDatabaseIds={["db-1", "db-2"]}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    const toggleButton = screen.getByRole("button", { name: /▶/ });
    fireEvent.click(toggleButton);

    const checkbox = screen.getByLabelText(/projects/i);
    fireEvent.click(checkbox);

    expect(mockOnSelectionChange).toHaveBeenCalledWith(["db-2"]);
  });

  it("selects all databases when Select All is clicked", () => {
    render(
      <DatabaseFilter
        databases={mockDatabases}
        selectedDatabaseIds={[]}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    const toggleButton = screen.getByRole("button", { name: /▶/ });
    fireEvent.click(toggleButton);

    const selectAllButton = screen.getByText(/select all/i);
    fireEvent.click(selectAllButton);

    expect(mockOnSelectionChange).toHaveBeenCalledWith(["db-1", "db-2", "db-3"]);
  });

  it("clears all selections when Clear All is clicked", () => {
    render(
      <DatabaseFilter
        databases={mockDatabases}
        selectedDatabaseIds={["db-1", "db-2"]}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    const toggleButton = screen.getByRole("button", { name: /▶/ });
    fireEvent.click(toggleButton);

    const clearAllButton = screen.getByText(/clear all/i);
    fireEvent.click(clearAllButton);

    expect(mockOnSelectionChange).toHaveBeenCalledWith([]);
  });

  it("shows empty message when no databases available", () => {
    render(
      <DatabaseFilter
        databases={[]}
        selectedDatabaseIds={[]}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    const toggleButton = screen.getByRole("button", { name: /▶/ });
    fireEvent.click(toggleButton);

    expect(screen.getByText(/no databases available/i)).toBeInTheDocument();
  });

  it("handles multiple database selection", () => {
    render(
      <DatabaseFilter
        databases={mockDatabases}
        selectedDatabaseIds={["db-1"]}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    const toggleButton = screen.getByRole("button", { name: /▶/ });
    fireEvent.click(toggleButton);

    const checkbox = screen.getByLabelText(/tasks/i);
    fireEvent.click(checkbox);

    expect(mockOnSelectionChange).toHaveBeenCalledWith(["db-1", "db-2"]);
  });
});
