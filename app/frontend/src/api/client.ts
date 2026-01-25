import axios, { AxiosInstance, AxiosError } from "axios";
import {
  User,
  GraphData,
  Database,
  View,
  ViewSettings,
} from "../types";

// API client configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: "/api",
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// Error handling helper
const handleApiError = (error: unknown): never => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail: string }>;
    const message = axiosError.response?.data?.detail || axiosError.message;
    throw new Error(message);
  }
  throw error;
};

// Authentication API
export const authApi = {
  /**
   * Register a new user
   */
  async register(email: string, password: string): Promise<User> {
    try {
      const response = await apiClient.post<User>("/auth/register", {
        email,
        password,
      });
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  /**
   * Login user
   */
  async login(email: string, password: string): Promise<User> {
    try {
      const response = await apiClient.post<User>("/auth/login", {
        email,
        password,
      });
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post("/auth/logout");
    } catch (error) {
      handleApiError(error);
    }
  },

  /**
   * Get current user
   */
  async getCurrentUser(): Promise<User> {
    try {
      const response = await apiClient.get<User>("/auth/me");
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },
};

// Notion Token API
export const notionApi = {
  /**
   * Save Notion API token
   */
  async saveNotionToken(token: string): Promise<{ success: boolean }> {
    try {
      const response = await apiClient.post<{ success: boolean }>(
        "/notion/token",
        { token }
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  /**
   * Verify Notion API token
   */
  async verifyNotionToken(): Promise<{ valid: boolean }> {
    try {
      const response = await apiClient.get<{ valid: boolean }>(
        "/notion/token/verify"
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },
};

// Graph Data API
export const graphApi = {
  /**
   * Get complete graph data
   */
  async getGraphData(): Promise<GraphData> {
    try {
      const response = await apiClient.get<GraphData>("/graph/data");
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  /**
   * Get list of databases
   */
  async getDatabases(): Promise<Database[]> {
    try {
      const response = await apiClient.get<Database[]>("/graph/databases");
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },
};

// View Management API
export const viewApi = {
  /**
   * Create a new view
   */
  async createView(
    name: string,
    databaseIds: string[],
    settings?: ViewSettings
  ): Promise<View> {
    try {
      const response = await apiClient.post<View>("/views", {
        name,
        database_ids: databaseIds,
        settings,
      });
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  /**
   * Get all views for current user
   */
  async getViews(): Promise<View[]> {
    try {
      const response = await apiClient.get<View[]>("/views");
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  /**
   * Get a specific view by ID
   */
  async getView(viewId: string): Promise<View> {
    try {
      const response = await apiClient.get<View>(`/views/${viewId}`);
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  /**
   * Update a view
   */
  async updateView(
    viewId: string,
    updates: {
      name?: string;
      databaseIds?: string[];
      settings?: ViewSettings;
    }
  ): Promise<View> {
    try {
      const payload: Record<string, unknown> = {};
      if (updates.name !== undefined) payload.name = updates.name;
      if (updates.databaseIds !== undefined)
        payload.database_ids = updates.databaseIds;
      if (updates.settings !== undefined) payload.settings = updates.settings;

      const response = await apiClient.put<View>(`/views/${viewId}`, payload);
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  /**
   * Delete a view
   */
  async deleteView(viewId: string): Promise<void> {
    try {
      await apiClient.delete(`/views/${viewId}`);
    } catch (error) {
      handleApiError(error);
    }
  },

  /**
   * Get graph data for a specific view
   */
  async getViewGraphData(viewId: string): Promise<GraphData> {
    try {
      const response = await apiClient.get<GraphData>(
        `/views/${viewId}/data`
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },
};

export default apiClient;
