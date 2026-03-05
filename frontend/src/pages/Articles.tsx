import { useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { PageHeader } from '@/components/page-header';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
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
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
  const [articleDetail, setArticleDetail] = useState<Article | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
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

  const handleArticleClick = async (article: Article) => {
    setSelectedArticle(article);
    setDetailLoading(true);
    try {
      const detail = await articlesApi.get(article.id);
      setArticleDetail(detail);
    } catch (err) {
      console.error(err);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCloseDialog = () => {
    setSelectedArticle(null);
    setArticleDetail(null);
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
            <Card
              key={article.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => handleArticleClick(article)}
            >
              <CardContent className="py-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold line-clamp-2 hover:text-blue-600 transition-colors">
                      {article.title}
                    </h3>
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
                    onClick={(e) => e.stopPropagation()}
                  >
                    <Button variant="ghost" size="icon" title="View original">
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

      {/* Article Detail Dialog */}
      <Dialog open={!!selectedArticle} onOpenChange={handleCloseDialog}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle className="text-xl leading-tight">
              {detailLoading ? selectedArticle?.title : articleDetail?.title}
            </DialogTitle>
            <DialogDescription className="mt-2">
              <div className="flex items-center gap-2 text-sm">
                <Badge variant="secondary">
                  {sourceMap[selectedArticle?.source_id || ''] || 'Unknown'}
                </Badge>
                {articleDetail?.published && (
                  <span>{new Date(articleDetail.published).toLocaleString()}</span>
                )}
                {articleDetail?.author && <span>by {articleDetail.author}</span>}
              </div>
            </DialogDescription>
          </DialogHeader>

          <div className="mt-4 overflow-y-auto max-h-[60vh] pr-2">
            {detailLoading ? (
              <div className="text-center py-8">Loading content...</div>
            ) : articleDetail?.content ? (
              <div className="prose prose-slate max-w-none">
                <div className="whitespace-pre-wrap text-slate-700 leading-relaxed">
                  {articleDetail.content}
                </div>
              </div>
            ) : articleDetail?.summary ? (
              <div className="text-slate-600">
                <p className="font-medium mb-2">Summary:</p>
                <p>{articleDetail.summary}</p>
                <p className="text-sm text-slate-400 mt-4">
                  Full content not available. Click "View original" to read the full article.
                </p>
              </div>
            ) : (
              <div className="text-center text-slate-500 py-8">
                No content available for this article.
              </div>
            )}
          </div>

          <div className="mt-4 pt-4 border-t flex justify-end">
            <a
              href={articleDetail?.url || selectedArticle?.url}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button variant="outline">
                <ExternalLink className="h-4 w-4 mr-2" />
                View Original
              </Button>
            </a>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
