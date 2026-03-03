import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { PageHeader } from '@/components/page-header';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Plus, Trash2, Copy, Check } from 'lucide-react';

export default function ApiKeys() {
  const [keys, setKeys] = useState<{ id: string; key: string; name: string; created: string }[]>([
    { id: '1', key: 'sk-test-123456', name: 'Default Key', created: new Date().toISOString() },
  ]);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyValue, setNewKeyValue] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleAdd = () => {
    if (!newKeyName || !newKeyValue) return;
    const newKey = {
      id: Date.now().toString(),
      key: newKeyValue,
      name: newKeyName,
      created: new Date().toISOString(),
    };
    setKeys([...keys, newKey]);
    setNewKeyName('');
    setNewKeyValue('');
    setShowAddForm(false);
  };

  const handleDelete = (id: string) => {
    if (!confirm('Are you sure you want to delete this API key?')) return;
    setKeys(keys.filter((k) => k.id !== id));
  };

  const handleCopy = (key: string, id: string) => {
    navigator.clipboard.writeText(key);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <>
      <PageHeader title="API Keys" description="Manage API keys for SSE access">
        <Button onClick={() => setShowAddForm(!showAddForm)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Key
        </Button>
      </PageHeader>

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
                />
              </div>
              <div>
                <label className="text-sm font-medium">API Key</label>
                <Input
                  value={newKeyValue}
                  onChange={(e) => setNewKeyValue(e.target.value)}
                  placeholder="sk-..."
                />
              </div>
              <div className="flex gap-2">
                <Button onClick={handleAdd}>Add</Button>
                <Button variant="outline" onClick={() => setShowAddForm(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {keys.map((keyItem) => (
          <Card key={keyItem.id}>
            <CardContent className="py-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">{keyItem.name}</div>
                  <div className="flex items-center gap-2 mt-1">
                    <code className="text-sm bg-slate-100 px-2 py-1 rounded">
                      {keyItem.key.substring(0, 10)}...{keyItem.key.substring(keyItem.key.length - 5)}
                    </code>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleCopy(keyItem.key, keyItem.id)}
                    >
                      {copiedId === keyItem.id ? (
                        <Check className="h-4 w-4 text-green-500" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                  <div className="text-sm text-slate-500 mt-1">
                    Created: {new Date(keyItem.created).toLocaleString()}
                  </div>
                </div>
                <Button variant="ghost" size="icon" onClick={() => handleDelete(keyItem.id)}>
                  <Trash2 className="h-4 w-4 text-red-500" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
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
