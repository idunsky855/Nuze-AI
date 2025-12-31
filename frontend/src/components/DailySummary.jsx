
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
      if (data && data.status === 'pending') {
        // Summary is being generated - show generating state
        setGenerating(true);
        setSummary(null);
      } else {
        setSummary(data);
        setGenerating(false);
      }
    } catch (err) {
      // 404 means no summary yet - that's fine
      if (err.response && err.response.status === 404) {
        setSummary(null);
      } else {
        console.error("Error loading summary:", err);
        setError("Failed to load daily summary.");
      }
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
      if (data && data.summary_text && data.status === 'completed') {
        setSummary(data);
        setGenerating(false);
      } else {
        // If response is empty or pending, try fetching again
        await loadSummary();
      }
    } catch (e) {
      if (e.response && e.response.status === 202) {
        // Already generating - show generating state
        setGenerating(true);
      } else if (e.response && e.response.status === 404) {
        setError("Could not generate summary (no relevant articles found for today).");
        setGenerating(false);
      } else if (e.response && e.response.status === 500) {
        setError("Failed to generate summary. The AI model may be unavailable. Please try again.");
        setGenerating(false);
      } else {
        setError("Failed to generate summary. Please try again.");
        setGenerating(false);
      }
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
        <>
          <p className="style-preferences-hint">
            💡 Tip: Customize your summary style in your <strong>Profile → Preferences</strong>
          </p>
          <button
            className="generate-summary-btn"
            onClick={handleGenerate}
          >
            Generate Daily Summary
          </button>
        </>
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
