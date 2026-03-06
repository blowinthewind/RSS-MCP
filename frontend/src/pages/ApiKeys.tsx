import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { PageHeader } from '@/components/page-header';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Plus, Trash2, Copy, Check, AlertCircle } from 'lucide-react';
import { apiKeysApi, type ApiKey, type ApiKeyCreateResponse } from '@/api';
import { useToast } from '@/hooks/use-toast';

export default function ApiKeys() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [newlyCreatedKey, setNewlyCreatedKey] = useState<ApiKeyCreateResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  // Load API keys on mount
  useEffect(() => {
    loadApiKeys();
  }, []);

  const loadApiKeys = async () => {
    try {
      const response = await apiKeysApi.list();
      setKeys(response.items);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load API keys',
        variant: 'destructive',
      });
    }
  };

  const handleAdd = async () => {
    if (!newKeyName.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter a name for the API key',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await apiKeysApi.create(newKeyName.trim());
      setNewlyCreatedKey(response);
      setNewKeyName('');
      setShowAddForm(false);
      await loadApiKeys(); // Refresh the list

      toast({
        title: 'Success',
        description: 'API key created successfully. Make sure to copy it now!',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to create API key',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
      return;
    }

    try {
      await apiKeysApi.delete(id);
      await loadApiKeys();
      toast({
        title: 'Success',
        description: 'API key deleted successfully',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete API key',
        variant: 'destructive',
      });
    }
  };

  const handleCopy = async (key: string, id: string) => {
    try {
      await navigator.clipboard.writeText(key);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
      toast({
        title: 'Copied',
        description: 'API key copied to clipboard',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to copy to clipboard',
        variant: 'destructive',
      });
    }
  };

  const handleDismissNewKey = () => {
    setNewlyCreatedKey(null);
  };

  return (
    <>
      <PageHeader title="API Keys" description="Manage API keys for SSE access">
        <Button onClick={() => setShowAddForm(!showAddForm)} disabled={isLoading}>
          <Plus className="h-4 w-4 mr-2" />
          Add Key
        </Button>
      </PageHeader>

      {/* Show newly created key (only once!) */}
      {newlyCreatedKey && (
        <Card className="mb-6 border-yellow-500 border-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-yellow-500" />
              New API Key Created
            </CardTitle>
            <CardDescription>
              This is the only time you will see the full API key. Copy it now!
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="bg-slate-900 text-white p-4 rounded-lg font-mono text-sm break-all">
                {newlyCreatedKey.key}
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={() => handleCopy(newlyCreatedKey.key, 'new')}
                  variant="secondary"
                >
                  {copiedId === 'new' ? (
                    <>
                      <Check className="h-4 w-4 mr-2" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4 mr-2" />
                      Copy Key
                    </>
                  )}
                </Button>
                <Button variant="outline" onClick={handleDismissNewKey}>
                  I've Saved It
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Add new key form */}
      {showAddForm && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Add New API Key</CardTitle>
            <CardDescription>Create a new API key for SSE access</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Name</label>
                <Input
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="My API Key"
                  disabled={isLoading}
                />
              </div>
              <div className="flex gap-2">
                <Button onClick={handleAdd} disabled={isLoading}>
                  {isLoading ? 'Creating...' : 'Create'}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowAddForm(false)}
                  disabled={isLoading}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* API Keys list */}
      <div className="space-y-4">
        {keys.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-slate-500">
              No API keys yet. Click "Add Key" to create one.
            </CardContent>
          </Card>
        ) : (
          keys.map((keyItem) => (
            <Card key={keyItem.id}>
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{keyItem.name}</div>
                    <div className="flex items-center gap-2 mt-1">
                      <code className="text-sm bg-slate-100 px-2 py-1 rounded">
                        {keyItem.key_preview}
                      </code>
                      {!keyItem.is_active && (
                        <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded">
                          Revoked
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-slate-500 mt-1">
                      Created: {new Date(keyItem.created_at).toLocaleString()}
                      {keyItem.last_used_at && (
                        <span className="ml-4">
                          Last used: {new Date(keyItem.last_used_at).toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(keyItem.id)}
                    disabled={!keyItem.is_active}
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>How to Use</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-600 mb-4">
            Use these API keys in the Authorization header when making SSE requests:
          </p>
          <pre className="bg-slate-900 text-white p-4 rounded-lg text-sm overflow-x-auto">
            {`Authorization: Bearer your-api-key`}
          </pre>
        </CardContent>
      </Card>
    </>
  );
}
