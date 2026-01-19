import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import Card, { CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import Alert from '../ui/Alert';
import { Tabs, TabsList, TabsTrigger } from '../ui/Tabs';
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  Calendar,
  FileText,
  GitCompare,
  Download,
  Info,
  CheckCircle,
  XCircle,
  Activity
} from 'lucide-react';
import { useToast } from '../../contexts/ToastContext';
import { cn } from '../../utils/cn';
import { api } from '../../services/api';

// Types
interface TimelineDataPoint {
  version_id: number;
  version_number: number;
  timestamp: string;
  word_count: number;
  avg_ai_prob: number;
  max_ai_prob: number;
  min_ai_prob: number;
  std_ai_prob: number;
  high_confidence_count: number;
  medium_confidence_count: number;
  low_confidence_count: number;
  overall_ai_probability: number;
}

interface TimelineResponse {
  timeline: TimelineDataPoint[];
  overall_trend: 'increasing' | 'decreasing' | 'stable' | 'insufficient_data' | 'no_data';
  ai_velocity: number;
  total_versions: number;
  error?: string;
}

interface InjectionEvent {
  version: number;
  version_id: number;
  timestamp: string;
  position: number;
  text: string;
  ai_probability: number;
  type: 'addition' | 'modification';
  severity: 'high' | 'medium' | 'low';
  delta_ai?: number;
  old_text?: string;
  new_text?: string;
}

interface MixedAuthorshipIndicator {
  type: string;
  description: string;
  value: number;
  severity: string;
  version?: number;
  from_version?: number;
  to_version?: number;
  segment_index?: number;
}

interface InjectionResponse {
  injection_events: InjectionEvent[];
  injection_score: number;
  total_injections: number;
  additions_count: number;
  modifications_count: number;
  severity_breakdown: { high: number; medium: number; low: number };
  mixed_authorship_indicators: MixedAuthorshipIndicator[];
  overall_risk: 'high' | 'medium' | 'low' | 'none';
}

interface DiffSection {
  text: string;
  position: number;
  ai_probability?: number;
  old_text?: string;
  new_text?: string;
  old_position?: number;
  delta_ai?: number;
}

interface VersionComparison {
  added_sections: DiffSection[];
  removed_sections: DiffSection[];
  modified_sections: DiffSection[];
  similarity_score: number;
  version_a_number: number;
  version_b_number: number;
}

