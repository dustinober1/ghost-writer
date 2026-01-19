import { useState, useEffect } from 'react';
import { driftAPI, DriftAlert, DriftSeverity, FeatureChange, getErrorMessage } from '../../services/api';
import { useToast } from '../../contexts/ToastContext';
import Card, { CardContent, CardHeader, CardTitle, CardDescription } from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import Alert from '../ui/Alert';
import { AlertTriangle, Warning, CheckCircle, Clock, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '../../utils/cn';

// Human-readable feature names
const FEATURE_NAMES: Record<string, string> = {
  avg_sentence_length: 'Avg Sentence Length',
  type_token_ratio: 'Type-Token Ratio',
  hapax_legomena_ratio: 'Unique Words Ratio',
  readability_score: 'Readability Score',
  burstiness: 'Burstiness',
  perplexity_mean: 'Perplexity (Mean)',
  perplexity_std: 'Perplexity (Std Dev)',
  pos_noun_ratio: 'Noun Ratio',
  pos_verb_ratio: 'Verb Ratio',
  pos_adj_ratio: 'Adjective Ratio',
  pos_adv_ratio: 'Adverb Ratio',
  pronoun_ratio: 'Pronoun Ratio',
  conjunction_ratio: 'Conjunction Ratio',
  preposition_ratio: 'Preposition Ratio',
  article_ratio: 'Article Ratio',
  punctuation_comma_ratio: 'Comma Usage',
  punctuation_period_ratio: 'Period Usage',
  punctuation_semicolon_ratio: 'Semicolon Usage',
  punctuation_quote_ratio: 'Quote Usage',
  punctuation_exclamation_ratio: 'Exclamation Usage',
  punctuation_question_ratio: 'Question Mark Usage',
  contraction_ratio: 'Contraction Usage',
  passive_voice_ratio: 'Passive Voice',
  sentence_complexity: 'Sentence Complexity',
  coherence_local: 'Local Coherence',
  coherence_global: 'Global Coherence',
  vocabulary_richness: 'Vocabulary Richness',
  avg_word_length: 'Avg Word Length',
  frequency_word_ratio: 'Common Word Ratio'
};

interface DriftAlertsProps {
  onAlertAcknowledged?: () => void;
}

export default function DriftAlerts({ onAlertAcknowledged }: DriftAlertsProps) {
  const [alerts, setAlerts] = useState<DriftAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAcknowledged, setShowAcknowledged] = useState(false);
  const [acknowledging, setAcknowledging] = useState<Set<number>>(new Set());
  const [expandedAlerts, setExpandedAlerts] = useState<Set<number>>(new Set());
  const { success, error: showError } = useToast();

  useEffect(() => {
    loadAlerts();
  }, [showAcknowledged]);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const data = await driftAPI.getAlerts(showAcknowledged);
      setAlerts(data.alerts);
    } catch (err: any) {
      console.error('Error loading drift alerts:', err);
      // Don't show error toast on initial load - alerts may not exist yet
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async (alertId: number, updateBaseline: boolean = false) => {
    try {
      setAcknowledging(prev => new Set(prev).add(alertId));
      await driftAPI.acknowledgeAlert(alertId, updateBaseline);

      // Remove from local list
      setAlerts(prev => prev.filter(a => a.id !== alertId));

      success(updateBaseline
        ? 'Alert acknowledged and baseline updated'
        : 'Alert acknowledged');

      if (onAlertAcknowledged) {
        onAlertAcknowledged();
      }
    } catch (err: any) {
      console.error('Error acknowledging alert:', err);
      showError(getErrorMessage(err));
    } finally {
      setAcknowledging(prev => {
        const next = new Set(prev);
        next.delete(alertId);
        return next;
      });
    }
  };

  const toggleExpanded = (alertId: number) => {
    setExpandedAlerts(prev => {
      const next = new Set(prev);
      if (next.has(alertId)) {
        next.delete(alertId);
      } else {
        next.add(alertId);
      }
      return next;
    });
  };

  const getSeverityVariant = (severity: DriftSeverity) => {
    switch (severity) {
      case 'alert':
        return 'error';
      case 'warning':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getSeverityIcon = (severity: DriftSeverity) => {
    switch (severity) {
      case 'alert':
        return <AlertTriangle className="h-5 w-5" />;
      case 'warning':
        return <Warning className="h-5 w-5" />;
      default:
        return null;
    }
  };

  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`;
    return date.toLocaleDateString();
  };

  const getDeviationColor = (deviation: number) => {
    if (Math.abs(deviation) >= 3.0) return 'text-error-600 dark:text-error-400';
    if (Math.abs(deviation) >= 2.0) return 'text-warning-600 dark:text-warning-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  const renderConfidenceInterval = (alert: DriftAlert) => {
    const baseline = alert.baseline_similarity;
    const current = alert.similarity_score;
    const zScore = alert.z_score;

    // Calculate the range based on z-score
    const range = Math.abs(zScore) * 0.05; // Approximate std dev
    const ciLower = Math.max(0, baseline - range);
    const ciUpper = Math.min(1, baseline + range);

    // Calculate percentage position for the bar
    const barWidth = 100;
    const baselinePos = baseline * barWidth;
    const currentPos = current * barWidth;

    return (
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400">
          <span>Baseline: {(baseline * 100).toFixed(1)}%</span>
          <span>Current: {(current * 100).toFixed(1)}%</span>
        </div>
        <div className="relative h-6 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          {/* Baseline marker */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-success-500"
            style={{ left: `${baselinePos}%` }}
          />
          {/* Current value marker */}
          <div
            className={cn(
              "absolute top-0 bottom-0 w-2",
              Math.abs(zScore) >= 3.0 ? "bg-error-500" : "bg-warning-500"
            )}
            style={{ left: `${currentPos}%`, transform: 'translateX(-50%)' }}
          />
          {/* Confidence interval range */}
          <div
            className="absolute top-1 bottom-1 bg-gray-400 dark:bg-gray-600 opacity-30 rounded"
            style={{
              left: `${ciLower * barWidth}%`,
              width: `${(ciUpper - ciLower) * barWidth}%`
            }}
          />
        </div>
        <div className="text-center text-xs text-gray-500 dark:text-gray-500">
          {zScore >= 0 ? '+' : ''}{zScore.toFixed(2)} standard deviations from baseline
        </div>
      </div>
    );
  };

  const renderFeatureChanges = (features: FeatureChange[]) => {
    const topFeatures = features.slice(0, 5);

    return (
      <div className="mt-4">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Most Changed Features
        </h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-2 px-3 text-gray-600 dark:text-gray-400 font-medium">
                  Feature
                </th>
                <th className="text-right py-2 px-3 text-gray-600 dark:text-gray-400 font-medium">
                  Baseline
                </th>
                <th className="text-right py-2 px-3 text-gray-600 dark:text-gray-400 font-medium">
                  Current
                </th>
                <th className="text-right py-2 px-3 text-gray-600 dark:text-gray-400 font-medium">
                  Deviation
                </th>
              </tr>
            </thead>
            <tbody>
              {topFeatures.map((feature, idx) => (
                <tr
                  key={idx}
                  className="border-b border-gray-100 dark:border-gray-800 last:border-0"
                >
                  <td className="py-2 px-3 text-gray-900 dark:text-gray-100">
                    {FEATURE_NAMES[feature.feature] || feature.feature}
                  </td>
                  <td className="py-2 px-3 text-right text-gray-600 dark:text-gray-400">
                    {feature.baseline_value.toFixed(3)}
                  </td>
                  <td className="py-2 px-3 text-right text-gray-900 dark:text-gray-100">
                    {feature.current_value.toFixed(3)}
                  </td>
                  <td className={cn(
                    "py-2 px-3 text-right font-medium",
                    getDeviationColor(feature.normalized_deviation)
                  )}>
                    {feature.normalized_deviation >= 0 ? '+' : ''}
                    {feature.normalized_deviation.toFixed(2)}σ
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderAlertCard = (alert: DriftAlert) => {
    const isExpanded = expandedAlerts.has(alert.id);
    const isLoading = acknowledging.has(alert.id);

    return (
      <Card key={alert.id} className="mb-4">
        <CardContent className="p-4">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2">
              <Badge variant={getSeverityVariant(alert.severity)} className="flex items-center gap-1">
                {getSeverityIcon(alert.severity)}
                {alert.severity.toUpperCase()}
              </Badge>
              <span className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {formatRelativeTime(alert.created_at)}
              </span>
            </div>
            <button
              onClick={() => toggleExpanded(alert.id)}
              className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
            >
              {isExpanded ? (
                <ChevronUp className="h-4 w-4 text-gray-500" />
              ) : (
                <ChevronDown className="h-4 w-4 text-gray-500" />
              )}
            </button>
          </div>

          <div className="space-y-3">
            {/* Similarity comparison */}
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {(alert.similarity_score * 100).toFixed(0)}%
              </span>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                similarity vs baseline {(alert.baseline_similarity * 100).toFixed(0)}%
              </span>
            </div>

            {/* Confidence interval visualization */}
            {renderConfidenceInterval(alert)}

            {/* Expanded content */}
            {isExpanded && (
              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                {/* Text preview */}
                {alert.text_preview && (
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Triggered by:
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400 italic">
                      "{alert.text_preview}"
                    </p>
                  </div>
                )}

                {/* Changed features */}
                {alert.changed_features && alert.changed_features.length > 0 && (
                  renderFeatureChanges(alert.changed_features)
                )}
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center gap-3 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleAcknowledge(alert.id, false)}
                disabled={isLoading}
                isLoading={isLoading}
              >
                <CheckCircle className="h-4 w-4 mr-1" />
                Acknowledge
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleAcknowledge(alert.id, true)}
                disabled={isLoading}
              >
                Acknowledge & Update Baseline
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Style Drift Alerts
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Notifications when your writing style drifts from your baseline
          </p>
        </div>
      </div>

      {/* Show acknowledged toggle */}
      <div className="flex items-center justify-between">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showAcknowledged}
            onChange={(e) => setShowAcknowledged(e.target.checked)}
            className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
          />
          <span className="text-sm text-gray-700 dark:text-gray-300">
            Show acknowledged alerts
          </span>
        </label>
        <Button
          variant="outline"
          size="sm"
          onClick={loadAlerts}
          disabled={loading}
        >
          Refresh
        </Button>
      </div>

      {/* Loading state */}
      {loading && (
        <Card>
          <CardContent className="p-8 text-center text-gray-500 dark:text-gray-400">
            Loading alerts...
          </CardContent>
        </Card>
      )}

      {/* Empty state */}
      {!loading && alerts.length === 0 && (
        <Card>
          <CardContent className="p-8 text-center">
            <CheckCircle className="h-12 w-12 text-success-500 mx-auto mb-3" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-1">
              No drift alerts detected
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Your writing style is consistent with your baseline fingerprint.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Alert severity info */}
      {!loading && alerts.length > 0 && (
        <Alert variant="info" className="mb-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 flex-shrink-0" />
            <div className="text-sm">
              <span className="font-medium">Alert levels:</span>{' '}
              <span className="text-error-600 dark:text-error-400 font-medium">ALERT</span> = 3+ standard deviations,
              <span className="text-warning-600 dark:text-warning-400 font-medium"> WARNING</span> = 2+ standard deviations
            </div>
          </div>
        </Alert>
      )}

      {/* Alerts list */}
      {!loading && alerts.map(renderAlertCard)}
    </div>
  );
}
