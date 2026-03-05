import { useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { PageHeader } from '@/components/page-header';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { sourcesApi, articlesApi } from '@/api';
import type { Source, Article } from '@/api';
import { Search, ExternalLink, ChevronLeft, ChevronRight } from 'lucide-react';

export default function Articles() {
  const [sources, setSources] = useState<Source[]>([]);
  const [articles, setArticles] = useState<Article[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchInput, setSearchInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSource, setSelectedSource] = useState('');
  const [page, setPage] = useState(0);
  const limit = 20;

  const loadSources = () => {
    sourcesApi
      .list()
      .then((data) => setSources(data.sources))
      .catch(console.error);
  };

  const loadArticles = () => {
    setLoading(true);
    const promise = searchQuery
      ? articlesApi.search({ q: searchQuery, limit, offset: page * limit })
      : articlesApi.list({ source_id: selectedSource || undefined, limit, offset: page * limit });

    promise
      .then((data) => {
        setArticles(data.items);
        setTotal(data.total);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const handleSearch = () => {
    setSearchQuery(searchInput);
    setPage(0);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  useEffect(() => {
    loadSources();
  }, []);

  useEffect(() => {
    loadArticles();
  }, [searchQuery, selectedSource, page]);

  const totalPages = Math.ceil(total / limit);
  const sourceMap = sources.reduce((acc, s) => {
    acc[s.id] = s.name;
    return acc;
  }, {} as Record<string, string>);

  return (
    <>
      <PageHeader title="Articles" description="Browse and search articles" />

      {/* Search and Filters */}
      <Card className="mb-6">
        <CardContent className="py-4">
          <div className="flex gap-4 flex-wrap">
            <div className="flex-1 min-w-[200px]">
              <div className="relative flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Search articles..."
                    className="pl-10"
                  />
                </div>
                <Button onClick={handleSearch}>
                  <Search className="h-4 w-4 mr-2" />
                  Search
                </Button>
              </div>
            </div>
            <select
              value={selectedSource}
              onChange={(e) => {
                setSelectedSource(e.target.value);
                setPage(0);
              }}
              className="h-10 px-3 rounded-md border border-slate-300 bg-white text-sm"
            >
              <option value="">All Sources</option>
              {sources.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Articles List */}
      <div className="space-y-4">
        {loading ? (
          <div>Loading...</div>
        ) : articles.length === 0 ? (
          <div className="text-center py-12 text-slate-500">No articles found</div>
        ) : (
          articles.map((article) => (
            <Card key={article.id}>
              <CardContent className="py-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold line-clamp-2">{article.title}</h3>
                    <div className="flex items-center gap-2 mt-2 text-sm text-slate-500">
                      <Badge variant="secondary">{sourceMap[article.source_id] || 'Unknown'}</Badge>
                      {article.published && (
                        <span>{new Date(article.published).toLocaleDateString()}</span>
                      )}
                      {article.author && <span>by {article.author}</span>}
                    </div>
                    {article.summary && (
                      <p className="text-sm text-slate-600 mt-2 line-clamp-3">
                        {article.summary}
                      </p>
                    )}
                  </div>
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="shrink-0"
                  >
                    <Button variant="ghost" size="icon">
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </a>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-6">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-sm text-slate-500">
            Page {page + 1} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </>
  );
}
