import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { analysisAPI, getErrorMessage } from '../../services/api';
import { useToast } from '../../contexts/ToastContext';
import Card, { CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card';
import Textarea from '../ui/Textarea';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import Alert from '../ui/Alert';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../ui/Tabs';
import { Upload, FileText, X, Sparkles, Clock, File } from 'lucide-react';
import { cn } from '../../utils/cn';

export default function TextInput() {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [granularity, setGranularity] = useState<'sentence' | 'paragraph'>('sentence');
  const [analysisMode, setAnalysisMode] = useState<'standard' | 'detailed' | 'quick'>('standard');
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const { success, error: showError } = useToast();

  const wordCount = text.split(/\s+/).filter((word) => word.length > 0).length;
  const charCount = text.length;
  const readingTime = Math.ceil(wordCount / 200); // Average reading speed: 200 words/min

  const handleAnalyze = async () => {
    if (!text.trim()) {
      setError('Please enter some text to analyze');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const result = await analysisAPI.analyze(text, granularity);
      sessionStorage.setItem('analysisResult', JSON.stringify(result));
      success('Analysis complete!');
      navigate('/analysis');
    } catch (err: any) {
      console.error('Analysis error:', err);
      const errorMsg = getErrorMessage(err);
      setError(errorMsg);
      showError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = useCallback((file: File) => {
    if (!file) return;

    const validTypes = ['.txt', '.docx', '.pdf'];
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!validTypes.includes(fileExtension)) {
      showError('Invalid file type. Please upload .txt, .docx, or .pdf files.');
      return;
    }

    setUploadedFileName(file.name);
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setText(content);
      success(`File "${file.name}" loaded successfully`);
    };
    reader.onerror = () => {
      showError('Error reading file');
    };
    reader.readAsText(file);
  }, [showError, success]);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileUpload(file);
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
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileUpload(file);
    }
  }, [handleFileUpload]);

  const clearText = () => {
    setText('');
    setUploadedFileName(null);
    setError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Text Analysis</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Analyze text for AI vs human writing patterns using advanced stylometric fingerprinting
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Input Panel */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Input Text</CardTitle>
              <CardDescription>Paste your text or upload a file</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* File Upload Zone */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={cn(
                  'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
                  isDragging
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/20'
                    : 'border-gray-300 dark:border-gray-700 hover:border-primary-400 dark:hover:border-primary-600',
                  text && 'border-gray-200 dark:border-gray-800'
                )}
              >
                {!text ? (
                  <>
                    <Upload className="h-12 w-12 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                      Drag and drop a file here, or click to browse
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-500 mb-4">
                      Supports .txt, .docx, .pdf files
                    </p>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".txt,.docx,.pdf"
                      onChange={handleFileInputChange}
                      className="hidden"
                      id="file-upload"
                    />
                    <Button
                      variant="outline"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <File className="h-4 w-4 mr-2" />
                      Choose File
                    </Button>
                  </>
                ) : (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <FileText className="h-8 w-8 text-primary-600 dark:text-primary-400" />
                      <div className="text-left">
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {uploadedFileName || 'Text entered'}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {wordCount.toLocaleString()} words • {charCount.toLocaleString()} characters
                        </p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" onClick={clearText}>
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                )}
              </div>

              {/* Text Input */}
              <Textarea
                value={text}
                onChange={(e) => {
                  setText(e.target.value);
                  setError('');
                }}
                placeholder="Or paste your text here..."
                className="min-h-[300px] font-mono text-sm"
                autoResize
              />

              {/* Text Stats */}
              <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                <div className="flex items-center gap-1.5">
                  <FileText className="h-4 w-4" />
                  <span>{wordCount.toLocaleString()} words</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span>{charCount.toLocaleString()} chars</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Clock className="h-4 w-4" />
                  <span>~{readingTime} min read</span>
                </div>
              </div>

              {error && (
                <Alert variant="error" title="Analysis Error">
                  {error}
                </Alert>
              )}

              {/* Analysis Options */}
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <Tabs value={granularity} onValueChange={(v) => setGranularity(v as 'sentence' | 'paragraph')}>
                  <TabsList>
                    <TabsTrigger value="sentence">Sentence-level</TabsTrigger>
                    <TabsTrigger value="paragraph">Paragraph-level</TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>

              {/* Analyze Button */}
              <Button
                onClick={handleAnalyze}
                disabled={loading || !text.trim()}
                isLoading={loading}
                className="w-full"
                size="lg"
              >
                <Sparkles className="h-5 w-5 mr-2" />
                {loading ? 'Analyzing...' : 'Analyze Text'}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar Stats */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Quick Stats</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Word Count</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {wordCount.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Character Count</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {charCount.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Reading Time</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  ~{readingTime} min
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Analysis Mode</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="mode"
                    value="quick"
                    checked={analysisMode === 'quick'}
                    onChange={() => setAnalysisMode('quick')}
                    className="text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm">Quick (faster, less detailed)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="mode"
                    value="standard"
                    checked={analysisMode === 'standard'}
                    onChange={() => setAnalysisMode('standard')}
                    className="text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm">Standard (recommended)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="mode"
                    value="detailed"
                    checked={analysisMode === 'detailed'}
                    onChange={() => setAnalysisMode('detailed')}
                    className="text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm">Detailed (slower, more accurate)</span>
                </label>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => navigate('/profile')}
              >
                Manage Fingerprint
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => navigate('/rewrite')}
              >
                Style Rewriting
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => navigate('/history')}
              >
                View History
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
