import { ApiResponse, PaginatedResponse, LoginCredentials, AuthResponse } from '../../../shared/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public data?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

class ApiService {
  private baseURL: string;
  private defaultHeaders: Record<string, string>;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  private getAuthHeaders(): Record<string, string> {
    if (typeof window === 'undefined') return {};

    const token = localStorage.getItem('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      ...this.defaultHeaders,
      ...this.getAuthHeaders(),
      ...options.headers,
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new ApiError(
          data.detail || `HTTP error! status: ${response.status}`,
          response.status,
          data
        );
      }

      return data;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // Authentication endpoints
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    return this.request<AuthResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async logout(): Promise<{ message: string }> {
    return this.request<{ message: string }>('/api/v1/auth/logout', {
      method: 'POST',
    });
  }

  async getCurrentUser() {
    return this.request('/api/v1/auth/me');
  }

  async changePassword(data: { current_password: string; new_password: string }) {
    return this.request('/api/v1/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async refreshToken(): Promise<{ access_token: string; token_type: string }> {
    return this.request('/api/v1/auth/refresh', {
      method: 'POST',
    });
  }

  // Infection case endpoints
  async getInfectionCases(params?: {
    verification_status?: string;
    pathogen_type?: string;
    date_from?: string;
    date_to?: string;
    page?: number;
    limit?: number;
    search?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value.toString());
        }
      });
    }

    const queryString = searchParams.toString();
    const endpoint = `/api/v1/cases${queryString ? `?${queryString}` : ''}`;

    return this.request(endpoint);
  }

  async getInfectionCase(id: string) {
    return this.request(`/api/v1/cases/${id}`);
  }

  async createInfectionCase(data: any) {
    return this.request('/api/v1/cases', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateInfectionCase(id: string, data: any) {
    return this.request(`/api/v1/cases/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async verifyInfectionCase(id: string, data: { verification_status: string; notes?: string }) {
    return this.request(`/api/v1/cases/${id}/verify`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async deleteInfectionCase(id: string) {
    return this.request(`/api/v1/cases/${id}`, {
      method: 'DELETE',
    });
  }

  // Verification token endpoints
  async getVerificationTokens(params?: {
    infection_case_id?: string;
    token_type?: string;
    is_active?: boolean;
    page?: number;
    limit?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value.toString());
        }
      });
    }

    const queryString = searchParams.toString();
    const endpoint = `/api/v1/tokens${queryString ? `?${queryString}` : ''}`;

    return this.request(endpoint);
  }

  async createVerificationToken(data: any) {
    return this.request('/api/v1/tokens', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getVerificationToken(id: string) {
    return this.request(`/api/v1/tokens/${id}`);
  }

  async revokeVerificationToken(id: string) {
    return this.request(`/api/v1/tokens/${id}/revoke`, {
      method: 'POST',
    });
  }

  async getTokenStatus(id: string) {
    return this.request(`/api/v1/tokens/${id}/status`);
  }

  // Analytics endpoints
  async getKPIMetrics() {
    return this.request('/api/v1/analytics/kpi');
  }

  async getComplianceStats() {
    return this.request('/api/v1/analytics/compliance');
  }

  async getTrendData(metric: string, period: string = '7d') {
    return this.request(`/api/v1/analytics/trends?metric=${metric}&period=${period}`);
  }

  async getClusterAnalysis(params?: {
    location?: string;
    risk_level?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value.toString());
        }
      });
    }

    const queryString = searchParams.toString();
    const endpoint = `/api/v1/analytics/clusters${queryString ? `?${queryString}` : ''}`;

    return this.request(endpoint);
  }

  async getAnalyticsSnapshots(params?: {
    date_from?: string;
    date_to?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value.toString());
        }
      });
    }

    const queryString = searchParams.toString();
    const endpoint = `/api/v1/analytics/snapshots${queryString ? `?${queryString}` : ''}`;

    return this.request(endpoint);
  }

  // Dashboard endpoints
  async getDashboardOverview() {
    return this.request('/api/v1/dashboard/overview');
  }

  async getHeatmapData(hoursBack: number = 24) {
    return this.request(`/api/v1/dashboard/heatmap?hours_back=${hoursBack}`);
  }

  async getSystemHealth() {
    return this.request('/api/v1/dashboard/system-health');
  }

  async getAuditLogs(params?: {
    page?: number;
    limit?: number;
    action?: string;
    resource_type?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value.toString());
        }
      });
    }

    const queryString = searchParams.toString();
    const endpoint = `/api/v1/dashboard/audit-logs${queryString ? `?${queryString}` : ''}`;

    return this.request(endpoint);
  }

  async getDashboardAlerts(params?: {
    hours_back?: number;
    acknowledged?: boolean;
    alert_type?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value.toString());
        }
      });
    }

    const queryString = searchParams.toString();
    const endpoint = `/api/v1/dashboard/alerts${queryString ? `?${queryString}` : ''}`;

    return this.request(endpoint);
  }

  async acknowledgeAlert(alertId: string, notes?: string) {
    return this.request(`/api/v1/dashboard/alerts/${alertId}/acknowledge`, {
      method: 'POST',
      body: JSON.stringify({ notes }),
    });
  }

  async getDashboardStatsSummary() {
    return this.request('/api/v1/dashboard/stats/summary');
  }

  // Health check
  async healthCheck() {
    return this.request('/health');
  }
}

export const apiService = new ApiService();
export { ApiError };