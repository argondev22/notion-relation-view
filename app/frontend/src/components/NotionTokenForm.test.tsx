import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import NotionTokenForm from "./NotionTokenForm";
import { notionApi } from "../api/client";

// Mock the API client
jest.mock("../api/client");

describe("NotionTokenForm", () => {
  const mockOnSuccess = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders notion token form with instructions", () => {
    render(<NotionTokenForm onSuccess={mockOnSuccess} />);

    expect(screen.getByText(/connect notion/i)).toBeInTheDocument();
    expect(
      screen.getByText(/how to get your notion api token/i)
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/notion api token/i)).toBeInTheDocument();
  });

  it("validates token input", () => {
    render(<NotionTokenForm onSuccess={mockOnSuccess} />);

    const tokenInput = screen.getByLabelText(
      /notion api token/i
    ) as HTMLInputElement;
    expect(tokenInput.type).toBe("password");
    expect(tokenInput.required).toBe(true);
  });

  it("disables submit button when token is empty", () => {
    render(<NotionTokenForm onSuccess={mockOnSuccess} />);

    const submitButton = screen.getByRole("button", { name: /save token/i });
    expect(submitButton).toBeDisabled();
  });

  it("enables submit button when token is entered", () => {
    render(<NotionTokenForm onSuccess={mockOnSuccess} />);

    fireEvent.change(screen.getByLabelText(/notion api token/i), {
      target: { value: "secret_test_token" },
    });

    const submitButton = screen.getByRole("button", { name: /save token/i });
    expect(submitButton).not.toBeDisabled();
  });

  it("calls save token API on form submission", async () => {
    const mockSaveToken = notionApi.saveNotionToken as jest.MockedFunction<
      typeof notionApi.saveNotionToken
    >;
    mockSaveToken.mockResolvedValue({ success: true });

    render(<NotionTokenForm onSuccess={mockOnSuccess} />);

    fireEvent.change(screen.getByLabelText(/notion api token/i), {
      target: { value: "secret_test_token" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save token/i }));

    await waitFor(() => {
      expect(mockSaveToken).toHaveBeenCalledWith("secret_test_token");
      expect(mockOnSuccess).toHaveBeenCalled();
    });
  });

  it("displays error message on save failure", async () => {
    const mockSaveToken = notionApi.saveNotionToken as jest.MockedFunction<
      typeof notionApi.saveNotionToken
    >;
    mockSaveToken.mockRejectedValue(new Error("Invalid token"));

    render(<NotionTokenForm onSuccess={mockOnSuccess} />);

    fireEvent.change(screen.getByLabelText(/notion api token/i), {
      target: { value: "invalid_token" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save token/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid token/i)).toBeInTheDocument();
    });
  });

  it("disables form during submission", async () => {
    const mockSaveToken = notionApi.saveNotionToken as jest.MockedFunction<
      typeof notionApi.saveNotionToken
    >;
    mockSaveToken.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(<NotionTokenForm onSuccess={mockOnSuccess} />);

    fireEvent.change(screen.getByLabelText(/notion api token/i), {
      target: { value: "secret_test_token" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save token/i }));

    expect(screen.getByLabelText(/notion api token/i)).toBeDisabled();
    expect(screen.getByRole("button", { name: /saving/i })).toBeDisabled();
  });
});
