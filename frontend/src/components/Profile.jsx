import React, { useState } from 'react';
import { updatePassword } from '../api';

const Profile = ({ user, onUpdateProfile, onCancel }) => {
    const [formData, setFormData] = useState({
        firstName: user.first_name || user.firstName || '',
        lastName: user.last_name || user.lastName || '',
        age: user.age || '',
        gender: user.gender || '',
        location: user.location || ''
    });

    const [passwordData, setPasswordData] = useState({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
    });

    const [showPasswordSection, setShowPasswordSection] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });
    const [passwordMessage, setPasswordMessage] = useState({ type: '', text: '' });

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handlePasswordChange = (e) => {
        const { name, value } = e.target;
        setPasswordData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmitProfile = (e) => {
        e.preventDefault();
        onUpdateProfile(formData);
        setMessage({ type: 'success', text: 'Profile updated successfully!' });
        setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    };

    const handleSubmitPassword = async (e) => {
        e.preventDefault();
        if (passwordData.newPassword !== passwordData.confirmPassword) {
            setPasswordMessage({ type: 'error', text: 'New passwords do not match' });
            return;
        }

        try {
            await updatePassword(passwordData.currentPassword, passwordData.newPassword);

            // Success
            setMessage({ type: 'success', text: 'Password changed successfully!' });
            setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
            setPasswordMessage({ type: '', text: '' });
            setShowPasswordSection(false);

            setTimeout(() => {
                setMessage({ type: '', text: '' });
            }, 3000);
        } catch (err) {
            console.error(err);
            // Default error or specific from backend
            const errorText = err.response?.data?.detail || 'Failed to update password';
            setPasswordMessage({ type: 'error', text: errorText });
            setTimeout(() => setPasswordMessage({ type: '', text: '' }), 3000);
        }
    };

    // Helper to get initials
    const getInitials = () => {
        const first = formData.firstName || user.name || '';
        const last = formData.lastName || '';
        if (!first) return 'Me';
        return (first.charAt(0) + (last ? last.charAt(0) : '')).toUpperCase();
    };

    return (
        <div className="login-container">
            <div className="login-card profile-card">
                <div className="profile-header">
                    <h1 className="login-title">My Profile</h1>
                    <button onClick={onCancel} className="close-button">×</button>
                </div>

                <div className="profile-avatar-section">
                    <div className="avatar-circle">
                        {getInitials()}
                    </div>
                    <p className="profile-email">{user.email}</p>
                </div>

                {message.text && (
                    <div className={`message ${message.type}`}>
                        {message.text}
                    </div>
                )}

                <div className="profile-content-grid">
                    {/* Left Column: Personal Info */}
                    <div className="profile-section">
                        <h3 className="section-title">Personal Details 👤</h3>
                        <form onSubmit={handleSubmitProfile} className="login-form">
                            <div className="form-row">
                                <div className="form-group">
                                    <label htmlFor="firstName">First Name</label>
                                    <input
                                        type="text"
                                        id="firstName"
                                        name="firstName"
                                        value={formData.firstName}
                                        onChange={handleChange}
                                        placeholder="First Name"
                                    />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="lastName">Last Name</label>
                                    <input
                                        type="text"
                                        id="lastName"
                                        name="lastName"
                                        value={formData.lastName}
                                        onChange={handleChange}
                                        placeholder="Last Name"
                                    />
                                </div>
                            </div>

                            <div className="form-row">
                                <div className="form-group">
                                    <label htmlFor="age">Age</label>
                                    <input
                                        type="number"
                                        id="age"
                                        name="age"
                                        value={formData.age}
                                        onChange={handleChange}
                                        placeholder="Age"
                                    />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="gender">Gender</label>
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
                            </div>

                            <div className="form-row">
                                <div className="form-group" style={{ width: '100%' }}>
                                    <label htmlFor="location">Location</label>
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
                            </div>

                            <button type="submit" className="login-button save-button">Save Changes</button>
                        </form>
                    </div>

                    {/* Right Column/Section: Security */}
                    <div className="profile-section security-section">
                        <h3 className="section-title">Security 🔒</h3>

                        {!showPasswordSection ? (
                            <div className="security-placeholder">
                                <p>Password last changed: Never</p>
                                <button
                                    type="button"
                                    className="login-button secondary-button"
                                    onClick={() => setShowPasswordSection(true)}
                                >
                                    Change Password
                                </button>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmitPassword} className="login-form password-form active">
                                {passwordMessage.text && (
                                    <div className={`message ${passwordMessage.type}`}>
                                        {passwordMessage.text}
                                    </div>
                                )}
                                <div className="form-group">
                                    <label htmlFor="currentPassword">Current Password</label>
                                    <input
                                        type="password"
                                        id="currentPassword"
                                        name="currentPassword"
                                        value={passwordData.currentPassword}
                                        onChange={handlePasswordChange}
                                        placeholder="••••••"
                                    />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="newPassword">New Password</label>
                                    <input
                                        type="password"
                                        id="newPassword"
                                        name="newPassword"
                                        value={passwordData.newPassword}
                                        onChange={handlePasswordChange}
                                        placeholder="New Password"
                                    />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="confirmPassword">Confirm Password</label>
                                    <input
                                        type="password"
                                        id="confirmPassword"
                                        name="confirmPassword"
                                        value={passwordData.confirmPassword}
                                        onChange={handlePasswordChange}
                                        placeholder="Confirm Password"
                                    />
                                </div>

                                <div className="password-actions">
                                    <button type="button" className="text-button" onClick={() => setShowPasswordSection(false)}>Cancel</button>
                                    <button type="submit" className="login-button warning-button">Update</button>
                                </div>
                            </form>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Profile;
