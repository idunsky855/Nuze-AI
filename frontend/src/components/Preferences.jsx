import React, { useState, useEffect } from 'react';
import { fetchPreferences, savePreferences } from '../api';

const Preferences = ({ onSave }) => {
    const [metadata, setMetadata] = useState({
        Length: 0.5,
        Complexity: 0.5,
        Neutral: 0.5,
        Informative: 0.5,
        Emotional: 0.5
    });
    const [loading, setLoading] = useState(true);
    const [msg, setMsg] = useState(null);

    useEffect(() => {
        const loadPrefs = async () => {
            try {
                const data = await fetchPreferences();
                if (data.metadata) {
                    setMetadata(prev => ({ ...prev, ...data.metadata }));
                }
            } catch (err) {
                console.error("Failed to load preferences", err);
            } finally {
                setLoading(false);
            }
        };
        loadPrefs();
    }, []);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setMetadata(prev => ({
            ...prev,
            [name]: parseFloat(value)
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMsg(null);
        try {
            await savePreferences({ metadata });
            setMsg("Preferences saved successfully! Redirecting...");
            setTimeout(() => {
                if (onSave) onSave(metadata);
            }, 1000);
        } catch (err) {
            console.error("Failed to save", err);
            setMsg("Failed to save preferences.");
        }
    };

    if (loading) return <div className="login-container"><div className="login-card">Loading...</div></div>;

    return (
        <div className="login-container">
            <div className="login-card preferences-card">
                <div className="profile-header">
                    <h1 className="login-title">Content Preferences</h1>
                    <button onClick={onSave} className="close-button">×</button>
                </div>
                <p className="preferences-subtitle">Fine-tune your reading experience.</p>

                {msg && <div style={{ textAlign: 'center', marginBottom: '1rem', color: msg.includes('Failed') ? 'red' : 'green' }}>{msg}</div>}

                <form onSubmit={handleSubmit} className="preferences-form">

                    <div className="preferences-grid">
                        {/* Section 1: Structure */}
                        <div className="preference-section">
                            <h3 className="section-title">Structure 📏</h3>

                            <div className="preference-group">
                                <div className="label-row">
                                    <label>Length</label>
                                    <span className="value-badge">{Math.round(metadata.Length * 100)}%</span>
                                </div>
                                <div className="slider-container">
                                    <span className="slider-icon">⚡</span>
                                    <input
                                        type="range"
                                        name="Length"
                                        min="0"
                                        max="1"
                                        step="0.1"
                                        value={metadata.Length}
                                        onChange={handleChange}
                                        className="preference-slider"
                                    />
                                    <span className="slider-icon">📜</span>
                                </div>
                                <div className="slider-labels">
                                    <span>Brief</span>
                                    <span>Detailed</span>
                                </div>
                            </div>

                            <div className="preference-group">
                                <div className="label-row">
                                    <label>Complexity</label>
                                    <span className="value-badge">{Math.round(metadata.Complexity * 100)}%</span>
                                </div>
                                <div className="slider-container">
                                    <span className="slider-icon">🐣</span>
                                    <input
                                        type="range"
                                        name="Complexity"
                                        min="0"
                                        max="1"
                                        step="0.1"
                                        value={metadata.Complexity}
                                        onChange={handleChange}
                                        className="preference-slider"
                                    />
                                    <span className="slider-icon">🧠</span>
                                </div>
                                <div className="slider-labels">
                                    <span>Simple</span>
                                    <span>Deep</span>
                                </div>
                            </div>
                        </div>

                        {/* Section 2: Tone (Middle Column / Row) */}
                        <div className="preference-section">
                            <h3 className="section-title">Tone 🎭</h3>

                            <div className="preference-group">
                                <div className="label-row">
                                    <label>Objectivity</label>
                                    <span className="value-badge">{Math.round(metadata.Neutral * 100)}%</span>
                                </div>
                                <div className="slider-container">
                                    <span className="slider-icon">⚖️</span>
                                    <input
                                        type="range"
                                        name="Neutral"
                                        min="0"
                                        max="1"
                                        step="0.1"
                                        value={metadata.Neutral}
                                        onChange={handleChange}
                                        className="preference-slider"
                                    />
                                </div>
                            </div>

                            <div className="preference-group">
                                <div className="label-row">
                                    <label>Analysis</label>
                                    <span className="value-badge">{Math.round(metadata.Informative * 100)}%</span>
                                </div>
                                <div className="slider-container">
                                    <span className="slider-icon">📊</span>
                                    <input
                                        type="range"
                                        name="Informative"
                                        min="0"
                                        max="1"
                                        step="0.1"
                                        value={metadata.Informative}
                                        onChange={handleChange}
                                        className="preference-slider"
                                    />
                                </div>
                            </div>

                            <div className="preference-group">
                                <div className="label-row">
                                    <label>Emotion</label>
                                    <span className="value-badge">{Math.round(metadata.Emotional * 100)}%</span>
                                </div>
                                <div className="slider-container">
                                    <span className="slider-icon">❤️</span>
                                    <input
                                        type="range"
                                        name="Emotional"
                                        min="0"
                                        max="1"
                                        step="0.1"
                                        value={metadata.Emotional}
                                        onChange={handleChange}
                                        className="preference-slider"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="form-actions">
                        <button type="submit" className="login-button save-button">Save & Apply</button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default Preferences;
