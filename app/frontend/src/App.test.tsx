import React from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "./App";

jest.mock("./components/AuthProvider", () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
}));

jest.mock("./components/AuthPage", () => ({
  __esModule: true,
  default: () => <div>AuthPage Mock</div>,
}));

jest.mock("./components/ViewManager", () => ({
  __esModule: true,
  default: () => <div>ViewManager Mock</div>,
}));

jest.mock("./components/ViewPage", () => ({
  __esModule: true,
  default: () => <div>ViewPage Mock</div>,
}));

describe("App", () => {
  it("renders welcome message", () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );
    expect(screen.getByText("Notion Relation View")).toBeInTheDocument();
  });
});
