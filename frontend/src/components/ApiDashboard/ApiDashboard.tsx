import { useState, useEffect } from 'react';
import Card, { CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Alert from '../ui/Alert';
import Modal from '../ui/Modal';
import { useToast } from '../../contexts/ToastContext';
import { apiKeysAPI, usageAPI, getErrorMessage } from '../../services/api';
import { Key, Plus, Trash2, BarChart3, ExternalLink, Copy, Check } from 'lucide-react';

interface UsageStats {
  tier: string;
  limits: {
    requests_per_day: number;
    requests_per_minute: number;
  };
  usage: {
    requests_today: number;
    requests_this_minute: number;
  };
  remaining: {
    today: number;
    this_minute: number;
  };
}

interface ApiKey {
  id: number;
  key_prefix: string;
  name: string;
  is_active: boolean;
  created_at: string;
  expires_at: string | null;
  last_used: string | null;
}

interface CreatedKeyResponse {
  key: string;
  key_prefix: string;
  name: string;
  expires_at: string | null;
}

export default function ApiDashboard() {
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyExpires, setNewKeyExpires] = useState<number | undefined>(undefined);
  const [creating, setCreating] = useState(false);
  const [createdKey, setCreatedKey] = useState<CreatedKeyResponse | null>(null);
  const [copied, setCopied] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const { success, error: showError } = useToast();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [usageData, keysData] = await Promise.all([
        usageAPI.getUsage(),
        apiKeysAPI.list(),
      ]);
      setUsage(usageData);
      setApiKeys(keysData);
    } catch (err: any) {
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateKey = async () => {
    if (!newKeyName.trim()) {
      showError('Please enter a name for the API key');
      return;
    }

    setCreating(true);
    try {
      const result = await apiKeysAPI.create(newKeyName, newKeyExpires);
      setCreatedKey(result);
      success('API key created successfully');
      setNewKeyName('');
      setNewKeyExpires(undefined);
      setShowCreateModal(false);
      await loadData();
    } catch (err: any) {
      showError(getErrorMessage(err));
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteKey = async (keyId: number) => {
    if (!confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
      return;
    }

    setDeletingId(keyId);
    try {
      await apiKeysAPI.delete(keyId);
      success('API key deleted');
      await loadData();
    } catch (err: any) {
      showError(getErrorMessage(err));
    } finally {
      setDeletingId(null);
    }
  };

  const copyKeyToClipboard = () => {
    if (createdKey?.key) {
      navigator.clipboard.writeText(createdKey.key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'enterprise': return 'text-purple-600';
      case 'pro': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  const getUsagePercentage = (used: number, total: number) => {
    return Math.round((used / total) * 100);
  };

  if (loading) {
    return <div className="animate-pulse">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">API Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Manage your API keys and monitor your usage
        </p>
      </div>

      {/* Usage Stats */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Usage Statistics
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Current Tier</p>
              <p className={`text-2xl font-bold ${getTierColor(usage?.tier || 'free')}`}>
                {usage?.tier.toUpperCase() || 'FREE'}
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => window.open('/docs', '_blank')}
              className="flex items-center gap-2"
            >
              <ExternalLink className="h-4 w-4" />
              View API Docs
            </Button>
          </div>

          <div className="space-y-4">
            {/* Daily Usage */}
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600 dark:text-gray-400">Daily Requests</span>
                <span className="font-medium">
                  {usage?.usage.requests_today || 0} / {usage?.limits.requests_per_day || 0}
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{
                    width: `${Math.min(
                      getUsagePercentage(usage?.usage.requests_today || 0, usage?.limits.requests_per_day || 1),
                      100
                    )}%`
                  }}
                />
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {usage?.remaining.today || 0} requests remaining today
              </p>
            </div>

            {/* Per-Minute Usage */}
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600 dark:text-gray-400">Per-Minute Requests</span>
                <span className="font-medium">
                  {usage?.usage.requests_this_minute || 0} / {usage?.limits.requests_per_minute || 0}
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-green-600 h-2 rounded-full transition-all"
                  style={{
                    width: `${Math.min(
                      getUsagePercentage(usage?.usage.requests_this_minute || 0, usage?.limits.requests_per_minute || 1),
                      100
                    )}%`
                  }}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* API Keys */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Key className="h-5 w-5" />
                API Keys
              </CardTitle>
              <CardDescription>
                Manage keys for programmatic access
              </CardDescription>
            </div>
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="h-4 w-4 mr-2" />
              New Key
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {apiKeys.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <Key className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No API keys yet</p>
              <p className="text-sm">Create a key to start using the API</p>
            </div>
          ) : (
            <div className="space-y-3">
              {apiKeys.map((key) => (
                <div
                  key={key.id}
                  className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-gray-900 dark:text-gray-100">
                        {key.name}
                      </p>
                      <span className="text-xs text-gray-500 dark:text-gray-400 font-mono">
                        {key.key_prefix}***
                      </span>
                      {key.is_active ? (
                        <span className="text-xs px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded">
                          Active
                        </span>
                      ) : (
                        <span className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
                          Inactive
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-4 mt-1 text-xs text-gray-500 dark:text-gray-400">
                      <span>Created: {new Date(key.created_at).toLocaleDateString()}</span>
                      {key.expires_at && (
                        <span>Expires: {new Date(key.expires_at).toLocaleDateString()}</span>
                      )}
                      {key.last_used && (
                        <span>Last used: {new Date(key.last_used).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDeleteKey(key.id)}
                    isLoading={deletingId === key.id}
                    className="text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Key Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create API Key"
      >
        <div className="space-y-4">
          <Input
            label="Key Name"
            placeholder="e.g., Production App, Testing Script"
            value={newKeyName}
            onChange={(e) => setNewKeyName(e.target.value)}
          />
          <Input
            type="number"
            label="Expires In Days (optional)"
            placeholder="Leave empty for no expiration"
            value={newKeyExpires || ''}
            onChange={(e) => setNewKeyExpires(e.target.value ? parseInt(e.target.value) : undefined)}
            min="1"
            max="365"
          />

          <Alert variant="info" title="Important">
            <p className="text-sm">
              The full API key will only be shown once after creation. Make sure to save it securely.
            </p>
          </Alert>

          <div className="flex gap-4 justify-end">
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateKey} isLoading={creating}>
              Create Key
            </Button>
          </div>
        </div>
      </Modal>

      {/* New Key Display Modal */}
      {createdKey && (
        <Modal
          isOpen={!!createdKey}
          onClose={() => setCreatedKey(null)}
          title="API Key Created"
        >
          <div className="space-y-4">
            <Alert variant="success" title="Save Your Key">
              <p className="text-sm">
                This key will only be shown once. Copy it now and store it securely.
              </p>
            </Alert>

            <div className="flex gap-2">
              <Input
                value={createdKey.key}
                readOnly
                className="font-mono text-sm"
              />
              <Button
                variant="outline"
                onClick={copyKeyToClipboard}
                className={copied ? 'bg-green-50 dark:bg-green-900/20' : ''}
              >
                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>

            <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
              <p><strong>Name:</strong> {createdKey.name}</p>
              <p><strong>Prefix:</strong> {createdKey.key_prefix}***</p>
              {createdKey.expires_at && (
                <p><strong>Expires:</strong> {new Date(createdKey.expires_at).toLocaleString()}</p>
              )}
            </div>

            <div className="flex justify-end">
              <Button onClick={() => setCreatedKey(null)}>
                I've Saved My Key
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
