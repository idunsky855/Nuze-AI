
import React, { useState, useEffect } from 'react';
import { getDailySummary, generateDailySummary } from '../api';


const DailySummary = ({ user, generating, setGenerating }) => {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  // local generating state removed, using props
  const [error, setError] = useState(null);

  const loadSummary = async () => {
    try {
      setLoading(true);
      const data = await getDailySummary();
      setSummary(data);
    } catch (err) {
      console.error("Error loading summary:", err);
      setError("Failed to load daily summary.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const data = await generateDailySummary();
      setSummary(data);
    } catch (e) {
      if (e.response && e.response.status === 404) {
        setError("Could not generate summary (no relevant articles found for today).");
      } else {
        setError("Failed to generate summary. Please try again.");
      }
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="summary-loading">
        <div className="spinner"></div>
        <p>Checking for daily brief...</p>
      </div>
    );
  }

  if (summary) {
    return (
      <div className="daily-summary-container">
        <h2>Daily Briefing</h2>
        <div className="summary-meta">
          {new Date(summary.generated_at).toLocaleDateString()}
        </div>
        <div className="summary-content">
          <SummaryDisplay content={summary.summary_text} />
        </div>
      </div>
    );
  }

  return (
    <div className="daily-summary-empty">
      <p>Your daily briefing is ready to be created.</p>
      {generating ? (
        <div className="generating-container">
          <div className="spinner"></div>
          <p className="generating-text">Generating your personalized summary...</p>
          <p className="generating-hint">This may take up to a few minutes</p>
        </div>
      ) : (
        <button
          className="generate-summary-btn"
          onClick={handleGenerate}
        >
          Generate Daily Summary
        </button>
      )}
      {error && (
        <div className="summary-error-container">
          <p className="error-text">{error}</p>
          <button className="retry-btn" onClick={handleGenerate}>
            Try Again
          </button>
        </div>
      )}
    </div>
  );
};

const SummaryDisplay = ({ content }) => {
  try {
    const data = typeof content === 'string' ? JSON.parse(content) : content;
    return (
      <div className="summary-json-view">
        <p className="summary-greeting">{data.greeting}</p>

        {data.top_image_url && (
          <div className="summary-hero-image">
            <img src={data.top_image_url} alt="Top story visual" />
          </div>
        )}

        <div className="summary-body" style={{ whiteSpace: 'pre-line' }}>
          {data.summary}
        </div>
        {data.key_points && (
          <div className="summary-key-points">
            <h3>Key Points</h3>
            <ul>
              {data.key_points.map((kp, i) => <li key={i}>{kp}</li>)}
            </ul>
          </div>
        )}
      </div>
    );
  } catch (e) {
    // Fallback for plain text
    return <div className="summary-text-view">{content}</div>;
  }
};

export default DailySummary;
