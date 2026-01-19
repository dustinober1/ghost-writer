import { useState, useEffect, useCallback } from 'react';
import { fingerprintAPI, getErrorMessage, FingerprintProfile, FingerprintComparisonResponse } from '../../services/api';
import { useToast } from '../../contexts/ToastContext';
import Card, { CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import Alert from '../ui/Alert';
import Textarea from '../ui/Textarea';
import { Fingerprint, Target, Sparkles, CheckCircle2, Info, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '../../utils/cn';

interface FeatureDisplay {
  name: string;
  displayName: string;
  textValue: number;
  fingerprintValue: number;
  deviation: number;
  isHigher: boolean;
}

// Feature name mapping for display
const FEATURE_NAMES: Record<string, string> = {
  burstiness: 'Burstiness',
  perplexity: 'Perplexity',
  rare_word_ratio: 'Rare Word Ratio',
  unique_word_ratio: 'Unique Word Ratio',
  noun_ratio: 'Noun Ratio',
  verb_ratio: 'Verb Ratio',
  adjective_ratio: 'Adjective Ratio',
  adverb_ratio: 'Adverb Ratio',
  avg_word_length: 'Avg Word Length',
  sentence_complexity: 'Sentence Complexity',
  word_count: 'Word Count',
  sentence_count: 'Sentence Count',
  avg_sentence_length: 'Avg Sentence Length',
  bigram_diversity: 'Bigram Diversity',
  trigram_diversity: 'Trigram Diversity',
  bigram_repetition: 'Bigram Repetition',
  trigram_repetition: 'Trigram Repetition',
  lexical_overlap: 'Lexical Overlap',
  topic_consistency: 'Topic Consistency',
  transition_smoothness: 'Transition Smoothness',
  comma_ratio: 'Comma Ratio',
  semicolon_ratio: 'Semicolon Ratio',
  question_ratio: 'Question Ratio',
  exclamation_ratio: 'Exclamation Ratio',
  parentheses_ratio: 'Parentheses Ratio',
  flesch_reading_ease: 'Flesch Reading Ease',
  flesch_kincaid_grade: 'Flesch-Kincaid Grade',
};

export default function FingerprintProfile() {
  const [profile, setProfile] = useState<FingerprintProfile | null>(null);
  const [comparisonText, setComparisonText] = useState('');
  const [comparisonResult, setComparisonResult] = useState<FingerprintComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [comparing, setComparing] = useState(false);
  const { success, error: showError } = useToast();

  const loadProfile = useCallback(async () => {
    try {
      const data = await fingerprintAPI.getProfile();
      setProfile(data);
    } catch (err: any) {
      console.error('Load profile error:', err);
      // Silent fail if no fingerprint
      if (err.response?.status !== 404) {
        showError(getErrorMessage(err));
      }
    }
  }, [showError]);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  const handleCompare = async () => {
    if (!comparisonText.trim() || comparisonText.length < 10) {
      showError('Please enter at least 10 characters to compare');
      return;
    }

    setComparing(true);
    try {
      const result = await fingerprintAPI.compare(comparisonText, true);
      setComparisonResult(result);
      success('Comparison complete');
    } catch (err: any) {
      console.error('Compare error:', err);
      showError(getErrorMessage(err));
    } finally {
      setComparing(false);
    }
  };

  const getMatchLevelColor = (level: string) => {
    switch (level) {
      case 'HIGH':
        return 'success';
      case 'MEDIUM':
        return 'warning';
      case 'LOW':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const getSimilarityColor = (similarity: number) => {
    if (similarity >= 0.85) return 'text-success-600 dark:text-success-400';
    if (similarity >= 0.70) return 'text-warning-600 dark:text-warning-400';
    return 'text-destructive-600 dark:text-destructive-400';
  };

  const getSimilarityBgColor = (similarity: number) => {
    if (similarity >= 0.85) return 'bg-success-100 dark:bg-success-900/20';
    if (similarity >= 0.70) return 'bg-warning-100 dark:bg-warning-900/20';
    return 'bg-destructive-100 dark:bg-destructive-900/20';
  };

  const formatFeatureDeviations = (deviations: FingerprintComparisonResponse['feature_deviations']): FeatureDisplay[] => {
    return deviations.map(d => ({
      name: d.feature,
      displayName: FEATURE_NAMES[d.feature] || d.feature,
      textValue: d.text_value,
      fingerprintValue: d.fingerprint_value,
      deviation: d.deviation,
      isHigher: d.text_value > d.fingerprint_value,
    }));
  };

  if (!profile?.has_fingerprint) {
    return (
      <Card>
        <CardContent className="py-12">
          <div className="text-center">
            <Fingerprint className="h-16 w-16 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              No Fingerprint Found
            </h3>
            <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
              You need to generate a fingerprint before using this feature. Go to the Basic Fingerprint tab to create one.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Fingerprint Profile Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary-100 dark:bg-primary-900/20 rounded-lg">
                <Fingerprint className="h-6 w-6 text-primary-600 dark:text-primary-400" />
              </div>
              <div>
                <CardTitle>Fingerprint Profile</CardTitle>
                <CardDescription>
                  Your writing style fingerprint with statistical metadata
                </CardDescription>
              </div>
            </div>
            {profile.method && (
              <Badge variant="outline" size="lg">
                {profile.method === 'time_weighted' ? 'Time-Weighted EMA' :
                 profile.method === 'average' ? 'Average' :
                 profile.method === 'source_weighted' ? 'Source-Weighted' :
                 profile.method}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Corpus Size */}
            <div className="space-y-1">
              <p className="text-xs text-gray-600 dark:text-gray-400">Corpus Size</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {profile.corpus_size ?? 'N/A'}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500">samples</p>
            </div>

            {/* Alpha (if available) */}
            {profile.alpha !== undefined && (
              <div className="space-y-1">
                <p className="text-xs text-gray-600 dark:text-gray-400">EMA Alpha</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {profile.alpha.toFixed(2)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-500">smoothing</p>
              </div>
            )}

            {/* Feature Count */}
            <div className="space-y-1">
              <p className="text-xs text-gray-600 dark:text-gray-400">Features</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {profile.feature_count}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500">stylometric</p>
            </div>

            {/* Last Updated */}
            <div className="space-y-1">
              <p className="text-xs text-gray-600 dark:text-gray-400">Last Updated</p>
              <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                {profile.updated_at ? new Date(profile.updated_at).toLocaleDateString() : 'N/A'}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500">
                {profile.created_at && `created ${new Date(profile.created_at).toLocaleDateString()}`}
              </p>
            </div>
          </div>

          {/* Source Distribution */}
          {profile.source_distribution && Object.keys(profile.source_distribution).length > 0 && (
            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">Source Distribution</p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(profile.source_distribution).map(([source, count]) => (
                  <Badge key={source} variant="secondary">
                    {source}: {count}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Similarity Checker */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-info-100 dark:bg-info-900/20 rounded-lg">
              <Target className="h-6 w-6 text-info-600 dark:text-info-400" />
            </div>
            <div>
              <CardTitle>Similarity Checker</CardTitle>
              <CardDescription>
                Compare any text to your fingerprint to see if it matches your writing style
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Input Textarea */}
          <div>
            <label htmlFor="comparison-text" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Text to Compare
            </label>
            <Textarea
              id="comparison-text"
              value={comparisonText}
              onChange={(e) => setComparisonText(e.target.value)}
              placeholder="Paste text here to compare with your fingerprint..."
              className="min-h-[150px]"
              disabled={comparing}
            />
            <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">
              Enter at least 10 characters for comparison
            </p>
          </div>

          {/* Compare Button */}
          <Button
            onClick={handleCompare}
            disabled={comparing || !comparisonText.trim() || comparisonText.length < 10}
            isLoading={comparing}
            className="w-full"
            size="lg"
          >
            <Sparkles className="h-5 w-5 mr-2" />
            Check Similarity
          </Button>

          {/* Results */}
          {comparisonResult && (
            <div className="space-y-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              {/* Similarity Score */}
              <div className={cn(
                'rounded-lg p-6 text-center',
                getSimilarityBgColor(comparisonResult.similarity)
              )}>
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Similarity Score
                </p>
                <p className={cn(
                  'text-5xl font-bold',
                  getSimilarityColor(comparisonResult.similarity)
                )}>
                  {(comparisonResult.similarity * 100).toFixed(1)}%
                </p>
                <div className="flex items-center justify-center gap-2 mt-3">
                  <Badge variant={getMatchLevelColor(comparisonResult.match_level)} size="lg">
                    <CheckCircle2 className="h-4 w-4 mr-1" />
                    {comparisonResult.match_level} Match
                  </Badge>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {comparisonResult.method_used}
                  </span>
                </div>
              </div>

              {/* Confidence Interval */}
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Info className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    95% Confidence Interval
                  </p>
                </div>
                <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {(comparisonResult.confidence_interval.lower * 100).toFixed(1)}% - {(comparisonResult.confidence_interval.upper * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                  We are 95% confident the true similarity lies within this range.
                </p>
              </div>

              {/* Feature Deviations */}
              {comparisonResult.feature_deviations.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    Top Feature Differences
                  </p>
                  <div className="space-y-2">
                    {formatFeatureDeviations(comparisonResult.feature_deviations).map((feature) => (
                      <div
                        key={feature.name}
                        className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                      >
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          <div className={cn(
                            'p-1.5 rounded',
                            feature.isHigher
                              ? 'bg-warning-100 dark:bg-warning-900/20'
                              : 'bg-info-100 dark:bg-info-900/20'
                          )}>
                            {feature.isHigher ? (
                              <TrendingUp className="h-4 w-4 text-warning-600 dark:text-warning-400" />
                            ) : (
                              <TrendingDown className="h-4 w-4 text-info-600 dark:text-info-400" />
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                              {feature.displayName}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-500 truncate">
                              Text: {feature.textValue.toFixed(3)} vs Fingerprint: {feature.fingerprintValue.toFixed(3)}
                            </p>
                          </div>
                        </div>
                        <Badge variant="outline" className="ml-2">
                          Deviation: {feature.deviation.toFixed(3)}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
