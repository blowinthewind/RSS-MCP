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

const API_BASE = '/api';

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || 'Request failed');
  }
  
  return response.json();
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
  
  refresh: (id: string) => fetchApi<{ success: boolean; message: string }>(`/sources/${id}/refresh`, { method: 'POST' }),
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
  
  search: (params: { q: string; sources?: string; tags?: string; limit?: number; offset?: number }) => {
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
  get: () => fetchApi<Stats>('/'),
};
