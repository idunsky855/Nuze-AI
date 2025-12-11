import axios from 'axios';

const API_URL = 'http://localhost:8000'; // Adjust based on backend URL

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

export const fetchArticles = async () => {
    try {
        // Try to hit the real endpoint first
        const response = await axios.get(`${API_URL}/feed`, { headers: getAuthHeader() });
        return response.data;
    } catch (error) {
        console.error("Error fetching articles:", error);
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
