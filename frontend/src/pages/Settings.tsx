import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { PageHeader } from '@/components/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { statsApi, settingsApi, type Stats, type Settings } from '@/api';
import { useToast } from '@/hooks/use-toast';
import { RefreshCw, Database, Clock, Key, Save, RotateCcw, AlertCircle } from 'lucide-react';

export default function SettingsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [intervalMinutes, setIntervalMinutes] = useState(30);
  const [isSaving, setIsSaving] = useState(false);
  const [isRestarting, setIsRestarting] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statsData, settingsData] = await Promise.all([
        statsApi.get(),
        settingsApi.get(),
      ]);
      setStats(statsData);
      setSettings(settingsData);
      setIntervalMinutes(settingsData.fetch_interval_minutes);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load settings',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleIntervalChange = (value: string) => {
    const num = parseInt(value, 10);
    if (!isNaN(num)) {
      setIntervalMinutes(num);
      setHasChanges(num !== settings?.fetch_interval_minutes);
    }
  };

  const handleSave = async () => {
    if (intervalMinutes < 30) {
      toast({
        title: 'Error',
        description: 'Fetch interval must be at least 30 minutes',
        variant: 'destructive',
      });
      return;
    }

    setIsSaving(true);
    try {
      const updated = await settingsApi.update(intervalMinutes);
      setSettings(updated);
      setHasChanges(false);
      toast({
        title: 'Success',
        description: 'Settings saved. Restart scheduler to apply changes.',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to save settings',
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleRestart = async () => {
    if (!confirm('Are you sure you want to restart the scheduler?')) {
      return;
    }

    setIsRestarting(true);
    try {
      const result = await settingsApi.restart();
      toast({
        title: 'Success',
        description: result.message,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to restart scheduler',
        variant: 'destructive',
      });
    } finally {
      setIsRestarting(false);
    }
  };

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
          <CardDescription>Configure automatic RSS feed fetching interval</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-start gap-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
              <div className="text-sm text-yellow-800">
                <p className="font-medium">Important</p>
                <p>Frequent fetching may burden RSS servers. Minimum interval is 30 minutes.</p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Fetch Interval (minutes)
                </label>
                <Input
                  type="number"
                  min={30}
                  value={intervalMinutes}
                  onChange={(e) => handleIntervalChange(e.target.value)}
                  className={intervalMinutes < 30 ? 'border-red-500' : ''}
                />
                {intervalMinutes < 30 && (
                  <p className="text-sm text-red-500 mt-1">
                    Minimum interval is 30 minutes
                  </p>
                )}
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">
                  Current Setting
                </label>
                <div className="text-sm text-slate-600 py-2">
                  {settings?.fetch_interval_minutes} minutes
                  {settings?.updated_at && (
                    <span className="ml-2 text-slate-400">
                      (updated: {new Date(settings.updated_at).toLocaleString()})
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <Button
                onClick={handleSave}
                disabled={!hasChanges || intervalMinutes < 30 || isSaving}
              >
                <Save className="h-4 w-4 mr-2" />
                {isSaving ? 'Saving...' : 'Save Settings'}
              </Button>

              <Button
                variant="secondary"
                onClick={handleRestart}
                disabled={hasChanges || isRestarting}
                title={hasChanges ? 'Save changes before restarting' : 'Restart scheduler to apply changes'}
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                {isRestarting ? 'Restarting...' : 'Restart Scheduler'}
              </Button>
            </div>

            {hasChanges && (
              <p className="text-sm text-amber-600">
                You have unsaved changes. Save before restarting.
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </>
  );
}
