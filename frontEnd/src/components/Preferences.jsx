import React, { useState } from 'react';

const Preferences = ({ onSave }) => {
    const [preferences, setPreferences] = useState({
        articleLength: 1, // 0: Short, 1: Random, 2: Long
        tone: 1,          // 0: Serious, 1: Neutral, 2: Fun
        updateFrequency: 1 // 0: Low, 1: Medium, 2: High
    });

    const handleChange = (e) => {
        const { name, value } = e.target;
        setPreferences(prev => ({
            ...prev,
            [name]: parseInt(value, 10)
        }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        onSave(preferences);
    };

    const getLabel = (value, labels) => {
        return labels[value] || '';
    };

    return (
        <div className="login-container">
            <div className="login-card preferences-card">
                <h1 className="login-title">Customize Your Feed</h1>
                <p className="preferences-subtitle">Tell us what you like to see.</p>

                <form onSubmit={handleSubmit} className="preferences-form">

                    <div className="preference-group">
                        <label>Article Length</label>
                        <div className="slider-container">
                            <input
                                type="range"
                                name="articleLength"
                                min="0"
                                max="2"
                                step="1"
                                value={preferences.articleLength}
                                onChange={handleChange}
                                className="preference-slider"
                            />
                            <div className="slider-labels">
                                <span className={preferences.articleLength === 0 ? 'active' : ''}>Short</span>
                                <span className={preferences.articleLength === 1 ? 'active' : ''}>Random</span>
                                <span className={preferences.articleLength === 2 ? 'active' : ''}>Long</span>
                            </div>
                        </div>
                    </div>

                    <div className="preference-group">
                        <label>Tone</label>
                        <div className="slider-container">
                            <input
                                type="range"
                                name="tone"
                                min="0"
                                max="2"
                                step="1"
                                value={preferences.tone}
                                onChange={handleChange}
                                className="preference-slider"
                            />
                            <div className="slider-labels">
                                <span className={preferences.tone === 0 ? 'active' : ''}>Serious</span>
                                <span className={preferences.tone === 1 ? 'active' : ''}>Neutral</span>
                                <span className={preferences.tone === 2 ? 'active' : ''}>Fun</span>
                            </div>
                        </div>
                    </div>

                    <div className="preference-group">
                        <label>Update Frequency</label>
                        <div className="slider-container">
                            <input
                                type="range"
                                name="updateFrequency"
                                min="0"
                                max="2"
                                step="1"
                                value={preferences.updateFrequency}
                                onChange={handleChange}
                                className="preference-slider"
                            />
                            <div className="slider-labels">
                                <span className={preferences.updateFrequency === 0 ? 'active' : ''}>Low</span>
                                <span className={preferences.updateFrequency === 1 ? 'active' : ''}>Medium</span>
                                <span className={preferences.updateFrequency === 2 ? 'active' : ''}>High</span>
                            </div>
                        </div>
                    </div>

                    <button type="submit" className="login-button">Save Preferences</button>
                </form>
            </div>
        </div>
    );
};

export default Preferences;
