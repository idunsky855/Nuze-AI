import axios from 'axios';
import mockArticles from '../test/mock_articles.json';

const API_URL = 'http://localhost:8000'; // Adjust based on backend URL

export const fetchArticles = async () => {
    try {
        // In a real scenario, this would be:
        // const response = await axios.get(`${API_URL}/articles`);
        // return response.data;

        // For now, if backend endpoint doesn't exist, we might want to return mock data 
        // or try to hit the real endpoint. 
        // The user said "get articles from api", so let's try to hit it.
        // If it fails, we can handle error in component.
        // For testing purposes as requested, returning mock data from file
        console.log("Fetching mock articles for test...");
        return Promise.resolve(mockArticles);

        // Original API call logic (commented out for now)
        // const response = await axios.get(`${API_URL}/articles`);
        // return response.data;
    } catch (error) {
        console.error("Error fetching articles:", error);
        throw error;
    }
};
