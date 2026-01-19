import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { batchAPI, getErrorMessage } from '../../services/api';
import { useToast } from '../../contexts/ToastContext';
import Card, { CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Spinner from '../ui/Spinner';
import Badge from '../ui/Badge';
import ProgressBar from '../ui/ProgressBar';
import Alert from '../ui/Alert';
import {
  ArrowLeft,
  Download,
  FileText,
  Layers,
  TrendingUp,
  CheckCircle2,
  AlertCircle,
  RefreshCw
} from 'lucide-react';

interface BatchDocument {
  id: number;
  filename: string;
  word_count: number;
  ai_probability: number | null;
  confidence_level: string | null;
  cluster_id: number | null;
  status: string;
}

interface Cluster {
  cluster_id: number;
  document_ids: number[];
  avg_similarity: number;
}

interface BatchJob {
  job_id: number;
  status: string;
  total_documents: number;
  processed_documents: number;
  granularity: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  progress: number;
}

interface BatchResultsData {
  job: BatchJob;
  documents: BatchDocument[];
  clusters: Array<{
    cluster_id: number;
    document_count: number;
    avg_ai_probability: number | null;
  }>;
  similarity_matrix: number[][] | null;
}

export default function BatchResults() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const { error: showError, success: showSuccess } = useToast();

  const [results, setResults] = useState<BatchResultsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [selectedCluster, setSelectedCluster] = useState<number | null>(null);

  useEffect(() => {
    if (jobId) {
      loadResults();
    }
  }, [jobId]);

  // Poll for updates if job is still processing
  useEffect(() => {
    if (!results || results.job.status === 'COMPLETED' || results.job.status === 'FAILED') {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const data = await batchAPI.getBatchResults(Number(jobId));
        setResults(data);

        if (data.job.status === 'COMPLETED') {
          clearInterval(interval);
          showSuccess('Batch analysis completed!');
        } else if (data.job.status === 'FAILED') {
          clearInterval(interval);
          showError(data.job.error_message || 'Batch analysis failed');
        }
      } catch (err) {
        console.error('Error polling results:', err);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [results, jobId]);

  const loadResults = async () => {
    try {
      setLoading(true);
      const data = await batchAPI.getBatchResults(Number(jobId));
      setResults(data);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format: 'csv' | 'json') => {
    if (!jobId) return;

    setExporting(true);
    try {
      const blob = await batchAPI.exportBatch(Number(jobId), format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `batch_analysis_${jobId}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      showSuccess(`Exported as ${format.toUpperCase()}`);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setExporting(false);
    }
  };

  const getConfidenceBadge = (level: string | null) => {
    if (!level) return <Badge variant="outline">N/A</Badge>;
    switch (level) {
      case 'HIGH':
        return <Badge variant="error">High AI</Badge>;
      case 'MEDIUM':
        return <Badge variant="warning">Medium</Badge>;
      case 'LOW':
        return <Badge variant="success">Low AI</Badge>;
      default:
        return <Badge variant="outline">{level}</Badge>;
    }
  };

  const getAiProbabilityColor = (prob: number | null) => {
    if (prob === null) return 'text-gray-400';
    if (prob > 0.7) return 'text-error-600 dark:text-error-400';
    if (prob >= 0.4) return 'text-warning-600 dark:text-warning-400';
    return 'text-success-600 dark:text-success-400';
  };

  const getAiProbabilityLabel = (prob: number | null) => {
    if (prob === null) return 'N/A';
    return `${(prob * 100).toFixed(1)}%`;
  };

  // Filter documents by selected cluster
  const filteredDocuments = selectedCluster === null
    ? results?.documents || []
    : results?.documents.filter(d => d.cluster_id === selectedCluster) || [];

  // Calculate overview statistics
  const avgAiProbability = results?.documents.length
    ? results.documents
        .map(d => d.ai_probability)
        .filter((p): p is number => p !== null)
        .reduce((sum, p, _, arr) => sum + p / arr.length, 0)
    : null;

  const highConfidenceCount = results?.documents.filter(d => d.confidence_level === 'HIGH').length || 0;
  const mediumConfidenceCount = results?.documents.filter(d => d.confidence_level === 'MEDIUM').length || 0;
  const lowConfidenceCount = results?.documents.filter(d => d.confidence_level === 'LOW').length || 0;

  // Render similarity heatmap
  const renderSimilarityHeatmap = () => {
    if (!results?.similarity_matrix || results.similarity_matrix.length === 0) {
      return (
        <div className="flex items-center justify-center h-48 text-gray-500 dark:text-gray-400 text-sm">
          Similarity matrix not available
        </div>
      );
    }

    const matrix = results.similarity_matrix;
    const maxDocsToShow = Math.min(matrix.length, 20); // Limit for display
    const displayMatrix = matrix.slice(0, maxDocsToShow);

    return (
      <div className="overflow-x-auto">
        <div className="inline-block min-w-full">
          <div className="flex gap-0.5">
            {/* Row labels */}
            <div className="flex flex-col gap-0.5 mr-2">
              <div className="h-6"></div>
              {displayMatrix.map((_, i) => (
                <div key={i} className="h-6 flex items-center justify-end text-xs text-gray-500 w-6">
                  {i + 1}
                </div>
              ))}
            </div>
            {/* Matrix grid */}
            <div className="flex flex-col gap-0.5">
              {displayMatrix.map((row, i) => (
                <div key={i} className="flex gap-0.5">
                  {row.slice(0, maxDocsToShow).map((value, j) => {
                    // Color scale: red (low similarity) to green (high similarity)
                    // Values are in [-1, 1], but for similarity we expect [0, 1]
                    const normalizedValue = Math.max(0, Math.min(1, value));
                    const hue = (1 - normalizedValue) * 240; // 240 = blue (low), 0 = red (high)
                    const lightness = 70 + (1 - Math.abs(normalizedValue - 0.5) * 2) * 20;
                    return (
                      <div
                        key={j}
                        className="w-6 h-6 rounded-sm flex items-center justify-center text-[10px] font-medium"
                        style={{
                          backgroundColor: `hsl(${hue}, 70%, ${lightness}%)`,
                          color: normalizedValue > 0.5 ? '#fff' : '#000',
                        }}
                        title={`Doc ${i + 1} vs Doc ${j + 1}: ${(value * 100).toFixed(0)}%`}
                      >
                        {(normalizedValue * 100).toFixed(0)}
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
          {matrix.length > maxDocsToShow && (
            <div className="text-xs text-gray-500 mt-2">
              Showing {maxDocsToShow} of {matrix.length} documents
            </div>
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!results) {
    return (
      <Alert variant="error" title="Results Not Found">
        Unable to load batch results. The job may not exist or you may not have permission to view it.
      </Alert>
    );
  }

  const { job, documents, clusters } = results;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/batch')}
              className="gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                Batch Results
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Job #{job.job_id} • {new Date(job.created_at).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={loadResults}
            className="gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
          <Button
            variant="outline"
            onClick={() => handleExport('csv')}
            disabled={exporting || job.status !== 'COMPLETED'}
            className="gap-2"
          >
            <Download className="h-4 w-4" />
            Export CSV
          </Button>
          <Button
            variant="outline"
            onClick={() => handleExport('json')}
            disabled={exporting || job.status !== 'COMPLETED'}
            className="gap-2"
          >
            <Download className="h-4 w-4" />
            Export JSON
          </Button>
        </div>
      </div>

      {/* Status Banner */}
      {job.status !== 'COMPLETED' && (
        <Alert
          variant={job.status === 'FAILED' ? 'error' : 'info'}
          title={job.status === 'FAILED' ? 'Analysis Failed' : 'Processing'}
        >
          {job.status === 'FAILED'
            ? job.error_message || 'An error occurred during analysis.'
            : `Processing ${job.processed_documents} of ${job.total_documents} documents...`}
        </Alert>
      )}

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Total Documents
            </CardTitle>
            <FileText className="h-4 w-4 text-primary-600 dark:text-primary-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {documents.length}
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {job.processed_documents} processed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Clusters Found
            </CardTitle>
            <Layers className="h-4 w-4 text-info-600 dark:text-info-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {clusters.length}
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Similar document groups
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Avg AI Probability
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-warning-600 dark:text-warning-400" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getAiProbabilityColor(avgAiProbability)}`}>
              {getAiProbabilityLabel(avgAiProbability)}
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Across all documents
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
              High Confidence AI
            </CardTitle>
            <AlertCircle className="h-4 w-4 text-error-600 dark:text-error-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-error-600 dark:text-error-400">
              {highConfidenceCount}
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              of {documents.length} documents
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Progress for in-progress jobs */}
      {job.status === 'PROCESSING' && job.total_documents > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Spinner size="sm" />
              Processing Progress
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ProgressBar
              value={job.processed_documents}
              max={job.total_documents}
              showLabel
              label={`${job.processed_documents} of ${job.total_documents} documents`}
            />
          </CardContent>
        </Card>
      )}

      {/* Clusters Section */}
      {clusters.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Document Clusters</CardTitle>
            <CardDescription>
              Groups of similar documents based on content analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2 mb-4">
              <Button
                variant={selectedCluster === null ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setSelectedCluster(null)}
              >
                All Documents ({documents.length})
              </Button>
              {clusters.map((cluster) => (
                <Button
                  key={cluster.cluster_id}
                  variant={selectedCluster === cluster.cluster_id ? 'primary' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedCluster(cluster.cluster_id)}
                >
                  Cluster {cluster.cluster_id + 1} ({cluster.document_count})
                </Button>
              ))}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {clusters.map((cluster) => (
                <div
                  key={cluster.cluster_id}
                  className={`p-4 rounded-lg border ${
                    selectedCluster === cluster.cluster_id
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/20'
                      : 'border-gray-200 dark:border-gray-700'
                  }`}
                >
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    Cluster {cluster.cluster_id + 1}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {cluster.document_count} documents
                  </div>
                  {cluster.avg_ai_probability !== null && (
                    <div className={`text-sm font-medium mt-2 ${getAiProbabilityColor(cluster.avg_ai_probability)}`}>
                      AI: {(cluster.avg_ai_probability * 100).toFixed(1)}%
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Similarity Heatmap */}
      {results.similarity_matrix && results.similarity_matrix.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Similarity Matrix</CardTitle>
            <CardDescription>
              Document-to-document similarity percentages (higher = more similar)
            </CardDescription>
          </CardHeader>
          <CardContent>
            {renderSimilarityHeatmap()}
          </CardContent>
        </Card>
      )}

      {/* Documents Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            Documents
            {selectedCluster !== null && ` (Cluster ${selectedCluster + 1})`}
          </CardTitle>
          <CardDescription>
            Individual document analysis results
          </CardDescription>
        </CardHeader>
        <CardContent>
          {filteredDocuments.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No documents to display.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 dark:text-gray-400">
                      Filename
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 dark:text-gray-400">
                      Words
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 dark:text-gray-400">
                      AI Probability
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 dark:text-gray-400">
                      Confidence
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 dark:text-gray-400">
                      Cluster
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 dark:text-gray-400">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredDocuments.map((doc) => (
                    <tr
                      key={doc.id}
                      className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800"
                    >
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-gray-400" />
                          <span className="text-sm text-gray-900 dark:text-gray-100">
                            {doc.filename}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                        {doc.word_count.toLocaleString()}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`text-sm font-medium ${getAiProbabilityColor(doc.ai_probability)}`}>
                          {getAiProbabilityLabel(doc.ai_probability)}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        {getConfidenceBadge(doc.confidence_level)}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                        {doc.cluster_id !== null ? `#${doc.cluster_id + 1}` : '—'}
                      </td>
                      <td className="py-3 px-4">
                        {doc.status === 'COMPLETED' ? (
                          <CheckCircle2 className="h-4 w-4 text-success-600 dark:text-success-400" />
                        ) : (
                          <Spinner size="sm" />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
