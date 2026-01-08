import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyticsAPI, getErrorMessage } from '../../services/api';
import { useToast } from '../../contexts/ToastContext';
import Card, { CardContent, CardHeader, CardTitle, CardDescription } from '../ui/Card';
import Input from '../ui/Input';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import Spinner from '../ui/Spinner';
import Alert from '../ui/Alert';
import { Search, ChevronLeft, ChevronRight, FileText, Download } from 'lucide-react';

interface AnalysisHistoryItem {
  id: number;
  text_preview: string;
  overall_ai_probability: number;
  word_count: number;
  created_at: string;
}

interface AnalysisHistoryResponse {
  items: AnalysisHistoryItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export default function History() {
  const [history, setHistory] = useState<AnalysisHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [minProbability, setMinProbability] = useState<number | undefined>();
  const [maxProbability, setMaxProbability] = useState<number | undefined>();
  const [currentPage, setCurrentPage] = useState(1);
  const [searchInput, setSearchInput] = useState('');
  const { error: showError } = useToast();
  const navigate = useNavigate();

  useEffect(() => {
    loadHistory();
  }, [currentPage]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const data = await analyticsAPI.getHistory(
        currentPage,
        20,
        search || undefined,
        minProbability,
        maxProbability
      );
      setHistory(data);
    } catch (err: any) {
      console.error('History error:', err);
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setSearch(searchInput);
    setCurrentPage(1);
    loadHistory();
  };

  const handleFilter = () => {
    setCurrentPage(1);
    loadHistory();
  };

  const handleClearFilters = () => {
    setSearch('');
    setSearchInput('');
    setMinProbability(undefined);
    setMaxProbability(undefined);
    setCurrentPage(1);
    setTimeout(() => loadHistory(), 100);
  };

  const getProbabilityBadge = (probability: number) => {
    if (probability > 0.7) {
      return <Badge variant="error">High ({Math.round(probability * 100)}%)</Badge>;
    } else if (probability > 0.4) {
      return <Badge variant="warning">Medium ({Math.round(probability * 100)}%)</Badge>;
    } else {
      return <Badge variant="success">Low ({Math.round(probability * 100)}%)</Badge>;
    }
  };

  const handleViewDetails = (id: number) => {
    // Navigate to analysis details (would need to implement this)
    navigate(`/analysis?id=${id}`);
  };

  const handleExport = async (item: AnalysisHistoryItem) => {
    try {
      // In a full implementation, this would fetch the full analysis and export it
      const dataStr = JSON.stringify(item, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `analysis-${item.id}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      showError('Failed to export analysis');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Analysis History</h1>
        <p className="text-gray-600 dark:text-gray-400">View and manage your past analyses</p>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>Search and filter your analysis history</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-2">
              <div className="flex gap-2">
                <Input
                  placeholder="Search text content..."
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  className="flex-1"
                />
                <Button onClick={handleSearch}>
                  <Search className="h-4 w-4 mr-2" />
                  Search
                </Button>
              </div>
            </div>
            <Input
              type="number"
              placeholder="Min AI %"
              min="0"
              max="100"
              value={minProbability !== undefined ? minProbability * 100 : ''}
              onChange={(e) => setMinProbability(e.target.value ? parseFloat(e.target.value) / 100 : undefined)}
            />
            <Input
              type="number"
              placeholder="Max AI %"
              min="0"
              max="100"
              value={maxProbability !== undefined ? maxProbability * 100 : ''}
              onChange={(e) => setMaxProbability(e.target.value ? parseFloat(e.target.value) / 100 : undefined)}
            />
          </div>
          <div className="flex gap-2 mt-4">
            <Button variant="outline" onClick={handleFilter}>
              Apply Filters
            </Button>
            <Button variant="ghost" onClick={handleClearFilters}>
              Clear All
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* History Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            Analyses
            {history && (
              <span className="text-sm font-normal text-gray-500 dark:text-gray-400 ml-2">
                ({history.total} total)
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : !history || history.items.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
              <p className="text-gray-500 dark:text-gray-400">No analyses found</p>
              <Button
                variant="primary"
                className="mt-4"
                onClick={() => navigate('/analyze')}
              >
                Start Your First Analysis
              </Button>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                        Preview
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                        AI Probability
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                        Word Count
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                        Date
                      </th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.items.map((item) => (
                      <tr
                        key={item.id}
                        className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                      >
                        <td className="py-3 px-4">
                          <p className="text-sm text-gray-900 dark:text-gray-100 max-w-md truncate">
                            {item.text_preview}
                          </p>
                        </td>
                        <td className="py-3 px-4">
                          {getProbabilityBadge(item.overall_ai_probability)}
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                          {item.word_count.toLocaleString()}
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                          {new Date(item.created_at).toLocaleDateString()}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleViewDetails(item.id)}
                            >
                              View
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleExport(item)}
                            >
                              <Download className="h-4 w-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {history.total_pages > 1 && (
                <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    Page {history.page} of {history.total_pages}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                    >
                      <ChevronLeft className="h-4 w-4" />
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((p) => Math.min(history.total_pages, p + 1))}
                      disabled={currentPage === history.total_pages}
                    >
                      Next
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
