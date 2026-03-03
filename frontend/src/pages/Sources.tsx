import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/page-header';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { sourcesApi } from '@/api';
import type { Source } from '@/api';
import { Plus, RefreshCw, Trash2, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Sources() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newSource, setNewSource] = useState({ name: '', url: '', tags: '' });
  const navigate = useNavigate();

  const loadSources = () => {
    sourcesApi
      .list()
      .then((data) => setSources(data.sources))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadSources();
  }, []);

  const handleAddSource = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await sourcesApi.create({
        name: newSource.name,
        url: newSource.url,
        tags: newSource.tags.split(',').map((t) => t.trim()).filter(Boolean),
      });
      setNewSource({ name: '', url: '', tags: '' });
      setShowAddForm(false);
      loadSources();
    } catch (err) {
      console.error(err);
      alert('Failed to add source');
    }
  };

  const handleToggleEnabled = async (source: Source) => {
    try {
      await sourcesApi.enable(source.id, !source.enabled);
      loadSources();
    } catch (err) {
      console.error(err);
    }
  };

  const handleRefresh = async (sourceId: string) => {
    try {
      await sourcesApi.refresh(sourceId);
      loadSources();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (sourceId: string) => {
    if (!confirm('Are you sure you want to delete this source?')) return;
    try {
      await sourcesApi.delete(sourceId);
      loadSources();
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <>
      <PageHeader
        title="RSS Sources"
        description="Manage RSS feed sources"
      >
        <Button onClick={() => setShowAddForm(!showAddForm)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Source
        </Button>
      </PageHeader>

      {showAddForm && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Add New Source</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAddSource} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="text-sm font-medium">Name</label>
                  <Input
                    value={newSource.name}
                    onChange={(e) => setNewSource({ ...newSource, name: e.target.value })}
                    placeholder="Source name"
                    required
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">URL</label>
                  <Input
                    value={newSource.url}
                    onChange={(e) => setNewSource({ ...newSource, url: e.target.value })}
                    placeholder="https://example.com/rss"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">Tags (comma separated)</label>
                <Input
                  value={newSource.tags}
                  onChange={(e) => setNewSource({ ...newSource, tags: e.target.value })}
                  placeholder="tech, ai, news"
                />
              </div>
              <div className="flex gap-2">
                <Button type="submit">Add</Button>
                <Button type="button" variant="outline" onClick={() => setShowAddForm(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {sources.map((source) => (
          <Card key={source.id}>
            <CardContent className="py-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold">{source.name}</h3>
                    <Switch
                      checked={source.enabled}
                      onCheckedChange={() => handleToggleEnabled(source)}
                    />
                  </div>
                  <div className="text-sm text-slate-500 flex items-center gap-2 mt-1">
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:underline flex items-center gap-1"
                    >
                      {source.url}
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                  <div className="flex gap-2 mt-2">
                    {source.tags.map((tag) => (
                      <Badge key={tag} variant="secondary">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-500">
                  <span>{source.article_count || 0} articles</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleRefresh(source.id)}
                    title="Refresh"
                  >
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => navigate(`/articles?source=${source.id}`)}
                    title="View Articles"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(source.id)}
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </>
  );
}
