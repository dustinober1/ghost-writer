import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Card, { CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import Alert from '../ui/Alert';
import { Tabs, TabsList, TabsTrigger } from '../ui/Tabs';
import { ArrowLeft, Download, Share2, Save, Info, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useToast } from '../../contexts/ToastContext';
import { cn } from '../../utils/cn';

interface TextSegment {
  text: string;
  ai_probability: number;
  start_index: number;
  end_index: number;
}

interface HeatMapData {
  segments: TextSegment[];
  overall_ai_probability: number;
}

interface AnalysisResult {
  heat_map_data: HeatMapData;
  analysis_id: number;
  created_at: string;
}

export default function HeatMap() {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [granularity, setGranularity] = useState<'sentence' | 'paragraph'>('sentence');
  const [selectedSegment, setSelectedSegment] = useState<TextSegment | null>(null);
  const [hoveredSegment, setHoveredSegment] = useState<number | null>(null);
  const navigate = useNavigate();
  const { success } = useToast();

  useEffect(() => {
    const stored = sessionStorage.getItem('analysisResult');
    if (stored) {
      try {
        const result = JSON.parse(stored);
        setAnalysisResult(result);
      } catch (e) {
        console.error('Error parsing analysis result:', e);
        navigate('/analyze');
      }
    } else {
      navigate('/analyze');
    }
  }, [navigate]);

  const getColorForProbability = (probability: number): string => {
    const red = Math.min(255, Math.round(probability * 255));
    const green = Math.min(255, Math.round((1 - probability) * 255));
    const blue = 50;
    return `rgb(${red}, ${green}, ${blue})`;
  };

  const getTextColor = (probability: number): string => {
    return probability > 0.5 ? '#ffffff' : '#000000';
  };

  const getInterpretation = (probability: number) => {
    if (probability > 0.7) {
      return { label: 'High AI Likelihood', variant: 'error' as const, icon: TrendingUp };
    } else if (probability > 0.4) {
      return { label: 'Mixed', variant: 'warning' as const, icon: Minus };
    } else {
      return { label: 'Human-like', variant: 'success' as const, icon: TrendingDown };
    }
  };

  const handleExport = (format: 'json' | 'csv' | 'pdf') => {
    if (!analysisResult) return;

    if (format === 'json') {
      const dataStr = JSON.stringify(analysisResult, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `analysis-${analysisResult.analysis_id}.json`;
      link.click();
      URL.revokeObjectURL(url);
      success('Analysis exported as JSON');
    } else if (format === 'csv') {
      const csvRows = [
        ['Segment', 'Text', 'AI Probability', 'Start Index', 'End Index'],
        ...analysisResult.heat_map_data.segments.map((seg, idx) => [
          idx + 1,
          `"${seg.text.replace(/"/g, '""')}"`,
          seg.ai_probability.toFixed(4),
          seg.start_index,
          seg.end_index,
        ]),
      ];
      const csvContent = csvRows.map((row) => row.join(',')).join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `analysis-${analysisResult.analysis_id}.csv`;
      link.click();
      URL.revokeObjectURL(url);
      success('Analysis exported as CSV');
    } else {
      // PDF export would require a library like jsPDF
      success('PDF export coming soon!');
    }
  };

  if (!analysisResult) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-gray-500 dark:text-gray-400">Loading analysis...</div>
      </div>
    );
  }

  const { heat_map_data, overall_ai_probability } = analysisResult;
  const interpretation = getInterpretation(overall_ai_probability);
  const InterpretationIcon = interpretation.icon;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Analysis Results</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Analyzed on {new Date(analysisResult.created_at).toLocaleString()}
          </p>
        </div>
        <Button variant="outline" onClick={() => navigate('/analyze')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Analysis
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Summary Card */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Overall AI Probability</CardTitle>
                  <CardDescription>Confidence score for the entire document</CardDescription>
                </div>
                <Badge variant={interpretation.variant} size="lg">
                  <InterpretationIcon className="h-4 w-4 mr-1" />
                  {interpretation.label}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center">
                <div className="text-6xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                  {(overall_ai_probability * 100).toFixed(1)}%
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {overall_ai_probability > 0.7
                    ? 'High likelihood of AI-generated content'
                    : overall_ai_probability > 0.4
                    ? 'Mixed - some AI-like patterns detected'
                    : 'Low likelihood - appears more human-written'}
                </p>
              </div>

              {/* Progress Bar */}
              <div className="relative w-full h-8 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={cn(
                    'h-full transition-all duration-500 rounded-full',
                    overall_ai_probability > 0.7
                      ? 'bg-error-500'
                      : overall_ai_probability > 0.4
                      ? 'bg-warning-500'
                      : 'bg-success-500'
                  )}
                  style={{ width: `${overall_ai_probability * 100}%` }}
                />
                <div className="absolute inset-0 flex items-center justify-center text-xs font-medium text-gray-700 dark:text-gray-300">
                  Confidence Meter
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
                <Button
                  variant="outline"
                  onClick={() => handleExport('json')}
                  className="flex-1"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Export JSON
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleExport('csv')}
                  className="flex-1"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Export CSV
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    if (navigator.share) {
                      navigator.share({
                        title: 'Analysis Results',
                        text: `AI Probability: ${(overall_ai_probability * 100).toFixed(1)}%`,
                      });
                    } else {
                      success('Share functionality coming soon!');
                    }
                  }}
                >
                  <Share2 className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Granularity Selector */}
          <Card>
            <CardHeader>
              <CardTitle>View Options</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs value={granularity} onValueChange={(v) => setGranularity(v as 'sentence' | 'paragraph')}>
                <TabsList>
                  <TabsTrigger value="sentence">Sentence-level</TabsTrigger>
                  <TabsTrigger value="paragraph">Paragraph-level</TabsTrigger>
                </TabsList>
              </Tabs>
            </CardContent>
          </Card>

          {/* Legend */}
          <Card>
            <CardHeader>
              <CardTitle>Color Legend</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-4">
                <div className="flex items-center gap-2">
                  <div
                    className="w-6 h-6 rounded border border-gray-300 dark:border-gray-700"
                    style={{ backgroundColor: getColorForProbability(0) }}
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Human-like (0%)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div
                    className="w-6 h-6 rounded border border-gray-300 dark:border-gray-700"
                    style={{ backgroundColor: getColorForProbability(0.5) }}
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Mixed (50%)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div
                    className="w-6 h-6 rounded border border-gray-300 dark:border-gray-700"
                    style={{ backgroundColor: getColorForProbability(1) }}
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">AI-like (100%)</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Heatmap Text */}
          <Card>
            <CardHeader>
              <CardTitle>Text Analysis</CardTitle>
              <CardDescription>Click on segments to view detailed information</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="p-6 bg-gray-50 dark:bg-gray-900 rounded-lg min-h-[300px] leading-relaxed">
                {heat_map_data.segments.map((segment, index) => {
                  const bgColor = getColorForProbability(segment.ai_probability);
                  const textColor = getTextColor(segment.ai_probability);
                  const isSelected = selectedSegment === segment;
                  const isHovered = hoveredSegment === index;

                  return (
                    <span
                      key={index}
                      className={cn(
                        'inline-block px-1 py-0.5 mx-0.5 rounded cursor-pointer transition-all',
                        isSelected && 'ring-2 ring-primary-500 ring-offset-2',
                        isHovered && 'scale-105 shadow-md'
                      )}
                      style={{
                        backgroundColor: bgColor,
                        color: textColor,
                      }}
                      onClick={() => setSelectedSegment(segment)}
                      onMouseEnter={() => setHoveredSegment(index)}
                      onMouseLeave={() => setHoveredSegment(null)}
                      title={`AI Probability: ${(segment.ai_probability * 100).toFixed(1)}%`}
                    >
                      {segment.text}
                    </span>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar - Segment Details */}
        <div className="space-y-6">
          {selectedSegment ? (
            <Card>
              <CardHeader>
                <CardTitle>Segment Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">AI Probability</p>
                  <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                    {(selectedSegment.ai_probability * 100).toFixed(1)}%
                  </div>
                  <Badge variant={getInterpretation(selectedSegment.ai_probability).variant} className="mt-2">
                    {getInterpretation(selectedSegment.ai_probability).label}
                  </Badge>
                </div>

                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Text Preview</p>
                  <p className="text-sm text-gray-900 dark:text-gray-100 bg-gray-100 dark:bg-gray-800 p-3 rounded">
                    {selectedSegment.text.length > 200
                      ? selectedSegment.text.substring(0, 200) + '...'
                      : selectedSegment.text}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Start Index</p>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {selectedSegment.start_index}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">End Index</p>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {selectedSegment.end_index}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Length</p>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {selectedSegment.end_index - selectedSegment.start_index} chars
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Word Count</p>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {selectedSegment.text.split(/\s+/).filter((w) => w.length > 0).length}
                    </p>
                  </div>
                </div>

                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => setSelectedSegment(null)}
                >
                  Clear Selection
                </Button>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="text-center py-8">
                <Info className="h-12 w-12 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Click on any highlighted segment to view detailed analysis
                </p>
              </CardContent>
            </Card>
          )}

          {/* Statistics */}
          <Card>
            <CardHeader>
              <CardTitle>Statistics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Total Segments</span>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {heat_map_data.segments.length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">High AI (>70%)</span>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {heat_map_data.segments.filter((s) => s.ai_probability > 0.7).length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Medium (40-70%)</span>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {heat_map_data.segments.filter((s) => s.ai_probability >= 0.4 && s.ai_probability <= 0.7).length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Low AI (<40%)</span>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {heat_map_data.segments.filter((s) => s.ai_probability < 0.4).length}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
