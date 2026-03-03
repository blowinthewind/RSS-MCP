import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { PageHeader } from '@/components/page-header';
import { Badge } from '@/components/ui/badge';
import { statsApi } from '@/api';
import type { Stats } from '@/api';
import { RefreshCw, Database, Clock, Key } from 'lucide-react';

export default function Settings() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    statsApi
      .get()
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <>
      <PageHeader title="Settings" description="Service configuration and status" />

      {/* Service Info */}
      <div className="grid gap-4 md:grid-cols-2 mb-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <RefreshCw className="h-5 w-5" />
              Service Info
            </CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-slate-500">Service Name</dt>
                <dd className="font-medium">{stats?.mcp_name}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Version</dt>
                <dd className="font-medium">{stats?.mcp_version}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Deployment Mode</dt>
                <dd className="font-medium uppercase">{stats?.deployment}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              Authentication
            </CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-slate-500">Auth Enabled</dt>
                <dd>
                  <Badge variant={stats?.auth_enabled ? 'success' : 'secondary'}>
                    {stats?.auth_enabled ? 'Yes' : 'No'}
                  </Badge>
                </dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      </div>

      {/* Database Info */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Database
          </CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate-500">Total Sources</dt>
              <dd className="font-medium">{stats?.total_sources}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Total Articles</dt>
              <dd className="font-medium">{stats?.total_articles}</dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      {/* RSS Fetching Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            RSS Fetching
          </CardTitle>
          <CardDescription>Current RSS fetching configuration</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-600">
            RSS feeds are automatically fetched every 5 minutes. You can configure this by setting
            the DEFAULT_FETCH_INTERVAL environment variable.
          </p>
        </CardContent>
      </Card>
    </>
  );
}
