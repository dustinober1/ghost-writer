import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { rewriteAPI, getErrorMessage } from '../../services/api';
import './RewriteInterface.css';

function RewriteInterface() {
  const [originalText, setOriginalText] = useState('');
  const [rewrittenText, setRewrittenText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [targetStyle, setTargetStyle] = useState('');
  const navigate = useNavigate();

  const handleRewrite = async () => {
    if (!originalText.trim()) {
      setError('Please enter some text to rewrite');
      return;
    }

    setLoading(true);
    setError('');
    setRewrittenText('');

    try {
      const result = await rewriteAPI.rewrite(
        originalText,
        targetStyle || undefined
      );
      setRewrittenText(result.rewritten_text);
    } catch (err: any) {
      console.error('Rewrite error:', err);
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setOriginalText('');
    setRewrittenText('');
    setTargetStyle('');
    setError('');
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    // Could add a toast notification here
  };

  return (
    <div className="rewrite-container">
      <div className="rewrite-header">
        <h2>Style Rewriting</h2>
        <button onClick={() => navigate('/')} className="back-btn">
          ← Back to Home
        </button>
      </div>

      <p className="subtitle">
        Rewrite AI-generated text to match your personal writing style using your fingerprint.
      </p>

      {error && <div className="error-message">{error}</div>}

      <div className="style-guidance-section">
        <label htmlFor="target-style" className="style-label">
          Target Style (Optional - will use your fingerprint if not provided)
        </label>
        <textarea
          id="target-style"
          value={targetStyle}
          onChange={(e) => setTargetStyle(e.target.value)}
          placeholder="Describe the target writing style, or leave empty to use your fingerprint..."
          className="style-input"
          rows={2}
        />
      </div>

      <div className="input-section">
        <div className="text-panel">
          <div className="panel-header">
            <h3>Original Text (AI-generated)</h3>
            {originalText && (
              <button
                onClick={() => handleCopy(originalText)}
                className="copy-btn"
                title="Copy to clipboard"
              >
                📋 Copy
              </button>
            )}
          </div>
          <textarea
            value={originalText}
            onChange={(e) => setOriginalText(e.target.value)}
            placeholder="Paste AI-generated text here..."
            className="text-input"
            rows={12}
            disabled={loading}
          />
          <div className="text-stats">
            <span>Words: {originalText.split(/\s+/).filter((w) => w.length > 0).length}</span>
            <span>Characters: {originalText.length}</span>
          </div>
        </div>

        <div className="action-section">
          <button
            onClick={handleRewrite}
            disabled={loading || !originalText.trim()}
            className="rewrite-btn"
          >
            {loading ? 'Rewriting...' : '→ Rewrite'}
          </button>
          <button onClick={handleClear} className="clear-btn" disabled={loading}>
            Clear All
          </button>
        </div>

        <div className="text-panel">
          <div className="panel-header">
            <h3>Rewritten Text (Your Style)</h3>
            {rewrittenText && (
              <button
                onClick={() => handleCopy(rewrittenText)}
                className="copy-btn"
                title="Copy to clipboard"
              >
                📋 Copy
              </button>
            )}
          </div>
          <div className="rewritten-output">
            {rewrittenText ? (
              <div className="rewritten-text-content">{rewrittenText}</div>
            ) : (
              <div className="placeholder-text">
                {loading ? 'Rewriting...' : 'Rewritten text will appear here'}
              </div>
            )}
          </div>
          {rewrittenText && (
            <div className="text-stats">
              <span>
                Words: {rewrittenText.split(/\s+/).filter((w) => w.length > 0).length}
              </span>
              <span>Characters: {rewrittenText.length}</span>
            </div>
          )}
        </div>
      </div>

      {originalText && rewrittenText && (
        <div className="comparison-section">
          <h3>Side-by-Side Comparison</h3>
          <div className="comparison-grid">
            <div className="comparison-panel">
              <h4>Original</h4>
              <div className="comparison-text">{originalText}</div>
            </div>
            <div className="comparison-panel">
              <h4>Rewritten</h4>
              <div className="comparison-text rewritten">{rewrittenText}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default RewriteInterface;
