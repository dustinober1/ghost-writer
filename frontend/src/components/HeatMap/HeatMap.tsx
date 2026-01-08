import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './HeatMap.css';

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

function HeatMap() {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [granularity, setGranularity] = useState<'sentence' | 'paragraph'>('sentence');
  const navigate = useNavigate();

  useEffect(() => {
    const stored = sessionStorage.getItem('analysisResult');
    if (stored) {
      try {
        const result = JSON.parse(stored);
        setAnalysisResult(result);
      } catch (e) {
        console.error('Error parsing analysis result:', e);
        navigate('/');
      }
    } else {
      navigate('/');
    }
  }, [navigate]);

  const getColorForProbability = (probability: number): string => {
    // Red for AI-like (high probability), green for human-like (low probability)
    const red = Math.min(255, Math.round(probability * 255));
    const green = Math.min(255, Math.round((1 - probability) * 255));
    const blue = 50;
    return `rgb(${red}, ${green}, ${blue})`;
  };

  const getTextColor = (probability: number): string => {
    // Use white text for high contrast
    return probability > 0.5 ? '#ffffff' : '#000000';
  };

  if (!analysisResult) {
    return <div>Loading...</div>;
  }

  const { heat_map_data, overall_ai_probability } = analysisResult;

  return (
    <div className="heatmap-container">
      <div className="heatmap-header">
        <h2>Analysis Results</h2>
        <button onClick={() => navigate('/')} className="back-btn">
          ← Back to Input
        </button>
      </div>

      <div className="summary-section">
        <div className="summary-card">
          <h3>Overall AI Probability</h3>
          <div className="probability-display">
            <span className="probability-value">
              {(overall_ai_probability * 100).toFixed(1)}%
            </span>
            <div className="probability-bar">
              <div
                className="probability-fill"
                style={{
                  width: `${overall_ai_probability * 100}%`,
                  backgroundColor: getColorForProbability(overall_ai_probability),
                }}
              />
            </div>
          </div>
          <p className="probability-interpretation">
            {overall_ai_probability > 0.7
              ? 'High likelihood of AI-generated content'
              : overall_ai_probability > 0.4
              ? 'Mixed - some AI-like patterns detected'
              : 'Low likelihood - appears more human-written'}
          </p>
        </div>
      </div>

      <div className="granularity-selector">
        <label>
          <input
            type="radio"
            value="sentence"
            checked={granularity === 'sentence'}
            onChange={(e) => setGranularity(e.target.value as 'sentence' | 'paragraph')}
          />
          Sentence-level
        </label>
        <label>
          <input
            type="radio"
            value="paragraph"
            checked={granularity === 'paragraph'}
            onChange={(e) => setGranularity(e.target.value as 'sentence' | 'paragraph')}
          />
          Paragraph-level
        </label>
      </div>

      <div className="heatmap-legend">
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: 'rgb(0, 255, 50)' }} />
          <span>Human-like (0%)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: 'rgb(128, 128, 50)' }} />
          <span>Mixed (50%)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: 'rgb(255, 0, 50)' }} />
          <span>AI-like (100%)</span>
        </div>
      </div>

      <div className="heatmap-text">
        {heat_map_data.segments.map((segment, index) => {
          const bgColor = getColorForProbability(segment.ai_probability);
          const textColor = getTextColor(segment.ai_probability);

          return (
            <span
              key={index}
              className="text-segment"
              style={{
                backgroundColor: bgColor,
                color: textColor,
              }}
              title={`AI Probability: ${(segment.ai_probability * 100).toFixed(1)}%`}
            >
              {segment.text}
            </span>
          );
        })}
      </div>

      <div className="export-section">
        <button
          onClick={() => {
            const dataStr = JSON.stringify(analysisResult, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `analysis-${analysisResult.analysis_id}.json`;
            link.click();
          }}
          className="export-btn"
        >
          Export Analysis Results
        </button>
      </div>
    </div>
  );
}

export default HeatMap;
