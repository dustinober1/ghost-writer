import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { batchAPI, getErrorMessage } from '../../services/api';
import { useToast } from '../../contexts/ToastContext';
import Card, { CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Spinner from '../ui/Spinner';
import ProgressBar from '../ui/ProgressBar';
import Badge from '../ui/Badge';
import { Upload, FileText, Package, CheckCircle2, AlertCircle, X } from 'lucide-react';

interface BatchJob {
  job_id: number;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  total_documents: number;
  processed_documents: number;
  granularity: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  progress: number;
}

export default function BatchAnalysis() {
  const [files, setFiles] = useState<File[]>([]);
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<number | null>(null);
  const [jobStatus, setJobStatus] = useState<BatchJob | null>(null);
  const [recentJobs, setRecentJobs] = useState<BatchJob[]>([]);
  const [granularity, setGranularity] = useState<'sentence' | 'paragraph'>('sentence');
  const [loadingJobs, setLoadingJobs] = useState(true);

  const navigate = useNavigate();
  const { error: showError, success: showSuccess } = useToast();

  useEffect(() => {
    loadRecentJobs();
  }, []);

  // Poll for status updates if we have a processing job
  useEffect(() => {
    if (!currentJobId || !jobStatus || jobStatus.status === 'COMPLETED' || jobStatus.status === 'FAILED') {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const status = await batchAPI.getBatchStatus(currentJobId);
        setJobStatus(status);

        if (status.status === 'COMPLETED') {
          clearInterval(interval);
          showSuccess('Batch analysis completed!');
          loadRecentJobs();
          setTimeout(() => {
            navigate(`/batch/${currentJobId}`);
          }, 1000);
        } else if (status.status === 'FAILED') {
          clearInterval(interval);
          showError(status.error_message || 'Batch analysis failed');
          loadRecentJobs();
        }
      } catch (err) {
        console.error('Error polling status:', err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [currentJobId, jobStatus]);

  const loadRecentJobs = async () => {
    try {
      setLoadingJobs(true);
      const jobs = await batchAPI.listBatchJobs(0, 10);
      setRecentJobs(jobs);
    } catch (err) {
      console.error('Error loading jobs:', err);
    } finally {
      setLoadingJobs(false);
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    handleFiles(droppedFiles);
  }, []);

  const handleFiles = (newFiles: File[]) => {
    // Filter for text files and ZIP
    const textFiles = newFiles.filter(f =>
      f.name.endsWith('.txt') || f.type === 'text/plain'
    );
    const zipFiles = newFiles.filter(f =>
      f.name.endsWith('.zip') || f.type === 'application/zip'
    );

    if (zipFiles.length > 0) {
      if (zipFile) {
        showError('Only one ZIP file can be uploaded at a time');
      } else {
        setZipFile(zipFiles[0]);
      }
    }

    if (textFiles.length > 0) {
      setFiles(prev => [...prev, ...textFiles]);
    }

    if (textFiles.length === 0 && zipFiles.length === 0) {
      showError('Please upload .txt or .zip files only');
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(Array.from(e.target.files));
    }
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const removeZipFile = () => {
    setZipFile(null);
  };

  const handleUpload = async () => {
    if (files.length === 0 && !zipFile) {
      showError('Please add files to upload');
      return;
    }

    setIsUploading(true);
    try {
      let response;
      if (zipFile) {
        response = await batchAPI.uploadBatchZip(zipFile, granularity);
      } else {
        response = await batchAPI.uploadBatch(files, granularity);
      }

      setCurrentJobId(response.job_id);
      setJobStatus({
        job_id: response.job_id,
        status: response.status,
        total_documents: 0,
        processed_documents: 0,
        granularity,
        created_at: new Date().toISOString(),
        started_at: null,
        completed_at: null,
        error_message: null,
        progress: 0,
      });

      showSuccess('Files uploaded! Analysis starting...');
      setFiles([]);
      setZipFile(null);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setIsUploading(false);
    }
  };

  const viewJobResults = (jobId: number) => {
    navigate(`/batch/${jobId}`);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <Badge variant="success">Completed</Badge>;
      case 'PROCESSING':
        return <Badge variant="info">Processing</Badge>;
      case 'FAILED':
        return <Badge variant="error">Failed</Badge>;
      default:
        return <Badge variant="outline">Pending</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Batch Analysis</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Upload multiple documents to analyze AI-generated content patterns across your files.
        </p>
      </div>

      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Documents</CardTitle>
          <CardDescription>
            Drag and drop text files or a ZIP archive, or click to browse
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Granularity Selection */}
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Analysis granularity:
            </span>
            <div className="flex gap-2">
              <Button
                variant={granularity === 'sentence' ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setGranularity('sentence')}
              >
                Sentence
              </Button>
              <Button
                variant={granularity === 'paragraph' ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setGranularity('paragraph')}
              >
                Paragraph
              </Button>
            </div>
          </div>

          {/* Drop Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`
              border-2 border-dashed rounded-lg p-8 text-center transition-colors
              ${isDragging
                ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/20'
                : 'border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-600'
              }
            `}
          >
            <input
              type="file"
              id="file-upload"
              multiple
              accept=".txt,.zip"
              onChange={handleFileInput}
              className="hidden"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <div className="flex flex-col items-center gap-3">
                {isDragging ? (
                  <FileText className="h-12 w-12 text-primary-600 dark:text-primary-400" />
                ) : (
                  <Upload className="h-12 w-12 text-gray-400" />
                )}
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  <span className="text-primary-600 dark:text-primary-400 font-medium">
                    Click to browse
                  </span>
                  {' '}or drag and drop
                </div>
                <div className="text-xs text-gray-500">
                  .txt files or .zip archive
                </div>
              </div>
            </label>
          </div>

          {/* Selected Files */}
          {(files.length > 0 || zipFile) && (
            <div className="space-y-2">
              <div className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Selected Files:
              </div>
              {zipFile && (
                <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Package className="h-5 w-5 text-warning-600 dark:text-warning-400" />
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {zipFile.name}
                      </div>
                      <div className="text-xs text-gray-500">
                        {(zipFile.size / 1024).toFixed(1)} KB
                      </div>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={removeZipFile}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              )}
              {files.map((file, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-gray-400" />
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {file.name}
                      </div>
                      <div className="text-xs text-gray-500">
                        {(file.size / 1024).toFixed(1)} KB
                      </div>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFile(index)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}

          {/* Upload Button */}
          <div className="flex justify-end">
            <Button
              onClick={handleUpload}
              disabled={isUploading || files.length === 0}
              className="gap-2"
            >
              {isUploading ? (
                <>
                  <Spinner size="sm" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4" />
                  Upload & Analyze
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Current Job Progress */}
      {jobStatus && currentJobId && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {jobStatus.status === 'PROCESSING' && <Spinner size="sm" />}
              Processing Job #{currentJobId}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">
                Status: {jobStatus.status}
              </span>
              <span className="font-medium text-gray-900 dark:text-gray-100">
                {jobStatus.processed_documents} / {jobStatus.total_documents} documents
              </span>
            </div>
            {jobStatus.total_documents > 0 && (
              <ProgressBar
                value={jobStatus.processed_documents}
                max={jobStatus.total_documents}
                showLabel
                label="Progress"
              />
            )}
            {jobStatus.status === 'PROCESSING' && (
              <p className="text-sm text-gray-500">
                Analyzing documents... This may take a few minutes.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Recent Jobs */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Batch Jobs</CardTitle>
          <CardDescription>Your recent batch analysis jobs</CardDescription>
        </CardHeader>
        <CardContent>
          {loadingJobs ? (
            <div className="flex items-center justify-center py-8">
              <Spinner />
            </div>
          ) : recentJobs.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No batch jobs yet. Upload some documents to get started.
            </div>
          ) : (
            <div className="space-y-3">
              {recentJobs.map((job) => (
                <div
                  key={job.job_id}
                  className="flex items-center justify-between p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer"
                  onClick={() => job.status === 'COMPLETED' && viewJobResults(job.job_id)}
                >
                  <div className="flex items-center gap-4">
                    {job.status === 'COMPLETED' ? (
                      <CheckCircle2 className="h-5 w-5 text-success-600 dark:text-success-400" />
                    ) : job.status === 'FAILED' ? (
                      <AlertCircle className="h-5 w-5 text-error-600 dark:text-error-400" />
                    ) : (
                      <Spinner size="sm" />
                    )}
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        Job #{job.job_id}
                      </div>
                      <div className="text-xs text-gray-500">
                        {job.total_documents} documents • {formatDate(job.created_at)}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {getStatusBadge(job.status)}
                    {job.status === 'COMPLETED' && (
                      <Button variant="ghost" size="sm">
                        View Results
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
