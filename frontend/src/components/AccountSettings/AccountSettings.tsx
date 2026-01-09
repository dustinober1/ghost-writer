import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Card, { CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Alert from '../ui/Alert';
import Modal from '../ui/Modal';
import { useToast } from '../../contexts/ToastContext';
import { Download, Trash2, Shield, Mail, Key, AlertTriangle, FileDown } from 'lucide-react';
import api, { getErrorMessage } from '../../services/api';

interface AccountInfo {
  id: number;
  email: string;
  email_verified: boolean;
  is_active: boolean;
  created_at: string;
  data_summary: {
    writing_samples: number;
    analysis_results: number;
    has_fingerprint: boolean;
  };
}

export default function AccountSettings() {
  const [accountInfo, setAccountInfo] = useState<AccountInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deletePassword, setDeletePassword] = useState('');
  const [deleting, setDeleting] = useState(false);
  const navigate = useNavigate();
  const { success, error: showError } = useToast();

  useEffect(() => {
    loadAccountInfo();
  }, []);

  const loadAccountInfo = async () => {
    try {
      const response = await api.get('/api/account/me');
      setAccountInfo(response.data);
    } catch (err: any) {
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format: 'json' | 'csv') => {
    try {
      const response = await api.get(`/api/account/export?format=${format}`, {
        responseType: 'blob',
      });
      
      const blob = new Blob([response.data], {
        type: format === 'json' ? 'application/json' : 'text/csv',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `ghostwriter_export.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      success(`Data exported as ${format.toUpperCase()}`);
    } catch (err: any) {
      showError(getErrorMessage(err));
    }
  };

  const handleDeleteData = async (dataType: string) => {
    if (!confirm(`Are you sure you want to delete all ${dataType}? This cannot be undone.`)) {
      return;
    }

    try {
      await api.delete(`/api/account/data/${dataType}`);
      success(`${dataType} deleted successfully`);
      loadAccountInfo();
    } catch (err: any) {
      showError(getErrorMessage(err));
    }
  };

  const handleDeleteAccount = async () => {
    if (!deletePassword) {
      showError('Please enter your password');
      return;
    }

    setDeleting(true);
    try {
      await api.delete('/api/account/delete-immediately', {
        data: { password: deletePassword },
      });
      success('Account deleted successfully');
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      navigate('/login');
    } catch (err: any) {
      showError(getErrorMessage(err));
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return <div className="animate-pulse">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Account Settings</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Manage your account, export data, and control your privacy
        </p>
      </div>

      {/* Account Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Account Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Email</p>
              <p className="font-medium text-gray-900 dark:text-gray-100">{accountInfo?.email}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Member Since</p>
              <p className="font-medium text-gray-900 dark:text-gray-100">
                {accountInfo?.created_at ? new Date(accountInfo.created_at).toLocaleDateString() : '-'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Email Verified</p>
              <p className={`font-medium ${accountInfo?.email_verified ? 'text-green-600' : 'text-yellow-600'}`}>
                {accountInfo?.email_verified ? 'Yes' : 'No'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Account Status</p>
              <p className={`font-medium ${accountInfo?.is_active ? 'text-green-600' : 'text-red-600'}`}>
                {accountInfo?.is_active ? 'Active' : 'Inactive'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Data Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Your Data
          </CardTitle>
          <CardDescription>
            Summary of data we store about you
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {accountInfo?.data_summary.writing_samples || 0}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Writing Samples</p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {accountInfo?.data_summary.analysis_results || 0}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Analysis Results</p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {accountInfo?.data_summary.has_fingerprint ? '1' : '0'}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Fingerprints</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Data Export */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileDown className="h-5 w-5" />
            Export Your Data
          </CardTitle>
          <CardDescription>
            Download a copy of all your data (GDPR data portability)
          </CardDescription>
        </CardHeader>
        <CardContent className="flex gap-4">
          <Button variant="outline" onClick={() => handleExport('json')}>
            <Download className="h-4 w-4 mr-2" />
            Export as JSON
          </Button>
          <Button variant="outline" onClick={() => handleExport('csv')}>
            <Download className="h-4 w-4 mr-2" />
            Export as CSV
          </Button>
        </CardContent>
      </Card>

      {/* Delete Data */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-600">
            <Trash2 className="h-5 w-5" />
            Delete Data
          </CardTitle>
          <CardDescription>
            Permanently delete specific data or your entire account
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-4">
            <Button 
              variant="outline" 
              onClick={() => handleDeleteData('samples')}
              className="text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              Delete All Samples
            </Button>
            <Button 
              variant="outline" 
              onClick={() => handleDeleteData('analyses')}
              className="text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              Delete All Analyses
            </Button>
            <Button 
              variant="outline" 
              onClick={() => handleDeleteData('fingerprint')}
              className="text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              Delete Fingerprint
            </Button>
          </div>

          <hr className="border-gray-200 dark:border-gray-700" />

          <Alert variant="warning" title="Danger Zone">
            <p className="mb-4">
              Deleting your account will permanently remove all your data. This action cannot be undone.
            </p>
            <Button 
              variant="outline" 
              onClick={() => setShowDeleteModal(true)}
              className="text-red-600 border-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              <AlertTriangle className="h-4 w-4 mr-2" />
              Delete My Account
            </Button>
          </Alert>
        </CardContent>
      </Card>

      {/* Delete Account Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Delete Account"
      >
        <div className="space-y-4">
          <Alert variant="error" title="This action is irreversible">
            All your data will be permanently deleted, including:
            <ul className="list-disc list-inside mt-2">
              <li>Writing samples</li>
              <li>Fingerprint data</li>
              <li>Analysis history</li>
              <li>Account information</li>
            </ul>
          </Alert>

          <Input
            type="password"
            label="Confirm your password"
            value={deletePassword}
            onChange={(e) => setDeletePassword(e.target.value)}
            placeholder="Enter your password"
          />

          <div className="flex gap-4 justify-end">
            <Button variant="outline" onClick={() => setShowDeleteModal(false)}>
              Cancel
            </Button>
            <Button
              variant="outline"
              onClick={handleDeleteAccount}
              isLoading={deleting}
              className="text-red-600 border-red-600 hover:bg-red-50"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete Account
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
