import React, { useEffect, useState } from 'react';

const PreferenceUpdateToast = ({ show, oldPreferences, newPreferences }) => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (show && oldPreferences && newPreferences) {
      setVisible(true);

      // Auto-hide after 5 seconds
      const timer = setTimeout(() => {
        setVisible(false);
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [show, oldPreferences, newPreferences]);

  if (!visible || !oldPreferences || !newPreferences) return null;

  // Get the 10D category vectors (API returns as interests_vector)
  const oldCategories = oldPreferences.interests_vector || [];
  const newCategories = newPreferences.interests_vector || [];

  // Category names for the 10 dimensions
  const categoryNames = [
    'Politics', 'Business', 'Technology', 'Science',
    'Health', 'Sports', 'Entertainment', 'World',
    'Opinion', 'Lifestyle'
  ];

  return (
    <div className="preference-toast">
      <div className="preference-toast-header">
        <span className="preference-toast-icon">🎯</span>
        <span className="preference-toast-title">Interest Vector Updated!</span>
      </div>
      <div className="preference-toast-content">
        <p className="preference-toast-subtitle">Your 10D category preferences are adapting</p>
        <div className="preference-changes">
          {categoryNames.map((name, idx) => {
            const oldVal = oldCategories[idx] || 0;
            const newVal = newCategories[idx] || 0;
            const delta = newVal - oldVal;
            const hasChanged = Math.abs(delta) > 0.001;

            return (
              <div key={idx} className={`preference-change-item ${hasChanged ? 'changed' : ''}`}>
                <div className="preference-change-header">
                  <span className="preference-change-name">{name}</span>
                  {hasChanged && (
                    <span className={`preference-change-delta ${delta > 0 ? 'positive' : 'negative'}`}>
                      {delta > 0 ? '+' : ''}{delta.toFixed(3)}
                    </span>
                  )}
                </div>
                <div className="preference-change-values">
                  <span className="old-value">{oldVal.toFixed(3)}</span>
                  <span className="arrow">→</span>
                  <span className="new-value">{newVal.toFixed(3)}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default PreferenceUpdateToast;