export default function TemporalAnalysis() {
  const [searchParams] = useSearchParams();
  const documentId = searchParams.get('documentId') || 'default-doc';
  const { success, error } = useToast();

  const [activeTab, setActiveTab] = useState<'timeline' | 'injections' | 'compare'>('timeline');
  const [timelineData, setTimelineData] = useState<TimelineResponse | null>(null);
  const [injectionData, setInjectionData] = useState<InjectionResponse | null>(null);
  const [comparisonData, setComparisonData] = useState<VersionComparison | null>(null);
  const [loading, setLoading] = useState(true);
  const [versionA, setVersionA] = useState<number>(1);
  const [versionB, setVersionB] = useState<number>(2);

  useEffect(() => {
    loadTemporalData();
  }, [documentId]);

  const loadTemporalData = async () => {
    setLoading(true);
    try {
      // Load timeline data
      const timelineResponse = await api.get(`/api/temporal/timeline/${encodeURIComponent(documentId)}`);
      setTimelineData(timelineResponse.data);

      // Load injection data
      const injectionResponse = await api.get(`/api/temporal/injections/${encodeURIComponent(documentId)}`);
      setInjectionData(injectionResponse.data);

      // Set default version numbers for comparison
      if (timelineResponse.data.timeline && timelineResponse.data.timeline.length >= 2) {
        const versions = timelineResponse.data.timeline;
        setVersionA(versions[0].version_number);
        setVersionB(versions[versions.length - 1].version_number);
      }
    } catch (err: any) {
      error(err.response?.data?.detail || 'Failed to load temporal analysis');
      console.error('Error loading temporal data:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadComparison = async () => {
    if (versionA === versionB) {
      error('Please select different versions to compare');
      return;
    }
    try {
      const response = await api.post('/api/temporal/compare', {
        document_id: documentId,
        version_a: versionA,
        version_b: versionB
      });
      setComparisonData(response.data);
      success('Versions compared successfully');
    } catch (err: any) {
      error(err.response?.data?.detail || 'Failed to compare versions');
    }
  };

  const exportTimelineData = () => {
    if (!timelineData) return;

    const dataStr = JSON.stringify(timelineData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `timeline-${documentId}.json`;
    link.click();
    URL.revokeObjectURL(url);
    success('Timeline data exported');
  };

  // Helper functions
  const getTrendIcon = () => {
    if (!timelineData) return Minus;
    switch (timelineData.overall_trend) {
      case 'increasing': return TrendingUp;
      case 'decreasing': return TrendingDown;
      default: return Minus;
    }
  };

  const getTrendVariant = (): 'success' | 'warning' | 'error' => {
    if (!timelineData) return 'success';
    switch (timelineData.overall_trend) {
      case 'increasing': return 'error';
      case 'decreasing': return 'success';
      default: return 'warning';
    }
  };

  const getTrendLabel = () => {
    if (!timelineData) return 'Unknown';
    switch (timelineData.overall_trend) {
      case 'increasing': return 'Increasing AI Usage';
      case 'decreasing': return 'Decreasing AI Usage';
      case 'stable': return 'Stable';
      case 'insufficient_data': return 'Insufficient Data';
      case 'no_data': return 'No Data';
      default: return 'Unknown';
    }
  };

  const getRiskVariant = (risk: string): 'success' | 'warning' | 'error' => {
    switch (risk) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'success';
    }
  };

  const getSeverityVariant = (severity: string): 'success' | 'warning' | 'error' => {
    switch (severity) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'success';
    }
  };

  const getColorForProbability = (probability: number): string => {
    const red = Math.min(255, Math.round(probability * 255));
    const green = Math.min(255, Math.round((1 - probability) * 255));
    return `rgb(${red}, ${green}, 50)`;
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return dateStr;
    }
  };

  const TrendIcon = getTrendIcon();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-gray-500 dark:text-gray-400">Loading temporal analysis...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Temporal Analysis</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Document ID: {documentId}
          </p>
        </div>
        <Button variant="outline" onClick={() => window.history.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
      </div>

      {/* Summary Cards */}
      {timelineData && timelineData.total_versions > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Versions</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {timelineData.total_versions}
                  </p>
                </div>
                <FileText className="h-8 w-8 text-primary-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Overall Trend</p>
                  <Badge variant={getTrendVariant()} className="mt-1">
                    <TrendIcon className="h-3 w-3 mr-1" />
                    {getTrendLabel()}
                  </Badge>
                </div>
                <Activity className="h-8 w-8 text-primary-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">AI Velocity</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {timelineData.ai_velocity > 0 ? '+' : ''}{(timelineData.ai_velocity * 100).toFixed(1)}%
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-primary-500" />
              </div>
            </CardContent>
          </Card>

          {injectionData && (
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Injection Risk</p>
                    <Badge variant={getRiskVariant(injectionData.overall_risk)} className="mt-1">
                      {injectionData.overall_risk.charAt(0).toUpperCase() + injectionData.overall_risk.slice(1)}
                    </Badge>
                  </div>
                  <AlertTriangle className={`h-8 w-8 ${
                    injectionData.overall_risk === 'high' ? 'text-red-500' :
                    injectionData.overall_risk === 'medium' ? 'text-yellow-500' :
                    'text-green-500'
                  }`} />
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)}>
        <TabsList>
          <TabsTrigger value="timeline">
            <Calendar className="h-4 w-4 mr-2" />
            Timeline
          </TabsTrigger>
          <TabsTrigger value="injections">
            <AlertTriangle className="h-4 w-4 mr-2" />
            Injections
          </TabsTrigger>
          <TabsTrigger value="compare">
            <GitCompare className="h-4 w-4 mr-2" />
            Compare
          </TabsTrigger>
        </TabsList>

        {/* Timeline Tab */}
        {activeTab === 'timeline' && (
          <div className="space-y-6 mt-6">
            {timelineData && timelineData.timeline && timelineData.timeline.length > 0 ? (
              <>
                {/* Timeline Chart */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle>AI Probability Over Time</CardTitle>
                        <CardDescription>Track how AI probability has changed across versions</CardDescription>
                      </div>
                      <Button variant="outline" onClick={exportTimelineData}>
                        <Download className="h-4 w-4 mr-2" />
                        Export
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {/* Simple SVG Line Chart */}
                    <div className="relative h-64 w-full">
                      <svg className="w-full h-full" viewBox="0 0 600 200" preserveAspectRatio="none">
                        {/* Grid lines */}
                        {[0, 0.25, 0.5, 0.75, 1].map((y, i) => (
                          <line
                            key={i}
                            x1="0" y1={200 - y * 200}
                            x2="600" y2={200 - y * 200}
                            stroke="currentColor"
                            strokeWidth="1"
                            className="text-gray-200 dark:text-gray-700"
                          />
                        ))}

                        {/* Timeline line */}
                        <polyline
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="3"
                          className="text-primary-500"
                          points={timelineData.timeline.map((point, i) => {
                            const x = (i / (timelineData.timeline.length - 1 || 1)) * 600;
                            const y = 200 - point.avg_ai_prob * 200;
                            return `${x},${y}`;
                          }).join(' ')}
                        />

                        {/* Data points */}
                        {timelineData.timeline.map((point, i) => {
                          const x = (i / (timelineData.timeline.length - 1 || 1)) * 600;
                          const y = 200 - point.avg_ai_prob * 200;
                          return (
                            <g key={i}>
                              <circle
                                cx={x}
                                cy={y}
                                r="6"
                                fill={getColorForProbability(point.avg_ai_prob)}
                                className="cursor-pointer hover:r-8 transition-all"
                                onClick={() => {
                                  // Could show tooltip with version details
                                }}
                              />
                              <text
                                x={x}
                                y={y - 10}
                                textAnchor="middle"
                                className="text-xs fill-gray-600 dark:fill-gray-400"
                              >
                                v{point.version_number}
                              </text>
                            </g>
                          );
                        })}
                      </svg>

                      {/* Legend */}
                      <div className="flex items-center justify-center gap-6 mt-4 text-sm">
                        <div className="flex items-center gap-2">
                          <div
                            className="w-4 h-4 rounded"
                            style={{ backgroundColor: getColorForProbability(0) }}
                          />
                          <span className="text-gray-600 dark:text-gray-400">Human (0%)</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div
                            className="w-4 h-4 rounded"
                            style={{ backgroundColor: getColorForProbability(0.5) }}
                          />
                          <span className="text-gray-600 dark:text-gray-400">Mixed (50%)</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div
                            className="w-4 h-4 rounded"
                            style={{ backgroundColor: getColorForProbability(1) }}
                          />
                          <span className="text-gray-600 dark:text-gray-400">AI (100%)</span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Timeline Table */}
                <Card>
                  <CardHeader>
                    <CardTitle>Version Details</CardTitle>
                    <CardDescription>Detailed statistics for each version</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-gray-200 dark:border-gray-700">
                            <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 dark:text-gray-400">Version</th>
                            <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 dark:text-gray-400">Date</th>
                            <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 dark:text-gray-400">Words</th>
                            <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 dark:text-gray-400">Avg AI %</th>
                            <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 dark:text-gray-400">Range</th>
                            <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 dark:text-gray-400">High/Med/Low</th>
                          </tr>
                        </thead>
                        <tbody>
                          {timelineData.timeline.map((point) => (
                            <tr key={point.version_id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800">
                              <td className="py-3 px-4">
                                <Badge variant="outline">v{point.version_number}</Badge>
                              </td>
                              <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                                {formatDate(point.timestamp)}
                              </td>
                              <td className="py-3 px-4 text-sm text-gray-900 dark:text-gray-100">
                                {point.word_count}
                              </td>
                              <td className="py-3 px-4">
                                <div className="flex items-center gap-2">
                                  <div
                                    className="w-12 h-2 rounded"
                                    style={{ backgroundColor: getColorForProbability(point.avg_ai_prob) }}
                                  />
                                  <span className="text-sm font-medium">{(point.avg_ai_prob * 100).toFixed(1)}%</span>
                                </div>
                              </td>
                              <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                                {(point.min_ai_prob * 100).toFixed(0)}% - {(point.max_ai_prob * 100).toFixed(0)}%
                              </td>
                              <td className="py-3 px-4 text-sm">
                                <span className="text-red-500">{point.high_confidence_count}</span>
                                {' / '}
                                <span className="text-yellow-500">{point.medium_confidence_count}</span>
                                {' / '}
                                <span className="text-green-500">{point.low_confidence_count}</span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card>
                <CardContent className="text-center py-12">
                  <Info className="h-12 w-12 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-600 dark:text-gray-400">
                    No version history available for this document.
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                    Analyze this document multiple times to build a version history.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Injections Tab */}
        {activeTab === 'injections' && (
          <div className="space-y-6 mt-6">
            {injectionData && injectionData.total_injections > 0 ? (
              <>
                {/* Injection Summary */}
                <Card>
                  <CardHeader>
                    <CardTitle>Injection Summary</CardTitle>
                    <CardDescription>Overview of detected AI injections</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
                        <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                          {injectionData.severity_breakdown.high || 0}
                        </p>
                        <p className="text-sm text-red-600 dark:text-red-400">High Severity</p>
                      </div>
                      <div className="text-center p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                        <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                          {injectionData.severity_breakdown.medium || 0}
                        </p>
                        <p className="text-sm text-yellow-600 dark:text-yellow-400">Medium Severity</p>
                      </div>
                      <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                        <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                          {injectionData.severity_breakdown.low || 0}
                        </p>
                        <p className="text-sm text-green-600 dark:text-green-400">Low Severity</p>
                      </div>
                      <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                        <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                          {injectionData.injection_score.toFixed(2)}
                        </p>
                        <p className="text-sm text-blue-600 dark:text-blue-400">Injection Score</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Injection Events */}
                <Card>
                  <CardHeader>
                    <CardTitle>Detected Injection Events</CardTitle>
                    <CardDescription>Suspicious AI-generated content added between versions</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {injectionData.injection_events.map((event, idx) => (
                        <div
                          key={idx}
                          className={cn(
                            'p-4 rounded-lg border-2',
                            event.severity === 'high' && 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/10',
                            event.severity === 'medium' && 'border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/10',
                            event.severity === 'low' && 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/10'
                          )}
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Badge variant={getSeverityVariant(event.severity)}>
                                {event.severity.toUpperCase()}
                              </Badge>
                              <Badge variant="outline">
                                {event.type === 'addition' ? 'Addition' : 'Modification'}
                              </Badge>
                              <span className="text-sm text-gray-600 dark:text-gray-400">
                                Version {event.version}
                              </span>
                            </div>
                            <div className="flex items-center gap-1">
                              <span className="text-lg font-bold">
                                {(event.ai_probability * 100).toFixed(0)}%
                              </span>
                              <span className="text-sm text-gray-500">AI</span>
                            </div>
                          </div>
                          <p className="text-sm text-gray-700 dark:text-gray-300 italic mb-2">
                            "{event.text}"
                          </p>
                          {event.delta_ai !== undefined && (
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              AI probability change: {event.delta_ai > 0 ? '+' : ''}{(event.delta_ai * 100).toFixed(1)}%
                            </div>
                          )}
                          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            Position: {event.position} • {formatDate(event.timestamp)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Mixed Authorship Indicators */}
                {injectionData.mixed_authorship_indicators.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Mixed Authorship Indicators</CardTitle>
                      <CardDescription>Patterns suggesting mixed human-AI authorship</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {injectionData.mixed_authorship_indicators.map((indicator, idx) => (
                          <div
                            key={idx}
                            className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                          >
                            <div className={cn(
                              'p-2 rounded-full',
                              indicator.severity === 'high' && 'bg-red-100 dark:bg-red-900/30',
                              indicator.severity === 'medium' && 'bg-yellow-100 dark:bg-yellow-900/30',
                              indicator.severity === 'low' && 'bg-green-100 dark:bg-green-900/30'
                            )}>
                              <Info className={cn(
                                'h-4 w-4',
                                indicator.severity === 'high' && 'text-red-600 dark:text-red-400',
                                indicator.severity === 'medium' && 'text-yellow-600 dark:text-yellow-400',
                                indicator.severity === 'low' && 'text-green-600 dark:text-green-400'
                              )} />
                            </div>
                            <div className="flex-1">
                              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                {indicator.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                              </p>
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                {indicator.description}
                              </p>
                            </div>
                            <Badge variant={getSeverityVariant(indicator.severity)} size="sm">
                              {indicator.severity}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </>
            ) : (
              <Card>
                <CardContent className="text-center py-12">
                  <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                  <p className="text-gray-600 dark:text-gray-400">
                    No AI injection events detected.
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                    This document shows no signs of AI-generated content being added between versions.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Compare Tab */}
        {activeTab === 'compare' && (
          <div className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Version Comparison</CardTitle>
                <CardDescription>Select two versions to compare</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4 mb-6">
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Version A
                    </label>
                    <select
                      value={versionA}
                      onChange={(e) => setVersionA(parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                    >
                      {timelineData?.timeline.map((v) => (
                        <option key={v.version_id} value={v.version_number}>
                          Version {v.version_number} ({formatDate(v.timestamp)})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Version B
                    </label>
                    <select
                      value={versionB}
                      onChange={(e) => setVersionB(parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                    >
                      {timelineData?.timeline.map((v) => (
                        <option key={v.version_id} value={v.version_number}>
                          Version {v.version_number} ({formatDate(v.timestamp)})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-end">
                    <Button onClick={loadComparison} disabled={versionA === versionB}>
                      <GitCompare className="h-4 w-4 mr-2" />
                      Compare
                    </Button>
                  </div>
                </div>

                {comparisonData && (
                  <div className="space-y-4">
                    {/* Similarity Score */}
                    <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Similarity Score
                        </span>
                        <span className="text-lg font-bold text-gray-900 dark:text-gray-100">
                          {(comparisonData.similarity_score * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary-500 transition-all"
                          style={{ width: `${comparisonData.similarity_score * 100}%` }}
                        />
                      </div>
                    </div>

                    {/* Comparison Results */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {/* Added Sections */}
                      <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                        <div className="flex items-center gap-2 mb-3">
                          <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
                          <h3 className="font-medium text-gray-900 dark:text-gray-100">Added</h3>
                          <Badge variant="success" size="sm">{comparisonData.added_sections.length}</Badge>
                        </div>
                        <div className="space-y-2 max-h-60 overflow-y-auto">
                          {comparisonData.added_sections.slice(0, 5).map((section, idx) => (
                            <div key={idx} className="text-sm">
                              <p className="text-gray-700 dark:text-gray-300 line-clamp-2">
                                "{section.text}"
                              </p>
                              {section.ai_probability !== undefined && (
                                <div className="flex items-center gap-1 mt-1">
                                  <div
                                    className="w-8 h-1 rounded"
                                    style={{ backgroundColor: getColorForProbability(section.ai_probability) }}
                                  />
                                  <span className="text-xs text-gray-500">
                                    {(section.ai_probability * 100).toFixed(0)}% AI
                                  </span>
                                </div>
                              )}
                            </div>
                          ))}
                          {comparisonData.added_sections.length > 5 && (
                            <p className="text-xs text-gray-500">
                              +{comparisonData.added_sections.length - 5} more
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Removed Sections */}
                      <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
                        <div className="flex items-center gap-2 mb-3">
                          <XCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
                          <h3 className="font-medium text-gray-900 dark:text-gray-100">Removed</h3>
                          <Badge variant="error" size="sm">{comparisonData.removed_sections.length}</Badge>
                        </div>
                        <div className="space-y-2 max-h-60 overflow-y-auto">
                          {comparisonData.removed_sections.slice(0, 5).map((section, idx) => (
                            <div key={idx} className="text-sm">
                              <p className="text-gray-700 dark:text-gray-300 line-clamp-2">
                                "{section.text}"
                              </p>
                            </div>
                          ))}
                          {comparisonData.removed_sections.length > 5 && (
                            <p className="text-xs text-gray-500">
                              +{comparisonData.removed_sections.length - 5} more
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Modified Sections */}
                      <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                        <div className="flex items-center gap-2 mb-3">
                          <Activity className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
                          <h3 className="font-medium text-gray-900 dark:text-gray-100">Modified</h3>
                          <Badge variant="warning" size="sm">{comparisonData.modified_sections.length}</Badge>
                        </div>
                        <div className="space-y-2 max-h-60 overflow-y-auto">
                          {comparisonData.modified_sections.slice(0, 5).map((section, idx) => (
                            <div key={idx} className="text-sm">
                              <p className="text-red-600 dark:text-red-400 line-clamp-1">
                                - "{section.old_text}"
                              </p>
                              <p className="text-green-600 dark:text-green-400 line-clamp-1">
                                + "{section.new_text}"
                              </p>
                              {section.delta_ai !== undefined && (
                                <p className="text-xs text-gray-500 mt-1">
                                  AI change: {section.delta_ai > 0 ? '+' : ''}{(section.delta_ai * 100).toFixed(0)}%
                                </p>
                              )}
                            </div>
                          ))}
                          {comparisonData.modified_sections.length > 5 && (
                            <p className="text-xs text-gray-500">
                              +{comparisonData.modified_sections.length - 5} more
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </Tabs>
    </div>
  );
}
