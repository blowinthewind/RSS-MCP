export interface Source {
  id: string;
  name: string;
  url: string;
  tags: string[];
  enabled: boolean;
  fetch_interval: number;
  last_fetched: string | null;
  created_at: string;
  updated_at: string;
  article_count?: number;
}

export interface Article {
  id: string;
  source_id: string;
  title: string;
  url: string;
  summary: string | null;
  content: string | null;
  author: string | null;
  published: string | null;
  fetched_at: string;
}

export interface SourceListResponse {
  sources: Source[];
  total: number;
}

export interface ArticleListResponse {
  items: Article[];
  total: number;
  offset: number;
  limit: number;
}

export interface Stats {
  mcp_name: string;
  mcp_version: string;
  deployment: string;
  auth_enabled: boolean;
  total_sources: number;
  total_articles: number;
}

export interface ApiErrorResponse {
  detail: string;
  message?: string;
}

export interface ApiKey {
  id: string;
  name: string;
  key_preview: string;
  created_at: string;
  last_used_at: string | null;
  is_active: boolean;
}

export interface ApiKeyCreateResponse extends ApiKey {
  key: string; // Only returned once on creation
}

export interface ApiKeyListResponse {
  items: ApiKey[];
}

const API_BASE = '/api';

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Request interceptor
async function requestInterceptor(
  endpoint: string,
  options?: RequestInit
): Promise<{ endpoint: string; options: RequestInit }> {
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const mergedOptions: RequestInit = {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options?.headers,
    },
  };

  return { endpoint, options: mergedOptions };
}

// Response interceptor
async function responseInterceptor<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = 'Request failed';
    let errorData: unknown;

    try {
      errorData = await response.json();
      errorMessage = (errorData as ApiErrorResponse).detail || (errorData as ApiErrorResponse).message || errorMessage;
    } catch {
      errorMessage = response.statusText || errorMessage;
    }

    throw new ApiError(errorMessage, response.status, errorData);
  }

  // Handle empty responses
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// Error handler
function errorHandler(error: unknown): never {
  if (error instanceof ApiError) {
    console.error(`API Error (${error.status}):`, error.message);
    throw error;
  }

  if (error instanceof TypeError && error.message === 'Failed to fetch') {
    console.error('Network error: Unable to connect to server');
    throw new ApiError('Network error: Please check your connection', 0);
  }

  console.error('Unexpected error:', error);
  throw new ApiError('An unexpected error occurred', 500);
}

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  try {
    // Apply request interceptor
    const { endpoint: processedEndpoint, options: processedOptions } = await requestInterceptor(
      endpoint,
      options
    );

    const response = await fetch(`${API_BASE}${processedEndpoint}`, processedOptions);

    // Apply response interceptor
    return await responseInterceptor<T>(response);
  } catch (error) {
    return errorHandler(error);
  }
}

export const sourcesApi = {
  list: (params?: { tags?: string; enabled?: boolean }) => {
    const searchParams = new URLSearchParams();
    if (params?.tags) searchParams.set('tags', params.tags);
    if (params?.enabled !== undefined) searchParams.set('enabled', String(params.enabled));
    const query = searchParams.toString();
    return fetchApi<SourceListResponse>(`/sources${query ? `?${query}` : ''}`);
  },

  get: (id: string) => fetchApi<Source>(`/sources/${id}`),

  create: (data: { name: string; url: string; tags?: string[]; fetch_interval?: number }) =>
    fetchApi<Source>('/sources', { method: 'POST', body: JSON.stringify(data) }),

  update: (id: string, data: Partial<Source>) =>
    fetchApi<Source>(`/sources/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  delete: (id: string) => fetchApi<void>(`/sources/${id}`, { method: 'DELETE' }),

  enable: (id: string, enabled: boolean) =>
    fetchApi<void>(`/sources/${id}/enable?enabled=${enabled}`, { method: 'POST' }),

  refresh: (id: string) =>
    fetchApi<{ success: boolean; message: string }>(`/sources/${id}/refresh`, { method: 'POST' }),
};

export const articlesApi = {
  list: (params?: { source_id?: string; limit?: number; offset?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.source_id) searchParams.set('source_ids', params.source_id);
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.offset) searchParams.set('offset', String(params.offset));
    const query = searchParams.toString();
    return fetchApi<ArticleListResponse>(`/feeds${query ? `?${query}` : ''}`);
  },

  search: (params: {
    q: string;
    sources?: string;
    tags?: string;
    limit?: number;
    offset?: number;
  }) => {
    const searchParams = new URLSearchParams();
    searchParams.set('q', params.q);
    if (params.sources) searchParams.set('sources', params.sources);
    if (params.tags) searchParams.set('tags', params.tags);
    if (params.limit) searchParams.set('limit', String(params.limit));
    if (params.offset) searchParams.set('offset', String(params.offset));
    return fetchApi<ArticleListResponse>(`/search?${searchParams}`);
  },

  get: (id: string) => fetchApi<Article>(`/articles/${id}`),
};

export const statsApi = {
  get: () => fetchApi<Stats>('/stats'),
};

export const apiKeysApi = {
  list: () => fetchApi<ApiKeyListResponse>('/api-keys'),

  create: (name: string) =>
    fetchApi<ApiKeyCreateResponse>('/api-keys', {
      method: 'POST',
      body: JSON.stringify({ name }),
    }),

  delete: (id: string) => fetchApi<void>(`/api-keys/${id}`, { method: 'DELETE' }),

  revoke: (id: string) =>
    fetchApi<ApiKey>(`/api-keys/${id}/revoke`, { method: 'POST' }),
};

export interface Settings {
  fetch_interval_minutes: number;
  updated_at: string | null;
}

export interface RestartResponse {
  success: boolean;
  message: string;
}

export const settingsApi = {
  get: () => fetchApi<Settings>('/settings'),

  update: (fetch_interval_minutes: number) =>
    fetchApi<Settings>('/settings', {
      method: 'PATCH',
      body: JSON.stringify({ fetch_interval_minutes }),
    }),

  restart: () =>
    fetchApi<RestartResponse>('/settings/restart', { method: 'POST' }),
};
