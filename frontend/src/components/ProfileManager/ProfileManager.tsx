import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fingerprintAPI } from '../../services/api';
import './ProfileManager.css';

interface FingerprintStatus {
  has_fingerprint: boolean;
  fingerprint: {
    id: number;
    user_id: number;
    feature_vector: number[];
    model_version: string;
    created_at: string;
    updated_at: string;
  } | null;
  sample_count: number;
}

function ProfileManager() {
  const [status, setStatus] = useState<FingerprintStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [uploadText, setUploadText] = useState('');
  const [fineTuneTexts, setFineTuneTexts] = useState<string[]>(['']);
  const navigate = useNavigate();

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const data = await fingerprintAPI.getStatus();
      setStatus(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error loading fingerprint status');
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await fingerprintAPI.upload(undefined, file);
      setSuccess('File uploaded successfully!');
      await loadStatus();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error uploading file');
    } finally {
      setLoading(false);
    }
  };

  const handleTextUpload = async () => {
    if (!uploadText.trim()) {
      setError('Please enter some text');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await fingerprintAPI.upload(uploadText);
      setSuccess('Text uploaded successfully!');
      setUploadText('');
      await loadStatus();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error uploading text');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateFingerprint = async () => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await fingerprintAPI.generate();
      setSuccess('Fingerprint generated successfully!');
      await loadStatus();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error generating fingerprint');
    } finally {
      setLoading(false);
    }
  };

  const handleFineTune = async () => {
    const validTexts = fineTuneTexts.filter((text) => text.trim());
    if (validTexts.length === 0) {
      setError('Please enter at least one text sample');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await fingerprintAPI.fineTune(validTexts, 0.3);
      setSuccess('Fingerprint fine-tuned successfully!');
      setFineTuneTexts(['']);
      await loadStatus();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error fine-tuning fingerprint');
    } finally {
      setLoading(false);
    }
  };

  const addFineTuneField = () => {
    setFineTuneTexts([...fineTuneTexts, '']);
  };

  const updateFineTuneText = (index: number, value: string) => {
    const newTexts = [...fineTuneTexts];
    newTexts[index] = value;
    setFineTuneTexts(newTexts);
  };

  return (
    <div className="profile-manager-container">
      <div className="profile-header">
        <h2>Profile & Fingerprint Management</h2>
        <button onClick={() => navigate('/')} className="back-btn">
          ← Back to Home
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <div className="status-section">
        <h3>Fingerprint Status</h3>
        {status && (
          <div className="status-card">
            <div className="status-item">
              <span className="status-label">Has Fingerprint:</span>
              <span className={status.has_fingerprint ? 'status-yes' : 'status-no'}>
                {status.has_fingerprint ? 'Yes' : 'No'}
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Writing Samples:</span>
              <span>{status.sample_count}</span>
            </div>
            {status.fingerprint && (
              <div className="status-item">
                <span className="status-label">Model Version:</span>
                <span>{status.fingerprint.model_version}</span>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="upload-section">
        <h3>Upload Writing Samples</h3>
        <p className="section-description">
          Upload your past writing to build your personal fingerprint. The more samples you provide,
          the more accurate your fingerprint will be.
        </p>

        <div className="upload-methods">
          <div className="upload-method">
            <h4>Upload File</h4>
            <label htmlFor="file-upload" className="file-upload-label">
              Choose File (txt, docx, pdf)
            </label>
            <input
              type="file"
              id="file-upload"
              accept=".txt,.docx,.pdf"
              onChange={handleFileUpload}
              className="file-input"
              disabled={loading}
            />
          </div>

          <div className="upload-method">
            <h4>Paste Text</h4>
            <textarea
              value={uploadText}
              onChange={(e) => setUploadText(e.target.value)}
              placeholder="Paste your writing sample here..."
              className="text-upload-input"
              rows={5}
              disabled={loading}
            />
            <button
              onClick={handleTextUpload}
              disabled={loading || !uploadText.trim()}
              className="upload-btn"
            >
              Upload Text
            </button>
          </div>
        </div>
      </div>

      <div className="generate-section">
        <h3>Generate Fingerprint</h3>
        <p className="section-description">
          Generate your fingerprint from uploaded writing samples. You need at least one sample.
        </p>
        <button
          onClick={handleGenerateFingerprint}
          disabled={loading || !status || status.sample_count === 0}
          className="generate-btn"
        >
          {loading ? 'Generating...' : 'Generate Fingerprint'}
        </button>
      </div>

      {status?.has_fingerprint && (
        <div className="finetune-section">
          <h3>Fine-tune Fingerprint</h3>
          <p className="section-description">
            Add more writing samples to improve your fingerprint accuracy.
          </p>
          {fineTuneTexts.map((text, index) => (
            <div key={index} className="finetune-input-group">
              <textarea
                value={text}
                onChange={(e) => updateFineTuneText(index, e.target.value)}
                placeholder="Enter a new writing sample..."
                className="finetune-input"
                rows={3}
                disabled={loading}
              />
            </div>
          ))}
          <div className="finetune-actions">
            <button onClick={addFineTuneField} className="add-field-btn" disabled={loading}>
              + Add Another Sample
            </button>
            <button
              onClick={handleFineTune}
              disabled={loading}
              className="finetune-btn"
            >
              {loading ? 'Fine-tuning...' : 'Fine-tune Fingerprint'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ProfileManager;
