import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/page-header';
import { statsApi, sourcesApi } from '@/api';
import type { Stats, Source } from '@/api';
import { Rss, FileText, Settings } from 'lucide-react';

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([statsApi.get(), sourcesApi.list()])
      .then(([statsData, sourcesData]) => {
        setStats(statsData);
        setSources(sourcesData.sources);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <>
      <PageHeader title="Dashboard" description="Overview of RSS MCP Service" />

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sources</CardTitle>
            <Rss className="h-4 w-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_sources || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Articles</CardTitle>
            <FileText className="h-4 w-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_articles || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Enabled Sources</CardTitle>
            <Settings className="h-4 w-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {sources.filter((s) => s.enabled).length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Auth Enabled</CardTitle>
            <Settings className="h-4 w-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.auth_enabled ? 'Yes' : 'No'}</div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Sources */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Sources</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {sources.slice(0, 5).map((source) => (
              <div
                key={source.id}
                className="flex items-center justify-between border-b border-slate-100 pb-3 last:border-0"
              >
                <div>
                  <div className="font-medium">{source.name}</div>
                  <div className="text-sm text-slate-500">{source.url}</div>
                </div>
                <div className="text-sm text-slate-500">
                  {source.article_count || 0} articles
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </>
  );
}
