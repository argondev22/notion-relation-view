import React from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "./App";

jest.mock("./components/AuthProvider", () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  useAuth: () => ({
    user: null,
    loading: false,
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(),
    refreshUser: jest.fn(),
  }),
}));

jest.mock("./components/AuthPage", () => ({
  __esModule: true,
  default: ({ onSuccess }: { onSuccess: () => void }) => (
    <div>
      AuthPage Mock
      <button onClick={onSuccess}>Login Success</button>
    </div>
  ),
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
