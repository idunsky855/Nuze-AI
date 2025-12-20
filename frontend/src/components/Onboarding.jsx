import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { initiateUser } from '../api';

const categories = [
    "Politics & Law", "Economy & Business", "Science & Technology",
    "Health & Wellness", "Education & Society", "Culture & Entertainment",
    "Religion & Belief", "Sports", "World & International Affairs",
    "Opinion & General News"
];

const Onboarding = ({ onOnboardingComplete }) => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        age: '',
        gender: '',
        location: '',
        preferences: []
    });
    const [error, setError] = useState('');

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleCheckboxChange = (category) => {
        setFormData(prev => {
            const isSelected = prev.preferences.includes(category);
            if (isSelected) {
                return { ...prev, preferences: prev.preferences.filter(c => c !== category) };
            } else {
                if (prev.preferences.length < 3) {
                    return { ...prev, preferences: [...prev.preferences, category] };
                }
                return prev;
            }
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!formData.age || !formData.gender || !formData.location) {
            setError('Please fill in all required fields');
            return;
        }

        if (formData.preferences.length !== 3) {
            setError('Please select exactly 3 interests');
            return;
        }

        try {
            await initiateUser({
                ...formData,
                age: parseInt(formData.age)
            });
            if (onOnboardingComplete) {
                onOnboardingComplete();
            } else {
                navigate('/');
            }
        } catch (err) {
            setError('Failed to submit onboarding data');
            console.error(err);
        }
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <h1 className="login-title">Welcome! Tell us about yourself</h1>
                <form onSubmit={handleSubmit} className="login-form">
                    <div className="form-group">
                        <label htmlFor="age">Age *</label>
                        <input
                            type="number"
                            id="age"
                            name="age"
                            value={formData.age}
                            onChange={handleChange}
                            placeholder="Age"
                            min="0"
                            max="120"
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="gender">Gender *</label>
                        <select
                            id="gender"
                            name="gender"
                            value={formData.gender}
                            onChange={handleChange}
                        >
                            <option value="">Select...</option>
                            <option value="male">Male</option>
                            <option value="female">Female</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label htmlFor="location">Location *</label>
                        <select
                            id="location"
                            name="location"
                            value={formData.location}
                            onChange={handleChange}
                        >
                            <option value="">Select...</option>
                            <option value="urban">Urban</option>
                            <option value="suburban">Suburban</option>
                            <option value="rural">Rural</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label>Interests (Select 3 categories)</label>
                        <div className="checkbox-group" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                            {categories.map(cat => (
                                <label key={cat} style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.9rem', opacity: !formData.preferences.includes(cat) && formData.preferences.length >= 3 ? 0.5 : 1 }}>
                                    <input
                                        type="checkbox"
                                        checked={formData.preferences.includes(cat)}
                                        onChange={() => handleCheckboxChange(cat)}
                                        disabled={!formData.preferences.includes(cat) && formData.preferences.length >= 3}
                                    />
                                    {cat}
                                </label>
                            ))}
                        </div>
                    </div>

                    {error && <p className="error-message">{error}</p>}

                    <button type="submit" className="login-button">Get Started</button>
                </form>
            </div>
        </div>
    );
};

export default Onboarding;
