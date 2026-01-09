import { useState, useEffect } from 'react';
import Card, { CardContent, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Badge from '../ui/Badge';
import Spinner from '../ui/Spinner';
import { useToast } from '../../contexts/ToastContext';
import api, { getErrorMessage } from '../../services/api';
import { 
  Users, Activity, Database, Shield, Search, 
  ChevronLeft, ChevronRight, Lock, Unlock, Trash2, 
  CheckCircle, XCircle, BarChart3
} from 'lucide-react';

interface SystemStats {
  total_users: number;
  active_users: number;
  verified_users: number;
  total_analyses: number;
  total_samples: number;
  total_fingerprints: number;
  analyses_last_24h: number;
  analyses_last_7d: number;
  new_users_last_24h: number;
  new_users_last_7d: number;
}

interface AdminUser {
  id: number;
  email: string;
  email_verified: boolean;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  failed_login_attempts: number;
  locked_until: string | null;
  sample_count: number;
  analysis_count: number;
  has_fingerprint: boolean;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [usersLoading, setUsersLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const { success, error: showError } = useToast();

  useEffect(() => {
    loadStats();
    loadUsers(1);
  }, []);

  const loadStats = async () => {
    try {
      const response = await api.get('/api/admin/stats');
      setStats(response.data);
    } catch (err: any) {
      if (err.response?.status === 403) {
        showError('Admin privileges required');
      } else {
        showError(getErrorMessage(err));
      }
    }
  };

  const loadUsers = async (pageNum: number, searchTerm: string = '') => {
    setUsersLoading(true);
    try {
      const params = new URLSearchParams({ page: pageNum.toString(), per_page: '10' });
      if (searchTerm) params.append('search', searchTerm);
      
      const response = await api.get(`/api/admin/users?${params}`);
      setUsers(response.data.users);
      setTotalPages(response.data.pages);
      setPage(pageNum);
    } catch (err: any) {
      showError(getErrorMessage(err));
    } finally {
      setUsersLoading(false);
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadUsers(1, search);
  };

  const handleAction = async (action: string, userId: number) => {
    try {
      await api.post(`/api/admin/users/${userId}/${action}`);
      success(`Action completed successfully`);
      loadUsers(page, search);
    } catch (err: any) {
      showError(getErrorMessage(err));
    }
  };

  const handleDelete = async (userId: number) => {
    if (!confirm('Are you sure you want to delete this user? This cannot be undone.')) {
      return;
    }
    try {
      await api.delete(`/api/admin/users/${userId}`);
      success('User deleted');
      loadUsers(page, search);
      loadStats();
    } catch (err: any) {
      showError(getErrorMessage(err));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Admin Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400">
          System management and user administration
        </p>
      </div>

      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <Users className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{stats.total_users}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Users</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                  <Activity className="h-5 w-5 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{stats.analyses_last_24h}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Analyses (24h)</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                  <Database className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{stats.total_fingerprints}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Fingerprints</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg">
                  <BarChart3 className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{stats.total_analyses}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Analyses</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* User Management */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            User Management
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search */}
          <div className="flex gap-2">
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by email..."
              className="flex-1"
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button onClick={handleSearch}>
              <Search className="h-4 w-4" />
            </Button>
          </div>

          {/* Users Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left p-3 font-medium">Email</th>
                  <th className="text-left p-3 font-medium">Status</th>
                  <th className="text-left p-3 font-medium">Stats</th>
                  <th className="text-left p-3 font-medium">Created</th>
                  <th className="text-left p-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {usersLoading ? (
                  <tr>
                    <td colSpan={5} className="text-center p-6">
                      <Spinner />
                    </td>
                  </tr>
                ) : users.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center p-6 text-gray-500">
                      No users found
                    </td>
                  </tr>
                ) : (
                  users.map((user) => (
                    <tr key={user.id} className="border-b border-gray-100 dark:border-gray-800">
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <span className="text-gray-900 dark:text-gray-100">{user.email}</span>
                          {user.is_admin && (
                            <Badge variant="primary">Admin</Badge>
                          )}
                        </div>
                      </td>
                      <td className="p-3">
                        <div className="flex flex-wrap gap-1">
                          {user.is_active ? (
                            <Badge variant="success">Active</Badge>
                          ) : (
                            <Badge variant="error">Inactive</Badge>
                          )}
                          {user.email_verified ? (
                            <Badge variant="secondary">Verified</Badge>
                          ) : (
                            <Badge variant="warning">Unverified</Badge>
                          )}
                          {user.locked_until && (
                            <Badge variant="error">Locked</Badge>
                          )}
                        </div>
                      </td>
                      <td className="p-3 text-gray-600 dark:text-gray-400">
                        <span title="Samples">{user.sample_count} samples</span>
                        <span className="mx-1">•</span>
                        <span title="Analyses">{user.analysis_count} analyses</span>
                      </td>
                      <td className="p-3 text-gray-600 dark:text-gray-400">
                        {new Date(user.created_at).toLocaleDateString()}
                      </td>
                      <td className="p-3">
                        <div className="flex gap-1">
                          {user.is_active ? (
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleAction('deactivate', user.id)}
                              title="Deactivate"
                            >
                              <XCircle className="h-4 w-4 text-red-500" />
                            </Button>
                          ) : (
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleAction('activate', user.id)}
                              title="Activate"
                            >
                              <CheckCircle className="h-4 w-4 text-green-500" />
                            </Button>
                          )}
                          {user.locked_until && (
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleAction('unlock', user.id)}
                              title="Unlock"
                            >
                              <Unlock className="h-4 w-4 text-yellow-500" />
                            </Button>
                          )}
                          {!user.email_verified && (
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleAction('verify-email', user.id)}
                              title="Verify Email"
                            >
                              <CheckCircle className="h-4 w-4 text-blue-500" />
                            </Button>
                          )}
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={() => handleDelete(user.id)}
                            title="Delete"
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page === 1}
                onClick={() => loadUsers(page - 1, search)}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page === totalPages}
                onClick={() => loadUsers(page + 1, search)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
