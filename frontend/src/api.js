import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Helper to get token
const getAuthHeader = () => {
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
};

export const login = async (email, password) => {
    const formData = new FormData();
    formData.append('username', email); // OAuth2PasswordRequestForm expects 'username'
    formData.append('password', password);

    const response = await axios.post(`${API_URL}/auth/login`, formData);
    return response.data;
};

export const signup = async (userData) => {
    const response = await axios.post(`${API_URL}/auth/signup`, userData);
    return response.data;
};

export const fetchArticles = async (skip = 0, limit = 20) => {
    try {
        // Try to hit the real endpoint first
        const response = await axios.get(`${API_URL}/feed?skip=${skip}&limit=${limit}`, { headers: getAuthHeader() });
        return response.data;
    } catch (error) {
        console.error("Error fetching articles:", error);
        throw error;
    }
};

export const fetchReadHistory = async (skip = 0, limit = 20) => {
    try {
        const response = await axios.get(`${API_URL}/me/read?skip=${skip}&limit=${limit}`, { headers: getAuthHeader() });
        return response.data;
    } catch (error) {
        console.error("Error fetching read history:", error);
        throw error;
    }
};

export const recordInteraction = async (articleId, type) => {
    await axios.post(`${API_URL}/interactions`, { articleId, type }, { headers: getAuthHeader() });
    console.log(`Interaction recorded: ${type} on article ${articleId}`);
    return Promise.resolve();
};

export const initiateUser = async (data) => {
    const response = await axios.post(`${API_URL}/me/onboarding`, data, {
        headers: getAuthHeader()
    });
    return response.data;
};

export const fetchCurrentUser = async () => {
    const response = await axios.get(`${API_URL}/me`, { headers: getAuthHeader() });
    return response.data;
};

export const fetchPreferences = async () => {
    const response = await axios.get(`${API_URL}/me/preferences`, { headers: getAuthHeader() });
    return response.data;
};

export const savePreferences = async (preferences) => {
    const response = await axios.post(`${API_URL}/me/preferences`, preferences, { headers: getAuthHeader() });
    return response.data;
};

export const updatePassword = async (currentPassword, newPassword) => {
    const response = await axios.post(`${API_URL}/me/password`, {
        current_password: currentPassword,
        new_password: newPassword
    }, { headers: getAuthHeader() });
    return response.data;
};

export const getDailySummary = async () => {
    try {
        const response = await axios.get(`${API_URL}/summary/today`, { headers: getAuthHeader() });
        return response.data;
    } catch (error) {
        if (error.response && error.response.status === 404) {
            return null;
        }
        console.error("Error fetching daily summary:", error);
        throw error;
    }
};

export const generateDailySummary = async () => {
    try {
        const response = await axios.post(`${API_URL}/summary/today`, {}, { headers: getAuthHeader() });
        return response.data;
    } catch (error) {
        console.error("Error generating daily summary:", error);
        throw error;
    }
};
