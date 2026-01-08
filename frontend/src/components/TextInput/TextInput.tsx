import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { analysisAPI } from '../../services/api';
import './TextInput.css';

function TextInput() {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleAnalyze = async () => {
    if (!text.trim()) {
      setError('Please enter some text to analyze');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const result = await analysisAPI.analyze(text, 'sentence');
      // Store result in sessionStorage for HeatMap component
      sessionStorage.setItem('analysisResult', JSON.stringify(result));
      navigate('/analysis');
    } catch (err: any) {
      console.error('Analysis error:', err);
      if (err.response) {
        setError(err.response.data?.detail || `Server error: ${err.response.status}`);
      } else if (err.request) {
        setError('Cannot connect to server. Make sure the backend is running.');
      } else {
        setError(err.message || 'Error analyzing text');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setText(content);
    };
    reader.readAsText(file);
  };

  const wordCount = text.split(/\s+/).filter(word => word.length > 0).length;
  const charCount = text.length;

  return (
    <div className="text-input-container">
      <h2>Text Analysis</h2>
      <p className="subtitle">Paste or upload text to analyze for AI vs human writing patterns</p>

      <div className="input-section">
        <div className="textarea-wrapper">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste your text here or upload a file..."
            className="text-input"
            rows={15}
          />
          <div className="text-stats">
            <span>Words: {wordCount}</span>
            <span>Characters: {charCount}</span>
          </div>
        </div>

        <div className="file-upload-section">
          <label htmlFor="file-upload" className="file-upload-label">
            Upload File (txt, docx, pdf)
          </label>
          <input
            type="file"
            id="file-upload"
            accept=".txt,.docx,.pdf"
            onChange={handleFileUpload}
            className="file-input"
          />
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      <button
        onClick={handleAnalyze}
        disabled={loading || !text.trim()}
        className="analyze-btn"
      >
        {loading ? 'Analyzing...' : 'Analyze Text'}
      </button>

      <div className="navigation-links">
        <button onClick={() => navigate('/profile')} className="nav-link-btn">
          Manage Profile & Fingerprint
        </button>
        <button onClick={() => navigate('/rewrite')} className="nav-link-btn">
          Style Rewriting
        </button>
      </div>
    </div>
  );
}

export default TextInput;
