import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import ViewManager from "./ViewManager";
import { viewApi } from "../api/client";
import { View } from "../types";

jest.mock("../api/client");

const mockViewApi = viewApi as jest.Mocked<typeof viewApi>;

describe("ViewManager", () => {
  const mockViews: View[] = [
    {
      id: "view-1",
      userId: "user-1",
      name: "Test View 1",
      databaseIds: ["db-1", "db-2"],
      settings: { zoomLevel: 1, panX: 0, panY: 0 },
      createdAt: "2024-01-01T00:00:00Z",
      updatedAt: "2024-01-01T00:00:00Z",
    },
    {
      id: "view-2",
      userId: "user-1",
      name: "Test View 2",
      databaseIds: ["db-3"],
      settings: { zoomLevel: 1.5, panX: 10, panY: 20 },
      createdAt: "2024-01-02T00:00:00Z",
      updatedAt: "2024-01-02T00:00:00Z",
    },
  ];

  const mockOnViewSelect = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockViewApi.getViews.mockResolvedValue(mockViews);
  });

  it("renders loading state initially", () => {
    render(<ViewManager onViewSelect={mockOnViewSelect} />);
    expect(screen.getByText("Loading views...")).toBeInTheDocument();
  });

  it("renders view list after loading", async () => {
    render(<ViewManager onViewSelect={mockOnViewSelect} />);

    await waitFor(() => {
      expect(screen.getByText("Test View 1")).toBeInTheDocument();
      expect(screen.getByText("Test View 2")).toBeInTheDocument();
    });
  });

  it("displays database count for each view", async () => {
    render(<ViewManager onViewSelect={mockOnViewSelect} />);

    await waitFor(() => {
      expect(screen.getByText("2 database(s)")).toBeInTheDocument();
      expect(screen.getByText("1 database(s)")).toBeInTheDocument();
    });
  });

  it("shows empty message when no views exist", async () => {
    mockViewApi.getViews.mockResolvedValue([]);

    render(<ViewManager onViewSelect={mockOnViewSelect} />);

    await waitFor(() => {
      expect(
        screen.getByText("No views yet. Create your first view!")
      ).toBeInTheDocument();
    });
  });

  it("calls onViewSelect when Open button is clicked", async () => {
    render(<ViewManager onViewSelect={mockOnViewSelect} />);

    await waitFor(() => {
      expect(screen.getByText("Test View 1")).toBeInTheDocument();
    });

    const openButtons = screen.getAllByText("Open");
    fireEvent.click(openButtons[0]);

    expect(mockOnViewSelect).toHaveBeenCalledWith(mockViews[0]);
  });

  it("copies view URL to clipboard when Copy URL button is clicked", async () => {
    const mockClipboard = {
      writeText: jest.fn().mockResolvedValue(undefined),
    };
    Object.assign(navigator, { clipboard: mockClipboard });

    window.alert = jest.fn();

    render(<ViewManager onViewSelect={mockOnViewSelect} />);

    await waitFor(() => {
      expect(screen.getByText("Test View 1")).toBeInTheDocument();
    });

    const copyButtons = screen.getAllByText("Copy URL");
    fireEvent.click(copyButtons[0]);

    expect(mockClipboard.writeText).toHaveBeenCalledWith(
      `${window.location.origin}/view/view-1`
    );
    expect(window.alert).toHaveBeenCalledWith(
      "View URL copied to clipboard!"
    );
  });

  it("shows delete confirmation dialog when Delete button is clicked", async () => {
    window.confirm = jest.fn().mockReturnValue(false);

    render(<ViewManager onViewSelect={mockOnViewSelect} />);

    await waitFor(() => {
      expect(screen.getByText("Test View 1")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByText("Delete");
    fireEvent.click(deleteButtons[0]);

    expect(window.confirm).toHaveBeenCalledWith(
      "Are you sure you want to delete this view?"
    );
    expect(mockViewApi.deleteView).not.toHaveBeenCalled();
  });

  it("deletes view when confirmed", async () => {
    window.confirm = jest.fn().mockReturnValue(true);
    mockViewApi.deleteView.mockResolvedValue(undefined);
    mockViewApi.getViews
      .mockResolvedValueOnce(mockViews)
      .mockResolvedValueOnce([mockViews[1]]);

    render(<ViewManager onViewSelect={mockOnViewSelect} />);

    await waitFor(() => {
      expect(screen.getByText("Test View 1")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByText("Delete");
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(mockViewApi.deleteView).toHaveBeenCalledWith("view-1");
    });
  });

  it("shows create view form when Create View button is clicked", async () => {
    render(<ViewManager onViewSelect={mockOnViewSelect} />);

    await waitFor(() => {
      expect(screen.getByText("Create View")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Create View"));

    expect(screen.getByLabelText("View Name")).toBeInTheDocument();
    const cancelButtons = screen.getAllByText("Cancel");
    expect(cancelButtons.length).toBeGreaterThan(0);
  });

  it("creates new view when form is submitted", async () => {
    const newView: View = {
      id: "view-3",
      userId: "user-1",
      name: "New View",
      databaseIds: [],
      settings: { zoomLevel: 1, panX: 0, panY: 0 },
      createdAt: "2024-01-03T00:00:00Z",
      updatedAt: "2024-01-03T00:00:00Z",
    };

    mockViewApi.createView.mockResolvedValue(newView);

    render(<ViewManager onViewSelect={mockOnViewSelect} />);

    await waitFor(() => {
      expect(screen.getByText("Create View")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Create View"));

    const input = screen.getByLabelText("View Name");
    fireEvent.change(input, { target: { value: "New View" } });

    const createButton = screen.getByRole("button", { name: "Create" });
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(mockViewApi.createView).toHaveBeenCalledWith("New View", []);
      expect(mockOnViewSelect).toHaveBeenCalledWith(newView);
    });
  });

  it("shows error message when view creation fails", async () => {
    mockViewApi.createView.mockRejectedValue(new Error("Creation failed"));

    render(<ViewManager onViewSelect={mockOnViewSelect} />);

    await waitFor(() => {
      expect(screen.getByText("Create View")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Create View"));

    const input = screen.getByLabelText("View Name");
    fireEvent.change(input, { target: { value: "New View" } });

    const createButton = screen.getByRole("button", { name: "Create" });
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(screen.getByText("Creation failed")).toBeInTheDocument();
    });
  });

  it("highlights current view when currentViewId is provided", async () => {
    render(
      <ViewManager onViewSelect={mockOnViewSelect} currentViewId="view-1" />
    );

    await waitFor(() => {
      const viewItems = screen.getAllByRole("generic").filter((el) =>
        el.className.includes("view-item")
      );
      const activeView = viewItems.find((el) =>
        el.className.includes("active")
      );
      expect(activeView).toBeInTheDocument();
    });
  });

  it("displays error message when loading views fails", async () => {
    mockViewApi.getViews.mockRejectedValue(new Error("Failed to load"));

    render(<ViewManager onViewSelect={mockOnViewSelect} />);

    await waitFor(() => {
      expect(screen.getByText("Failed to load")).toBeInTheDocument();
    });
  });
});
