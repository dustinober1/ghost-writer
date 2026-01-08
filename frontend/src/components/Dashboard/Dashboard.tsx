import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyticsAPI, getErrorMessage } from '../../services/api';
import { useToast } from '../../contexts/ToastContext';
import Card, { CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { FileText, PenTool, Upload, Fingerprint, TrendingUp, Activity, AlertCircle } from 'lucide-react';
import Badge from '../ui/Badge';
import Spinner from '../ui/Spinner';
import Alert from '../ui/Alert';

interface AnalyticsOverview {
  total_analyses: number;
  total_rewrites: number;
  total_samples: number;
  has_fingerprint: boolean;
  fingerprint_accuracy: number | null;
  average_ai_probability: number | null;
}

interface ActivityEntry {
  id: number;
  type: string;
  description: string;
  created_at: string;
  metadata?: Record<string, any>;
}

interface TrendData {
  label: string;
  data: Array<{
    date: string;
    count: number;
    value?: number | null;
  }>;
}

interface PerformanceMetrics {
  average_ai_probability: number;
  high_confidence_count: number;
  medium_confidence_count: number;
  low_confidence_count: number;
  total_analyses: number;
}

const COLORS = ['#4f46e5', '#22c55e', '#f59e0b', '#ef4444'];

export default function Dashboard() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [activity, setActivity] = useState<ActivityEntry[]>([]);
  const [trends, setTrends] = useState<TrendData[]>([]);
  const [performance, setPerformance] = useState<PerformanceMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const { error: showError } = useToast();
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [overviewData, activityData, trendsData, performanceData] = await Promise.all([
        analyticsAPI.getOverview(),
        analyticsAPI.getActivity(30),
        analyticsAPI.getTrends(30),
        analyticsAPI.getPerformance(),
      ]);

      setOverview(overviewData);
      setActivity(activityData);
      setTrends(trendsData);
      setPerformance(performanceData);
    } catch (err: any) {
      console.error('Dashboard error:', err);
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!overview) {
    return (
      <Alert variant="error" title="Error loading dashboard">
        Unable to load dashboard data. Please try again later.
      </Alert>
    );
  }

  // Prepare chart data
  const analysisTrendData = trends.find(t => t.label === 'Daily Analyses')?.data || [];
  const probabilityTrendData = trends.find(t => t.label === 'Average AI Probability')?.data || [];

  const distributionData = performance
    ? [
        { name: 'High (>70%)', value: performance.high_confidence_count },
        { name: 'Medium (40-70%)', value: performance.medium_confidence_count },
        { name: 'Low (<40%)', value: performance.low_confidence_count },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400">Overview of your analytics and activity</p>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Total Analyses
            </CardTitle>
            <FileText className="h-4 w-4 text-primary-600 dark:text-primary-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {overview.total_analyses}
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Text analyses performed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Writing Samples
            </CardTitle>
            <Upload className="h-4 w-4 text-success-600 dark:text-success-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {overview.total_samples}
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Samples uploaded
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Fingerprint Status
            </CardTitle>
            <Fingerprint className="h-4 w-4 text-warning-600 dark:text-warning-400" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {overview.has_fingerprint ? (
                <>
                  <Badge variant="success">Active</Badge>
                  {overview.fingerprint_accuracy && (
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {Math.round(overview.fingerprint_accuracy * 100)}% accuracy
                    </span>
                  )}
                </>
              ) : (
                <Badge variant="outline">Not Created</Badge>
              )}
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {overview.has_fingerprint ? 'Fingerprint ready' : 'Create fingerprint to get started'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Avg AI Probability
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-info-600 dark:text-info-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {overview.average_ai_probability !== null
                ? `${(overview.average_ai_probability * 100).toFixed(1)}%`
                : 'N/A'}
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Across all analyses
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Analyses Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Daily Analyses</CardTitle>
            <CardDescription>Number of analyses performed per day</CardDescription>
          </CardHeader>
          <CardContent>
            {analysisTrendData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analysisTrendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#4f46e5" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-gray-500 dark:text-gray-400">
                No data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* AI Probability Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>AI Detection Distribution</CardTitle>
            <CardDescription>Confidence level breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            {distributionData.some(d => d.value > 0) ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={distributionData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {distributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-gray-500 dark:text-gray-400">
                No data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Activity Timeline */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Your latest actions and analyses</CardDescription>
        </CardHeader>
        <CardContent>
          {activity.length > 0 ? (
            <div className="space-y-4">
              {activity.slice(0, 10).map((item) => (
                <div
                  key={item.id}
                  className="flex items-start gap-4 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex-shrink-0 mt-1">
                    {item.type === 'analysis' && <FileText className="h-5 w-5 text-primary-600 dark:text-primary-400" />}
                    {item.type === 'sample_upload' && <Upload className="h-5 w-5 text-success-600 dark:text-success-400" />}
                    {item.type === 'fingerprint_generated' && <Fingerprint className="h-5 w-5 text-warning-600 dark:text-warning-400" />}
                    {item.type === 'rewrite' && <PenTool className="h-5 w-5 text-info-600 dark:text-info-400" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {item.description}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {new Date(item.created_at).toLocaleString()}
                    </p>
                    {item.metadata && item.type === 'analysis' && (
                      <Badge variant="info" size="sm" className="mt-1">
                        AI: {(item.metadata.ai_probability * 100).toFixed(1)}%
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No recent activity
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
