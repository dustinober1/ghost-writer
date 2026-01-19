import { useState, useEffect, useCallback, useRef } from 'react';
import { fingerprintAPI, getErrorMessage, CorpusStatus, FingerprintSampleResponse } from '../../services/api';
import { useToast } from '../../contexts/ToastContext';
import Card, { CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import Alert from '../ui/Alert';
import Textarea from '../ui/Textarea';
import Modal from '../ui/Modal';
import { Upload, FileText, Trash2, CheckCircle, Sparkles, FileText as FileTextIcon, Calendar, Hash } from 'lucide-react';
import { cn } from '../../utils/cn';
import ProgressBar from '../ui/ProgressBar';

const MIN_SAMPLES_REQUIRED = 10;

type SourceType = 'manual' | 'essay' | 'academic' | 'blog' | 'email' | 'document';

interface SourceTypeOption {
  value: SourceType;
  label: string;
  description: string;
  weight: number;
}

const SOURCE_TYPE_OPTIONS: SourceTypeOption[] = [
  { value: 'essay', label: 'Essay', description: 'Academic or personal essays', weight: 1.2 },
  { value: 'academic', label: 'Academic', description: 'Research papers, articles', weight: 1.3 },
  { value: 'document', label: 'Document', description: 'Professional documents', weight: 1.1 },
  { value: 'blog', label: 'Blog', description: 'Blog posts or articles', weight: 1.0 },
  { value: 'email', label: 'Email', description: 'Email correspondence', weight: 0.9 },
  { value: 'manual', label: 'General', description: 'Other writing samples', weight: 1.0 },
];

export default function CorpusBuilder() {
  const [corpusStatus, setCorpusStatus] = useState<CorpusStatus | null>(null);
  const [samples, setSamples] = useState<FingerprintSampleResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadText, setUploadText] = useState('');
  const [selectedSourceType, setSelectedSourceType] = useState<SourceType>('manual');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [sampleToDelete, setSampleToDelete] = useState<FingerprintSampleResponse | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { success, error: showError } = useToast();

  useEffect(() => {
    loadCorpusStatus();
    loadSamples();
  }, [page]);

  const loadCorpusStatus = async () => {
    try {
      const data = await fingerprintAPI.corpus.getStatus();
      setCorpusStatus(data);
    } catch (err: any) {
      console.error('Load corpus status error:', err);
      // Don't show error toast for initial load, just log
    }
  };

  const loadSamples = async () => {
    try {
      const data = await fingerprintAPI.corpus.getSamples(page, 20);
      setSamples(data);
      // Calculate total pages based on sample count
      if (corpusStatus) {
        setTotalPages(Math.ceil(corpusStatus.sample_count / 20));
      }
    } catch (err: any) {
      console.error('Load samples error:', err);
      showError(getErrorMessage(err));
    }
  };

  const handleAddSample = async (text: string, sourceType: SourceType) => {
    if (!text.trim()) {
      showError('Please enter some text');
      return false;
    }

    if (text.trim().length < 10) {
      showError('Text must be at least 10 characters');
      return false;
    }

    setLoading(true);
    try {
      await fingerprintAPI.corpus.add(text, sourceType);
      success('Sample added to corpus!');
      setUploadText('');
      await loadCorpusStatus();
      await loadSamples();
      return true;
    } catch (err: any) {
      console.error('Add sample error:', err);
      showError(getErrorMessage(err));
      return false;
    } finally {
      setLoading(false);
    }
  };

  const handleTextSubmit = async () => {
    const success = await handleAddSample(uploadText, selectedSourceType);
    if (success) {
      setUploadText('');
    }
  };

  const handleFileUpload = async (files: FileList | File[]) => {
    const fileArray = Array.from(files);
    if (fileArray.length === 0) return;

    const validTypes = ['.txt', '.docx', '.pdf'];
    const invalidFiles = fileArray.filter(file => {
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
      return !validTypes.includes(fileExtension);
    });

    if (invalidFiles.length > 0) {
      showError(`Invalid file type(s): ${invalidFiles.map(f => f.name).join(', ')}. Please upload .txt, .docx, or .pdf files.`);
      return;
    }

    const validFiles = fileArray.filter(file => {
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
      return validTypes.includes(fileExtension);
    });

    let successCount = 0;
    let errorCount = 0;

    setLoading(true);

    for (const file of validFiles) {
      try {
        const text = await readFileContent(file);
        await handleAddSample(text, selectedSourceType);
        successCount++;
      } catch (err: any) {
        console.error(`File upload error for ${file.name}:`, err);
        errorCount++;
      }
    }

    if (successCount > 0) {
      if (validFiles.length === 1) {
        success('File uploaded successfully!');
      } else {
        success(`${successCount} file${successCount > 1 ? 's' : ''} uploaded successfully${errorCount > 0 ? ` (${errorCount} failed)` : ''}`);
      }
      await loadCorpusStatus();
      await loadSamples();
    }

    setLoading(false);
  };

  const readFileContent = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        resolve(content);
      };
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsText(file);
    });
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files);
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFileUpload(files);
    }
  }, []);

  const confirmDelete = (sample: FingerprintSampleResponse) => {
    setSampleToDelete(sample);
    setShowDeleteModal(true);
  };

  const handleDelete = async () => {
    if (!sampleToDelete) return;

    try {
      await fingerprintAPI.corpus.deleteSample(sampleToDelete.id);
      success('Sample deleted successfully!');
      setShowDeleteModal);
      setSampleToDelete(null);
      await loadCorpusStatus();
      await loadSamples();
    } catch (err: any) {
      console.error('Delete sample error:', err);
      showError(getErrorMessage(err));
    }
  };

  const handleGenerateFingerprint = async () => {
    if (!corpusStatus?.ready_for_fingerprint) return;

    setLoading(true);
    try {
      await fingerprintAPI.corpus.generateFingerprint('time_weighted', 0.3);
      success('Enhanced fingerprint generated successfully!');
      await loadCorpusStatus();
    } catch (err: any) {
      console.error('Generate fingerprint error:', err);
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const getProgressColor = (count: number) => {
    if (count < 5) return 'bg-red-500';
    if (count < MIN_SAMPLES_REQUIRED) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getSourceTypeLabel = (sourceType: string) => {
    const option = SOURCE_TYPE_OPTIONS.find(opt => opt.value === sourceType);
    return option?.label || sourceType;
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const maxSamples = corpusStatus?.sample_count || MIN_SAMPLES_REQUIRED;
  const progressPercentage = corpusStatus ? Math.min(100, (corpusStatus.sample_count / MIN_SAMPLES_REQUIRED) * 100) : 0;
  const isReady = corpusStatus?.ready_for_fingerprint || false;

  return (
    <div className="space-y-6">
      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Sample Count
            </CardTitle>
            <FileTextIcon className="h-4 w-4 text-primary-600 dark:text-primary-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {corpusStatus?.sample_count || 0} / {MIN_SAMPLES_REQUIRED}
            </div>
            <div className="mt-2">
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="text-gray-600 dark:text-gray-400">Progress</span>
                <span className="text-gray-600 dark:text-gray-400">
                  {corpusStatus?.sample_count || 0} / {MIN_SAMPLES_REQUIRED}
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className={cn('h-2 rounded-full transition-all duration-300', getProgressColor(corpusStatus?.sample_count || 0))}
                  style={{ width: `${progressPercentage}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Status
            </CardTitle>
            <CheckCircle className={cn('h-4 w-4', isReady ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400')} />
          </CardHeader>
          <CardContent>
            {isReady ? (
              <Badge variant="success" size="lg">
                <CheckCircle className="h-4 w-4 mr-1" />
                Ready for Enhanced Fingerprint
              </Badge>
            ) : (
              <div className="space-y-2">
                <Badge variant="outline" size="lg">
                  Collecting Samples
                </Badge>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {corpusStatus?.samples_needed || MIN_SAMPLES_REQUIRED} more sample{(corpusStatus?.samples_needed || 1) !== 1 ? 's' : ''} needed
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Total Words
            </CardTitle>
            <Hash className="h-4 w-4 text-info-600 dark:text-info-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {corpusStatus?.total_words?.toLocaleString() || 0}
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
              Across {corpusStatus?.sample_count || 0} samples
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Source Distribution */}
      {corpusStatus && Object.keys(corpusStatus.source_distribution).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Source Distribution</CardTitle>
            <CardDescription>Breakdown of your writing samples by type</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              {Object.entries(corpusStatus.source_distribution).map(([source, count]) => {
                const option = SOURCE_TYPE_OPTIONS.find(opt => opt.value === source);
                const percentage = corpusStatus.sample_count > 0
                  ? Math.round((count / corpusStatus.sample_count) * 100)
                  : 0;
                return (
                  <div key={source} className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 rounded-lg px-3 py-2">
                    <span className="font-medium text-sm">{option?.label || source}</span>
                    <Badge variant="secondary" size="sm">{count}</Badge>
                    <span className="text-xs text-gray-600 dark:text-gray-400">({percentage}%)</span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle>Add Writing Samples</CardTitle>
          <CardDescription>
            Add your past writing to build your corpus. You need at least {MIN_SAMPLES_REQUIRED} samples for an enhanced fingerprint.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Source Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Source Type
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {SOURCE_TYPE_OPTIONS.map(option => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setSelectedSourceType(option.value)}
                  className={cn(
                    'p-3 rounded-lg border text-left transition-all',
                    selectedSourceType === option.value
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/20 ring-2 ring-primary-500'
                      : 'border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-600'
                  )}
                >
                  <div className="font-medium text-sm">{option.label}</div>
                  <div className="text-xs text-gray-600 dark:text-gray-400">{option.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Text Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Paste Text Sample
            </label>
            <Textarea
              value={uploadText}
              onChange={(e) => setUploadText(e.target.value)}
              placeholder="Paste your writing sample here (minimum 10 characters)..."
              className="min-h-[150px]"
              disabled={loading}
            />
            <div className="flex justify-between items-center mt-2">
              <span className="text-xs text-gray-600 dark:text-gray-400">
                {uploadText.length} characters
              </span>
              <Button
                onClick={handleTextSubmit}
                disabled={loading || uploadText.trim().length < 10}
                isLoading={loading}
                size="sm"
              >
                <Upload className="h-4 w-4 mr-2" />
                Add Sample
              </Button>
            </div>
          </div>

          {/* File Upload */}
          <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Or Upload Files
            </label>
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={cn(
                'border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer',
                isDragging
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/20'
                  : 'border-gray-300 dark:border-gray-700 hover:border-primary-400 dark:hover:border-primary-600'
              )}
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="h-10 w-10 text-gray-400 dark:text-gray-600 mx-auto mb-3" />
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                Drag and drop files here, or click to browse
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500">
                Supports .txt files (.docx and .pdf support coming soon)
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.docx,.pdf"
                multiple
                onChange={handleFileInputChange}
                className="hidden"
                disabled={loading}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Generate Enhanced Fingerprint */}
      {isReady && (
        <Card className="border-green-200 dark:border-green-900">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-green-600 dark:text-green-400" />
              Generate Enhanced Fingerprint
            </CardTitle>
            <CardDescription>
              Your corpus is ready! Generate an enhanced fingerprint with time-weighted aggregation.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              onClick={handleGenerateFingerprint}
              disabled={loading}
              isLoading={loading}
              size="lg"
              className="w-full"
            >
              <Sparkles className="h-5 w-5 mr-2" />
              Generate Enhanced Fingerprint
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Samples List */}
      {samples.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Your Samples</CardTitle>
            <CardDescription>
              {corpusStatus?.sample_count || 0} total sample{(corpusStatus?.sample_count || 0) !== 1 ? 's' : ''}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">Source Type</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">Date Added</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">Word Count</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">Preview</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {samples.map(sample => (
                    <tr key={sample.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900/50">
                      <td className="py-3 px-4">
                        <Badge variant="secondary" size="sm">
                          {getSourceTypeLabel(sample.source_type)}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(sample.created_at)}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                        {sample.word_count} words
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400 max-w-xs truncate">
                        {sample.text_preview}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => confirmDelete(sample)}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/20"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-center items-center gap-2 mt-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Page {page} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Next
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false);
          setSampleToDelete(null);
        }}
        title="Delete Sample"
      >
        <div className="space-y-4">
          <p className="text-gray-700 dark:text-gray-300">
            Are you sure you want to delete this sample? This action cannot be undone.
          </p>
          {sampleToDelete && (
            <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-3">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                {getSourceTypeLabel(sampleToDelete.source_type)} - {sampleToDelete.word_count} words
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500 truncate">
                {sampleToDelete.text_preview}
              </p>
            </div>
          )}
          <div className="flex justify-end gap-3">
            <Button
              variant="outline"
              onClick={() => {
                setShowDeleteModal(false);
                setSampleToDelete(null);
              }}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleDelete}
            >
              Delete Sample
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
