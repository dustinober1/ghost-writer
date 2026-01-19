import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Card, { CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import Alert from '../ui/Alert';
import { Tabs, TabsList, TabsTrigger } from '../ui/Tabs';
import { ArrowLeft, Download, Share2, Info, TrendingUp, TrendingDown, Minus, Repeat2, X } from 'lucide-react';
import { useToast } from '../../contexts/ToastContext';
import { cn } from '../../utils/cn';

interface FeatureAttribution {
  feature_name: string;
  importance: number;
  interpretation: string;
}

interface OverusedPattern {
  pattern_type: 'repeated_phrase' | 'sentence_start' | 'word_repetition';
  pattern: string;
  count: number;
  locations: number[];
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  percentage?: number;
  examples?: string[];
}

interface TextSegment {
  text: string;
  ai_probability: number;
  start_index: number;
  end_index: number;
  confidence_level: 'HIGH' | 'MEDIUM' | 'LOW';
  feature_attribution?: FeatureAttribution[];
  sentence_explanation?: string;
}

interface HeatMapData {
  segments: TextSegment[];
  overall_ai_probability: number;
  confidence_distribution?: {
    high: number;
    medium: number;
    low: number;
  };
  document_explanation?: string;
  overused_patterns?: OverusedPattern[];
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
  const [dismissPatternCard, setDismissPatternCard] = useState(false);
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

  const getConfidenceVariant = (level: 'HIGH' | 'MEDIUM' | 'LOW'): 'error' | 'warning' | 'success' => {
    switch (level) {
      case 'HIGH':
        return 'error';
      case 'MEDIUM':
        return 'warning';
      case 'LOW':
        return 'success';
      default:
        return 'success';
    }
  };

  const getConfidenceLabel = (level: 'HIGH' | 'MEDIUM' | 'LOW'): string => {
    switch (level) {
      case 'HIGH':
        return 'High AI Likelihood';
      case 'MEDIUM':
        return 'Mixed Patterns';
      case 'LOW':
        return 'Human-like';
      default:
        return 'Unknown';
    }
  };

  const getConfidenceDescription = (level: 'HIGH' | 'MEDIUM' | 'LOW'): string => {
    switch (level) {
      case 'HIGH':
        return 'This sentence shows strong AI-generated patterns';
      case 'MEDIUM':
        return 'This sentence shows some AI-like characteristics';
      case 'LOW':
        return 'This sentence appears more human-written';
      default:
        return '';
    }
  };

  const getImportanceColor = (importance: number): string => {
    if (importance > 0.7) {
      return 'bg-red-500';
    } else if (importance > 0.4) {
      return 'bg-yellow-500';
    } else {
      return 'bg-green-500';
    }
  };

  const getImportanceVariant = (importance: number): 'high' | 'medium' | 'low' => {
    if (importance > 0.7) return 'high';
    if (importance > 0.4) return 'medium';
    return 'low';
  };

  // Pattern-related helper functions
  const getPatternSeverityVariant = (severity: 'HIGH' | 'MEDIUM' | 'LOW'): 'error' | 'warning' | 'success' => {
    switch (severity) {
      case 'HIGH':
        return 'error';
      case 'MEDIUM':
        return 'warning';
      case 'LOW':
        return 'success';
      default:
        return 'success';
    }
  };

  const getPatternTypeLabel = (patternType: string): string => {
    switch (patternType) {
      case 'repeated_phrase':
        return 'Repeated Phrase';
      case 'sentence_start':
        return 'Sentence Start';
      case 'word_repetition':
        return 'Word Repetition';
      default:
        return 'Pattern';
    }
  };

  const getPatternHighlightsInSegment = (segment: TextSegment): OverusedPattern[] => {
    if (!heat_map_data.overused_patterns) return [];

    return heat_map_data.overused_patterns.filter(pattern =>
      pattern.locations.some(location =>
        location >= segment.start_index && location < segment.end_index
      )
    );
  };

  const scrollToLocation = (location: number) => {
    // Find the segment that contains this location
    const targetSegment = heat_map_data.segments.find(seg =>
      location >= seg.start_index && location < seg.end_index
    );

    if (targetSegment) {
      setSelectedSegment(targetSegment);
      // Scroll the segment into view
      const segmentElement = document.querySelector(`[data-segment-index="${targetSegment.start_index}"]`);
      if (segmentElement) {
        segmentElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
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
        ['Segment', 'Text', 'AI Probability', 'Confidence Level', 'Start Index', 'End Index'],
        ...analysisResult.heat_map_data.segments.map((seg, idx) => [
          idx + 1,
          `"${seg.text.replace(/"/g, '""')}"`,
          seg.ai_probability.toFixed(4),
          seg.confidence_level,
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

  const { heat_map_data } = analysisResult;
  const { overall_ai_probability } = heat_map_data;
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

          {/* Document Explanation Card */}
          {heat_map_data.document_explanation && (
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Info className="h-5 w-5 text-primary-500" />
                  <CardTitle>What This Means</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                  {heat_map_data.document_explanation}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Repetitive Patterns Card */}
          {heat_map_data.overused_patterns && heat_map_data.overused_patterns.length > 0 && !dismissPatternCard && (
            <Card className="border-orange-200 dark:border-orange-800">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Repeat2 className="h-5 w-5 text-orange-500" />
                    <CardTitle>Repetitive Patterns Detected</CardTitle>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setDismissPatternCard(true)}
                    className="h-8 w-8 p-0"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
                <CardDescription>
                  {heat_map_data.overused_patterns.length} pattern{heat_map_data.overused_patterns.length > 1 ? 's' : ''} found that may indicate AI-generated content
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {heat_map_data.overused_patterns.slice(0, 5).map((pattern, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-750 transition-colors cursor-pointer"
                    onClick={() => scrollToLocation(pattern.locations[0])}
                  >
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {getPatternTypeLabel(pattern.pattern_type)}
                          </span>
                          <Badge variant={getPatternSeverityVariant(pattern.severity)} size="sm">
                            {pattern.severity}
                          </Badge>
                        </div>
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100 italic">
                          "{pattern.pattern}"
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-gray-900 dark:text-gray-100">
                          {pattern.count}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          use{pattern.count > 1 ? 's' : ''}
                        </p>
                      </div>
                    </div>
                    {pattern.percentage !== undefined && (
                      <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400">
                        <span>Frequency</span>
                        <span className="font-medium">{(pattern.percentage * 100).toFixed(1)}%</span>
                      </div>
                    )}
                    {pattern.examples && pattern.examples.length > 0 && (
                      <details className="mt-2">
                        <summary className="text-xs text-primary-500 cursor-pointer hover:underline">
                          View examples
                        </summary>
                        <ul className="mt-1 ml-4 text-xs text-gray-600 dark:text-gray-400 list-disc">
                          {pattern.examples.slice(0, 2).map((example, exIdx) => (
                            <li key={exIdx}>{example}</li>
                          ))}
                          {pattern.examples.length > 2 && (
                            <li className="text-gray-400">and {pattern.examples.length - 2} more...</li>
                          )}
                        </ul>
                      </details>
                    )}
                  </div>
                ))}
                {heat_map_data.overused_patterns.length > 5 && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 text-center pt-2">
                    And {heat_map_data.overused_patterns.length - 5} more patterns...
                  </p>
                )}
              </CardContent>
            </Card>
          )}

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
              <CardDescription>Click on segments to view detailed information. Patterns are highlighted in text.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="p-6 bg-gray-50 dark:bg-gray-900 rounded-lg min-h-[300px] leading-relaxed">
                {heat_map_data.segments.map((segment, index) => {
                  const bgColor = getColorForProbability(segment.ai_probability);
                  const textColor = getTextColor(segment.ai_probability);
                  const isSelected = selectedSegment === segment;
                  const isHovered = hoveredSegment === index;
                  const confidenceVariant = getConfidenceVariant(segment.confidence_level);
                  const segmentPatterns = getPatternHighlightsInSegment(segment);

                  // Get the most severe pattern for this segment (if any)
                  const mostSeverePattern = segmentPatterns.length > 0
                    ? segmentPatterns.reduce((prev, current) =>
                        prev.severity === 'HIGH' ? prev :
                        current.severity === 'HIGH' ? current :
                        prev.severity === 'MEDIUM' ? prev : current
                      )
                    : null;

                  // Determine pattern highlight color
                  const getPatternHighlightStyle = () => {
                    if (!mostSeverePattern) return {};
                    const severity = mostSeverePattern.severity;
                    if (severity === 'HIGH') {
                      return {
                        borderBottom: '3px solid rgba(239, 68, 68, 0.8)',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)'
                      };
                    } else if (severity === 'MEDIUM') {
                      return {
                        borderBottom: '3px solid rgba(251, 191, 36, 0.8)',
                        backgroundColor: 'rgba(251, 191, 36, 0.1)'
                      };
                    } else {
                      return {
                        borderBottom: '3px solid rgba(156, 163, 175, 0.8)',
                        backgroundColor: 'rgba(156, 163, 175, 0.1)'
                      };
                    }
                  };

                  // Create tooltip text with pattern information
                  const getTooltipText = () => {
                    let tooltip = `AI Probability: ${(segment.ai_probability * 100).toFixed(1)}% (${segment.confidence_level})\n${getConfidenceDescription(segment.confidence_level)}`;
                    if (segmentPatterns.length > 0) {
                      tooltip += '\n\nPatterns detected:';
                      segmentPatterns.slice(0, 2).forEach(p => {
                        tooltip += `\n- ${getPatternTypeLabel(p.pattern_type)}: "${p.pattern}" (${p.count}x)`;
                      });
                      if (segmentPatterns.length > 2) {
                        tooltip += `\n- and ${segmentPatterns.length - 2} more...`;
                      }
                    }
                    return tooltip;
                  };

                  return (
                    <span
                      key={index}
                      data-segment-index={segment.start_index}
                      className={cn(
                        'inline-block px-1 py-0.5 mx-0.5 rounded cursor-pointer transition-all relative',
                        isSelected && 'ring-2 ring-primary-500 ring-offset-2',
                        isHovered && 'scale-105 shadow-md'
                      )}
                      style={{
                        backgroundColor: bgColor,
                        color: textColor,
                        border: confidenceVariant === 'error' ? '2px solid rgba(239, 68, 68, 0.5)' :
                               confidenceVariant === 'warning' ? '2px solid rgba(251, 191, 36, 0.5)' :
                               '2px solid rgba(34, 197, 94, 0.5)',
                        ...getPatternHighlightStyle()
                      }}
                      onClick={() => setSelectedSegment(segment)}
                      onMouseEnter={() => setHoveredSegment(index)}
                      onMouseLeave={() => setHoveredSegment(null)}
                      title={getTooltipText()}
                    >
                      {segment.text}
                      {/* Confidence Badge Overlay */}
                      <span
                        className={cn(
                          'absolute -top-1 -right-1 text-[10px] font-bold px-1 py-0 rounded-sm leading-none',
                          confidenceVariant === 'error' && 'bg-red-600 text-white',
                          confidenceVariant === 'warning' && 'bg-yellow-500 text-white',
                          confidenceVariant === 'success' && 'bg-green-600 text-white'
                        )}
                      >
                        {segment.confidence_level.charAt(0)}
                      </span>
                      {/* Pattern Indicator */}
                      {segmentPatterns.length > 0 && (
                        <span
                          className={cn(
                            'absolute -bottom-1 -right-1 text-[8px] font-bold px-1 py-0 rounded-sm leading-none',
                            mostSeverePattern?.severity === 'HIGH' && 'bg-red-500 text-white',
                            mostSeverePattern?.severity === 'MEDIUM' && 'bg-yellow-500 text-white',
                            mostSeverePattern?.severity === 'LOW' && 'bg-gray-500 text-white'
                          )}
                          title={`${segmentPatterns.length} pattern${segmentPatterns.length > 1 ? 's' : ''} detected`}
                        >
                          P
                        </span>
                      )}
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
            <Card
              className={cn(
                'border-2',
                getConfidenceVariant(selectedSegment.confidence_level) === 'error' && 'border-red-500',
                getConfidenceVariant(selectedSegment.confidence_level) === 'warning' && 'border-yellow-500',
                getConfidenceVariant(selectedSegment.confidence_level) === 'success' && 'border-green-500'
              )}
            >
              <CardHeader>
                <CardTitle>Segment Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Prominent Confidence Badge */}
                <div className="flex items-center justify-between p-4 rounded-lg bg-gray-50 dark:bg-gray-800">
                  <div className="flex-1">
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Confidence Level</p>
                    <Badge
                      variant={getConfidenceVariant(selectedSegment.confidence_level)}
                      size="lg"
                      className="text-base px-4 py-1"
                    >
                      {selectedSegment.confidence_level}
                    </Badge>
                  </div>
                  <div className="text-right">
                    <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                      {(selectedSegment.ai_probability * 100).toFixed(1)}%
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">AI Probability</p>
                  </div>
                </div>

                {/* Confidence Description */}
                <Alert variant={getConfidenceVariant(selectedSegment.confidence_level)}>
                  <p className="text-sm">{getConfidenceDescription(selectedSegment.confidence_level)}</p>
                </Alert>

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

          {/* Why This Flag? - Feature Attribution */}
          {selectedSegment && selectedSegment.feature_attribution && selectedSegment.feature_attribution.length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>Why This Flag?</CardTitle>
                <CardDescription>Top contributing features</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {selectedSegment.feature_attribution.map((feature, idx) => (
                  <div key={idx} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {feature.feature_name}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {(feature.importance * 100).toFixed(0)}%
                      </span>
                    </div>
                    {/* Importance Bar */}
                    <div className="relative w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className={cn(
                          'h-full transition-all duration-300 rounded-full',
                          getImportanceColor(feature.importance)
                        )}
                        style={{ width: `${feature.importance * 100}%` }}
                        aria-label={`${feature.feature_name} importance: ${(feature.importance * 100).toFixed(0)}%`}
                      />
                    </div>
                    {/* Interpretation */}
                    <p className="text-xs text-gray-600 dark:text-gray-400 italic">
                      {feature.interpretation}
                    </p>
                  </div>
                ))}
              </CardContent>
            </Card>
          ) : null}

          {/* In Plain English - Sentence Explanation */}
          {selectedSegment && selectedSegment.sentence_explanation ? (
            <Card>
              <CardHeader>
                <CardTitle>In Plain English</CardTitle>
                <CardDescription>Why this sentence was flagged</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                  {selectedSegment.sentence_explanation}
                </p>
              </CardContent>
            </Card>
          ) : selectedSegment ? (
            <Card>
              <CardContent className="text-center py-6">
                <Info className="h-8 w-8 text-gray-400 dark:text-gray-600 mx-auto mb-3" />
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Sentence explanation not available for this segment
                </p>
              </CardContent>
            </Card>
          ) : null}

          {/* Statistics */}
          <Card>
            <CardHeader>
              <CardTitle>Statistics</CardTitle>
              <CardDescription>Confidence level distribution</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Confidence Distribution Visualization */}
              <div className="space-y-2">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">Confidence Distribution</p>

                {/* Stacked Bar */}
                <div className="w-full h-6 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden flex">
                  {(() => {
                    const high = heat_map_data.segments.filter(s => s.confidence_level === 'HIGH').length;
                    const medium = heat_map_data.segments.filter(s => s.confidence_level === 'MEDIUM').length;
                    const low = heat_map_data.segments.filter(s => s.confidence_level === 'LOW').length;
                    const total = heat_map_data.segments.length;
                    const highPct = total > 0 ? (high / total) * 100 : 0;
                    const mediumPct = total > 0 ? (medium / total) * 100 : 0;
                    const lowPct = total > 0 ? (low / total) * 100 : 0;

                    return (
                      <>
                        <div
                          className="bg-red-500 h-full flex items-center justify-center text-[10px] text-white font-medium"
                          style={{ width: `${highPct}%` }}
                          title={`High: ${high} (${highPct.toFixed(1)}%)`}
                        >
                          {highPct > 10 ? `${high}` : ''}
                        </div>
                        <div
                          className="bg-yellow-500 h-full flex items-center justify-center text-[10px] text-white font-medium"
                          style={{ width: `${mediumPct}%` }}
                          title={`Medium: ${medium} (${mediumPct.toFixed(1)}%)`}
                        >
                          {mediumPct > 10 ? `${medium}` : ''}
                        </div>
                        <div
                          className="bg-green-500 h-full flex items-center justify-center text-[10px] text-white font-medium"
                          style={{ width: `${lowPct}%` }}
                          title={`Low: ${low} (${lowPct.toFixed(1)}%)`}
                        >
                          {lowPct > 10 ? `${low}` : ''}
                        </div>
                      </>
                    );
                  })()}
                </div>

                {/* Legend with counts */}
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="flex flex-col items-center p-2 bg-red-50 dark:bg-red-900/20 rounded">
                    <span className="font-semibold text-red-700 dark:text-red-400">HIGH</span>
                    <span className="text-lg font-bold text-red-900 dark:text-red-300">
                      {heat_map_data.segments.filter(s => s.confidence_level === 'HIGH').length}
                    </span>
                    <span className="text-[10px] text-red-600 dark:text-red-500">
                      {((heat_map_data.segments.filter(s => s.confidence_level === 'HIGH').length / heat_map_data.segments.length) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex flex-col items-center p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded">
                    <span className="font-semibold text-yellow-700 dark:text-yellow-400">MEDIUM</span>
                    <span className="text-lg font-bold text-yellow-900 dark:text-yellow-300">
                      {heat_map_data.segments.filter(s => s.confidence_level === 'MEDIUM').length}
                    </span>
                    <span className="text-[10px] text-yellow-600 dark:text-yellow-500">
                      {((heat_map_data.segments.filter(s => s.confidence_level === 'MEDIUM').length / heat_map_data.segments.length) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex flex-col items-center p-2 bg-green-50 dark:bg-green-900/20 rounded">
                    <span className="font-semibold text-green-700 dark:text-green-400">LOW</span>
                    <span className="text-lg font-bold text-green-900 dark:text-green-300">
                      {heat_map_data.segments.filter(s => s.confidence_level === 'LOW').length}
                    </span>
                    <span className="text-[10px] text-green-600 dark:text-green-500">
                      {((heat_map_data.segments.filter(s => s.confidence_level === 'LOW').length / heat_map_data.segments.length) * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Traditional Statistics */}
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">Total Segments</span>
                  <span className="font-medium text-gray-900 dark:text-gray-100">
                    {heat_map_data.segments.length}
                  </span>
                </div>

                {/* Pattern Statistics */}
                {heat_map_data.overused_patterns && heat_map_data.overused_patterns.length > 0 && (
                  <>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Repetitive Patterns</span>
                      <span className="font-medium text-gray-900 dark:text-gray-100">
                        {heat_map_data.overused_patterns.length}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Repeated Phrases</span>
                      <span className="font-medium text-gray-900 dark:text-gray-100">
                        {heat_map_data.overused_patterns.filter(p => p.pattern_type === 'repeated_phrase').length}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Sentence Starts</span>
                      <span className="font-medium text-gray-900 dark:text-gray-100">
                        {heat_map_data.overused_patterns.filter(p => p.pattern_type === 'sentence_start').length}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Word Repetitions</span>
                      <span className="font-medium text-gray-900 dark:text-gray-100">
                        {heat_map_data.overused_patterns.filter(p => p.pattern_type === 'word_repetition').length}
                      </span>
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
