import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { rewriteAPI, getErrorMessage } from '../../services/api';
import { useToast } from '../../contexts/ToastContext';
import Card, { CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card';
import Textarea from '../ui/Textarea';
import Input from '../ui/Input';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import Alert from '../ui/Alert';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../ui/Tabs';
import { ArrowLeft, Copy, X, Sparkles, FileText, TrendingUp, Download, RotateCcw } from 'lucide-react';
import { cn } from '../../utils/cn';

const STYLE_PRESETS = [
  { id: 'professional', label: 'Professional', description: 'Formal, clear, and concise' },
  { id: 'casual', label: 'Casual', description: 'Conversational and friendly' },
  { id: 'academic', label: 'Academic', description: 'Scholarly and detailed' },
  { id: 'creative', label: 'Creative', description: 'Expressive and engaging' },
];

export default function RewriteInterface() {
  const [originalText, setOriginalText] = useState('');
  const [rewrittenText, setRewrittenText] = useState('');
  const [loading, setLoading] = useState(false);
  const [targetStyle, setTargetStyle] = useState('');
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [rewriteIntensity, setRewriteIntensity] = useState(0.5);
  const [viewMode, setViewMode] = useState<'split' | 'diff'>('split');
  const navigate = useNavigate();
  const { success, error: showError } = useToast();

  const handleRewrite = async () => {
    if (!originalText.trim()) {
      showError('Please enter some text to rewrite');
      return;
    }

    setLoading(true);
    setRewrittenText('');

    try {
      const styleGuidance = selectedPreset
        ? STYLE_PRESETS.find((p) => p.id === selectedPreset)?.label
        : targetStyle || undefined;

      const result = await rewriteAPI.rewrite(originalText, styleGuidance);
      setRewrittenText(result.rewritten_text);
      success('Text rewritten successfully!');
    } catch (err: any) {
      console.error('Rewrite error:', err);
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setOriginalText('');
    setRewrittenText('');
    setTargetStyle('');
    setSelectedPreset(null);
    setRewriteIntensity(0.5);
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    success('Copied to clipboard!');
  };

  const handlePresetSelect = (presetId: string) => {
    setSelectedPreset(presetId);
    const preset = STYLE_PRESETS.find((p) => p.id === presetId);
    if (preset) {
      setTargetStyle(preset.description);
    }
  };

  const calculateSimilarity = () => {
    if (!originalText || !rewrittenText) return null;
    // Simple word-based similarity (in a real app, use more sophisticated algorithm)
    const originalWords = originalText.toLowerCase().split(/\s+/);
    const rewrittenWords = rewrittenText.toLowerCase().split(/\s+/);
    const commonWords = originalWords.filter((w) => rewrittenWords.includes(w));
    return (commonWords.length / Math.max(originalWords.length, rewrittenWords.length)) * 100;
  };

  const originalWordCount = originalText.split(/\s+/).filter((w) => w.length > 0).length;
  const rewrittenWordCount = rewrittenText.split(/\s+/).filter((w) => w.length > 0).length;
  const similarity = calculateSimilarity();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Style Rewriting</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Rewrite AI-generated text to match your personal writing style
          </p>
        </div>
        <Button variant="outline" onClick={() => navigate('/')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Dashboard
        </Button>
      </div>

      {/* Style Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Style Configuration</CardTitle>
          <CardDescription>
            Choose a preset style or provide custom guidance. Leave empty to use your fingerprint.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
              Style Presets
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {STYLE_PRESETS.map((preset) => (
                <button
                  key={preset.id}
                  onClick={() => handlePresetSelect(preset.id)}
                  className={cn(
                    'p-3 rounded-lg border-2 text-left transition-all',
                    selectedPreset === preset.id
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-700'
                  )}
                >
                  <div className="font-medium text-sm text-gray-900 dark:text-gray-100">
                    {preset.label}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {preset.description}
                  </div>
                </button>
              ))}
            </div>
          </div>

          <Input
            label="Custom Style Guidance (Optional)"
            value={targetStyle}
            onChange={(e) => {
              setTargetStyle(e.target.value);
              setSelectedPreset(null);
            }}
            placeholder="Describe the target writing style..."
            disabled={loading}
          />

          {selectedPreset && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setSelectedPreset(null);
                setTargetStyle('');
              }}
            >
              Clear Preset
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Original Text */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Original Text</CardTitle>
                <CardDescription>AI-generated text to rewrite</CardDescription>
              </div>
              {originalText && (
                <Button variant="ghost" size="sm" onClick={() => handleCopy(originalText)}>
                  <Copy className="h-4 w-4" />
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              value={originalText}
              onChange={(e) => setOriginalText(e.target.value)}
              placeholder="Paste AI-generated text here..."
              className="min-h-[400px] font-mono text-sm"
              autoResize
              disabled={loading}
            />
            {originalText && (
              <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400 pt-2 border-t border-gray-200 dark:border-gray-700">
                <span>{originalWordCount.toLocaleString()} words</span>
                <span>{originalText.length.toLocaleString()} characters</span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Rewritten Text */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Rewritten Text</CardTitle>
                <CardDescription>Your personal writing style</CardDescription>
              </div>
              {rewrittenText && (
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm" onClick={() => handleCopy(rewrittenText)}>
                    <Copy className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      const blob = new Blob([rewrittenText], { type: 'text/plain' });
                      const url = URL.createObjectURL(blob);
                      const link = document.createElement('a');
                      link.href = url;
                      link.download = 'rewritten-text.txt';
                      link.click();
                      URL.revokeObjectURL(url);
                      success('Downloaded!');
                    }}
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {rewrittenText ? (
              <>
                <div className="min-h-[400px] p-4 bg-gray-50 dark:bg-gray-900 rounded-lg font-mono text-sm whitespace-pre-wrap">
                  {rewrittenText}
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400 pt-2 border-t border-gray-200 dark:border-gray-700">
                  <span>{rewrittenWordCount.toLocaleString()} words</span>
                  <span>{rewrittenText.length.toLocaleString()} characters</span>
                  {similarity !== null && (
                    <Badge variant="info" size="sm">
                      {similarity.toFixed(0)}% similar
                    </Badge>
                  )}
                </div>
              </>
            ) : (
              <div className="min-h-[400px] flex items-center justify-center text-gray-400 dark:text-gray-600 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg">
                {loading ? (
                  <div className="text-center">
                    <Sparkles className="h-8 w-8 animate-pulse mx-auto mb-2" />
                    <p>Rewriting...</p>
                  </div>
                ) : (
                  <p>Rewritten text will appear here</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Action Panel */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
            <div className="flex gap-2 flex-1">
              <Button
                onClick={handleRewrite}
                disabled={loading || !originalText.trim()}
                isLoading={loading}
                size="lg"
                className="flex-1"
              >
                <Sparkles className="h-5 w-5 mr-2" />
                Rewrite Text
              </Button>
              <Button
                variant="outline"
                onClick={handleClear}
                disabled={loading}
                size="lg"
              >
                <X className="h-4 w-4 mr-2" />
                Clear All
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Comparison View */}
      {originalText && rewrittenText && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Comparison</CardTitle>
              <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as 'split' | 'diff')}>
                <TabsList>
                  <TabsTrigger value="split">Side-by-Side</TabsTrigger>
                  <TabsTrigger value="diff">Diff View</TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
          </CardHeader>
          <CardContent>
            {viewMode === 'split' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                    Original
                  </h4>
                  <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg text-sm max-h-[300px] overflow-y-auto">
                    {originalText}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                    Rewritten
                  </h4>
                  <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg text-sm max-h-[300px] overflow-y-auto">
                    {rewrittenText}
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg text-sm max-h-[400px] overflow-y-auto">
                {/* Simple diff visualization - in production, use a proper diff library */}
                <div className="space-y-2">
                  <p className="text-gray-600 dark:text-gray-400">
                    <span className="font-semibold">Original:</span> {originalText.substring(0, 200)}
                    {originalText.length > 200 && '...'}
                  </p>
                  <p className="text-gray-900 dark:text-gray-100">
                    <span className="font-semibold">Rewritten:</span> {rewrittenText.substring(0, 200)}
                    {rewrittenText.length > 200 && '...'}
                  </p>
                  {similarity !== null && (
                    <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                      <Badge variant="info">
                        Similarity: {similarity.toFixed(1)}%
                      </Badge>
                      <Badge variant={rewrittenWordCount > originalWordCount ? 'success' : 'warning'} className="ml-2">
                        {rewrittenWordCount > originalWordCount ? '+' : ''}
                        {rewrittenWordCount - originalWordCount} words
                      </Badge>
                    </div>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
