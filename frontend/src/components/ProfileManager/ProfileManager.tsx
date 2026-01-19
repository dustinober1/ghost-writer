import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { fingerprintAPI, getErrorMessage, CorpusStatus } from '../../services/api';
import { useToast } from '../../contexts/ToastContext';
import Card, { CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import Alert from '../ui/Alert';
import Textarea from '../ui/Textarea';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../ui/Tabs';
import Modal from '../ui/Modal';
import { Upload, FileText, Fingerprint, CheckCircle2, X, Plus, Trash2, Sparkles, Clock, Target } from 'lucide-react';
import { cn } from '../../utils/cn';
import ProgressBar from '../ui/ProgressBar';
import CorpusBuilder from './CorpusBuilder';
import FingerprintProfile from './FingerprintProfile';

interface FingerprintStatus {
  has_fingerprint: boolean;
  fingerprint: {
    id: number;
    user_id: number;
    feature_vector: number[];
    model_version: string;
    created_at: string;
    updated_at: string;
  } | null;
  sample_count: number;
}

export default function ProfileManager() {
  const [status, setStatus] = useState<FingerprintStatus | null>(null);
  const [corpusStatus, setCorpusStatus] = useState<CorpusStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({ current: 0, total: 0, currentFile: '' });
  const [uploadText, setUploadText] = useState('');
  const [fineTuneTexts, setFineTuneTexts] = useState<string[]>(['']);
  const [isDragging, setIsDragging] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const { success, error: showError } = useToast();

  useEffect(() => {
    loadStatus();
    loadCorpusStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const data = await fingerprintAPI.getStatus();
      setStatus(data);
    } catch (err: any) {
      console.error('Load status error:', err);
      showError(getErrorMessage(err));
    }
  };

  const loadCorpusStatus = async () => {
    try {
      const data = await fingerprintAPI.corpus.getStatus();
      setCorpusStatus(data);
    } catch (err: any) {
      // Silent fail for corpus status - may not have any samples yet
      console.debug('Corpus status not available');
    }
  };

  const handleFileUpload = useCallback(async (files: FileList | File[]) => {
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

    setLoading(true);
    setUploadProgress({ current: 0, total: validFiles.length, currentFile: validFiles[0]?.name || '' });
    let successCount = 0;
    let errorCount = 0;

    // Upload files sequentially to avoid overwhelming the backend
    for (let i = 0; i < validFiles.length; i++) {
      const file = validFiles[i];
      setUploadProgress({ 
        current: i, 
        total: validFiles.length, 
        currentFile: file.name 
      });

      try {
        await fingerprintAPI.upload(undefined, file);
        successCount++;
      } catch (err: any) {
        console.error(`Upload error for ${file.name}:`, err);
        errorCount++;
        showError(`Failed to upload "${file.name}": ${getErrorMessage(err)}`);
      }
    }

    setUploadProgress({ 
      current: validFiles.length, 
      total: validFiles.length, 
      currentFile: '' 
    });

    if (successCount > 0) {
      if (validFiles.length === 1) {
        success('File uploaded successfully!');
      } else {
        success(`${successCount} file${successCount > 1 ? 's' : ''} uploaded successfully${errorCount > 0 ? ` (${errorCount} failed)` : ''}`);
      }
      await loadStatus();
    }

    setLoading(false);
    setUploadProgress({ current: 0, total: 0, currentFile: '' });
  }, [success, showError]);

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
  }, [handleFileUpload]);

  const handleTextUpload = async () => {
    if (!uploadText.trim()) {
      showError('Please enter some text');
      return;
    }

    setLoading(true);
    try {
      await fingerprintAPI.upload(uploadText);
      success('Text uploaded successfully!');
      setUploadText('');
      await loadStatus();
    } catch (err: any) {
      console.error('Upload text error:', err);
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateFingerprint = async () => {
    setLoading(true);
    try {
      await fingerprintAPI.generate();
      success('Fingerprint generated successfully!');
      await loadStatus();
    } catch (err: any) {
      console.error('Generate fingerprint error:', err);
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleFineTune = async () => {
    const validTexts = fineTuneTexts.filter((text) => text.trim());
    if (validTexts.length === 0) {
      showError('Please enter at least one text sample');
      return;
    }

    setLoading(true);
    try {
      await fingerprintAPI.fineTune(validTexts, 0.3);
      success('Fingerprint fine-tuned successfully!');
      setFineTuneTexts(['']);
      await loadStatus();
    } catch (err: any) {
      console.error('Fine-tune error:', err);
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const addFineTuneField = () => {
    setFineTuneTexts([...fineTuneTexts, '']);
  };

  const removeFineTuneField = (index: number) => {
    setFineTuneTexts(fineTuneTexts.filter((_, i) => i !== index));
  };

  const updateFineTuneText = (index: number, value: string) => {
    const newTexts = [...fineTuneTexts];
    newTexts[index] = value;
    setFineTuneTexts(newTexts);
  };

  const sampleGoal = 5;
  const progressPercentage = status ? Math.min(100, (status.sample_count / sampleGoal) * 100) : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Profile & Fingerprint</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Build your personal writing fingerprint to improve analysis accuracy
        </p>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Fingerprint Status
            </CardTitle>
            <Fingerprint className="h-4 w-4 text-primary-600 dark:text-primary-400" />
          </CardHeader>
          <CardContent>
            {status?.has_fingerprint ? (
              <div className="space-y-2">
                <Badge variant="success" size="lg">
                  <CheckCircle2 className="h-4 w-4 mr-1" />
                  Active
                </Badge>
                {status.fingerprint && (
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    <p>Model: {status.fingerprint.model_version}</p>
                    <p>Updated: {new Date(status.fingerprint.updated_at).toLocaleDateString()}</p>
                  </div>
                )}
              </div>
            ) : (
              <Badge variant="outline" size="lg">
                Not Created
              </Badge>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Writing Samples
            </CardTitle>
            <FileText className="h-4 w-4 text-success-600 dark:text-success-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {status?.sample_count || 0}
            </div>
            <div className="mt-2">
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="text-gray-600 dark:text-gray-400">Progress</span>
                <span className="text-gray-600 dark:text-gray-400">
                  {status?.sample_count || 0} / {sampleGoal}
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-success-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progressPercentage}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Recommendation
            </CardTitle>
            <Target className="h-4 w-4 text-info-600 dark:text-info-400" />
          </CardHeader>
          <CardContent>
            {!status?.has_fingerprint ? (
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Upload at least {sampleGoal - (status?.sample_count || 0)} more sample{sampleGoal - (status?.sample_count || 0) !== 1 ? 's' : ''} to generate fingerprint
              </p>
            ) : corpusStatus?.ready_for_fingerprint ? (
              <p className="text-sm text-gray-600 dark:text-gray-400">
                You have enough samples for an enhanced fingerprint with time-weighted training. Check the Enhanced Corpus tab to generate it.
              </p>
            ) : (
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Your fingerprint is active and ready to use
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Main Tabs */}
      <Tabs defaultValue="basic" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="basic">Basic Fingerprint</TabsTrigger>
          <TabsTrigger value="corpus">Enhanced Corpus</TabsTrigger>
          <TabsTrigger value="profile" disabled={!status?.has_fingerprint}>Fingerprint Profile</TabsTrigger>
        </TabsList>

        {/* Basic Fingerprint Tab */}
        <TabsContent value="basic" className="space-y-6 mt-6">
          {/* Upload Section */}
          <Card>
            <CardHeader>
              <CardTitle>Upload Writing Samples</CardTitle>
              <CardDescription>
                Upload your past writing to build your personal fingerprint. The more samples you provide, the more accurate your fingerprint will be.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="file" className="w-full">
                <TabsList>
                  <TabsTrigger value="file">Upload File</TabsTrigger>
                  <TabsTrigger value="text">Paste Text</TabsTrigger>
                </TabsList>

                <TabsContent value="file" className="space-y-4">
                  <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className={cn(
                      'border-2 border-dashed rounded-lg p-12 text-center transition-colors',
                      isDragging
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/20'
                        : 'border-gray-300 dark:border-gray-700 hover:border-primary-400 dark:hover:border-primary-600'
                    )}
                  >
                    <Upload className="h-12 w-12 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                      Drag and drop files here, or click to browse
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-500 mb-4">
                      Supports .txt, .docx, .pdf files (multiple files supported)
                    </p>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".txt,.docx,.pdf"
                      multiple
                      onChange={handleFileInputChange}
                      className="hidden"
                      id="file-upload"
                      disabled={loading}
                    />
                    <Button
                      variant="outline"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={loading}
                    >
                      <FileText className="h-4 w-4 mr-2" />
                      {loading ? 'Uploading...' : 'Choose Files'}
                    </Button>
                    {loading && uploadProgress.total > 0 && (
                      <div className="mt-4 w-full max-w-md mx-auto">
                        <ProgressBar
                          value={uploadProgress.current}
                          max={uploadProgress.total}
                          showLabel
                          label={uploadProgress.currentFile
                            ? `Uploading: ${uploadProgress.currentFile} (${uploadProgress.current + 1}/${uploadProgress.total})`
                            : `Processing files (${uploadProgress.current}/${uploadProgress.total})`}
                          size="md"
                        />
                      </div>
                    )}
                  </div>
                </TabsContent>

                <TabsContent value="text" className="space-y-4">
                  <Textarea
                    value={uploadText}
                    onChange={(e) => setUploadText(e.target.value)}
                    placeholder="Paste your writing sample here..."
                    className="min-h-[200px]"
                    disabled={loading}
                  />
                  <Button
                    onClick={handleTextUpload}
                    disabled={loading || !uploadText.trim()}
                    isLoading={loading}
                    className="w-full"
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Upload Text
                  </Button>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Generate Fingerprint */}
          <Card>
            <CardHeader>
              <CardTitle>Generate Fingerprint</CardTitle>
              <CardDescription>
                Generate your fingerprint from uploaded writing samples. You need at least one sample.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={handleGenerateFingerprint}
                disabled={loading || !status || status.sample_count === 0}
                isLoading={loading}
                className="w-full"
                size="lg"
              >
                <Sparkles className="h-5 w-5 mr-2" />
                Generate Fingerprint
              </Button>
              {status && status.sample_count === 0 && (
                <Alert variant="warning" className="mt-4">
                  Please upload at least one writing sample before generating a fingerprint.
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Fine-tune Section */}
          {status?.has_fingerprint && (
            <Card>
              <CardHeader>
                <CardTitle>Fine-tune Fingerprint</CardTitle>
                <CardDescription>
                  Add more writing samples to improve your fingerprint accuracy and adapt to your evolving writing style.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {fineTuneTexts.map((text, index) => (
                  <div key={index} className="flex gap-2">
                    <Textarea
                      value={text}
                      onChange={(e) => updateFineTuneText(index, e.target.value)}
                      placeholder="Enter a new writing sample..."
                      className="flex-1 min-h-[100px]"
                      disabled={loading}
                    />
                    {fineTuneTexts.length > 1 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFineTuneField(index)}
                        disabled={loading}
                        className="self-start"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                ))}
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={addFineTuneField}
                    disabled={loading}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Another Sample
                  </Button>
                  <Button
                    onClick={handleFineTune}
                    disabled={loading || fineTuneTexts.every((t) => !t.trim())}
                    isLoading={loading}
                    className="flex-1"
                  >
                    <Sparkles className="h-4 w-4 mr-2" />
                    Fine-tune Fingerprint
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Enhanced Corpus Tab */}
        <TabsContent value="corpus" className="mt-6">
          <CorpusBuilder />
        </TabsContent>

        {/* Fingerprint Profile Tab */}
        <TabsContent value="profile" className="mt-6">
          <FingerprintProfile />
        </TabsContent>
      </Tabs>
    </div>
  );
}
