import React, { useState } from 'react';

const Profile = ({ user, onUpdateProfile, onChangePassword, onCancel }) => {
    const [formData, setFormData] = useState({
        firstName: user.firstName || '',
        lastName: user.lastName || '',
        age: user.age || '',
        gender: user.gender || '',
        country: user.country || '',
        city: user.city || ''
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

    const handleSubmitPassword = (e) => {
        e.preventDefault();
        if (passwordData.newPassword !== passwordData.confirmPassword) {
            setPasswordMessage({ type: 'error', text: 'New passwords do not match' });
            return;
        }

        const success = onChangePassword(passwordData.currentPassword, passwordData.newPassword);
        if (success) {
            // Success message goes to the top (main message state)
            setMessage({ type: 'success', text: 'Password changed successfully!' });
            setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
            setPasswordMessage({ type: '', text: '' }); // Clear any local errors
            setShowPasswordSection(false); // Close immediately

            // Clear the success message after a delay
            setTimeout(() => {
                setMessage({ type: '', text: '' });
            }, 3000);
        } else {
            // Error message stays above the password form
            setPasswordMessage({ type: 'error', text: 'Incorrect current password' });
            setTimeout(() => setPasswordMessage({ type: '', text: '' }), 3000);
        }
    };

    return (
        <div className="login-container">
            <div className="login-card signup-card">
                <div className="profile-header">
                    <h1 className="login-title">Edit Profile</h1>
                    <button onClick={onCancel} className="close-button">×</button>
                </div>

                {message.text && (
                    <div className={`message ${message.type}`}>
                        {message.text}
                    </div>
                )}

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
                        <div className="form-group">
                            <label htmlFor="country">Country</label>
                            <input
                                type="text"
                                id="country"
                                name="country"
                                value={formData.country}
                                onChange={handleChange}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="city">City</label>
                            <input
                                type="text"
                                id="city"
                                name="city"
                                value={formData.city}
                                onChange={handleChange}
                            />
                        </div>
                    </div>

                    <button type="submit" className="login-button">Save Profile</button>
                </form>

                <div className="password-section-toggle">
                    <button
                        type="button"
                        className="toggle-button"
                        onClick={() => setShowPasswordSection(!showPasswordSection)}
                    >
                        {showPasswordSection ? 'Cancel Password Change' : 'Change Password'}
                    </button>
                </div>

                {showPasswordSection && (
                    <form onSubmit={handleSubmitPassword} className="login-form password-form">
                        <h3>Change Password</h3>
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
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="confirmPassword">Confirm New Password</label>
                            <input
                                type="password"
                                id="confirmPassword"
                                name="confirmPassword"
                                value={passwordData.confirmPassword}
                                onChange={handlePasswordChange}
                            />
                        </div>
                        <button type="submit" className="login-button warning-button">Update Password</button>
                    </form>
                )}
            </div>
        </div>
    );
};

export default Profile;
