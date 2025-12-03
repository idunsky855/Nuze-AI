import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { signup } from '../api';

const Signup = ({ onSwitchToLogin }) => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        name: ''
    });
    const [error, setError] = useState('');

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        // Basic validation
        if (!formData.email || !formData.password) {
            setError('Please fill in all required fields');
            return;
        }
        try {
            await signup(formData);
            // After successful signup, redirect to login so they can get a token
            // Or we could auto-login, but let's keep it simple for now
            alert('Signup successful! Please login.');
            onSwitchToLogin();
        } catch (err) {
            console.error(err);
            if (err.response && err.response.data && err.response.data.detail) {
                setError(err.response.data.detail);
            } else if (err.message) {
                setError(`Signup failed: ${err.message}`);
            } else {
                setError('Signup failed. Please try again.');
            }
        }
    };

    return (
        <div className="login-container">
            <div className="login-card signup-card">
                <h1 className="login-title">Sign Up</h1>
                <form onSubmit={handleSubmit} className="login-form">
                    <div className="form-group">
                        <label htmlFor="email">Email *</label>
                        <input
                            type="email"
                            id="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            placeholder="Email"
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="password">Password *</label>
                        <input
                            type="password"
                            id="password"
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
                            placeholder="Password"
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="name">Name</label>
                        <input
                            type="text"
                            id="name"
                            name="name"
                            value={formData.name}
                            onChange={handleChange}
                            placeholder="Full Name"
                        />
                    </div>

                    {error && <p className="error-message">{error}</p>}

                    <button type="submit" className="login-button">Sign Up</button>

                    <div className="auth-switch">
                        <p>Already have an account?</p>
                        <button type="button" className="switch-button" onClick={onSwitchToLogin}>
                            Login here
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default Signup;
