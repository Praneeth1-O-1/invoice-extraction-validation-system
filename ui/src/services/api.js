import axios from 'axios';

const API_URL = 'http://localhost:8000';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const invoiceService = {
    // Check backend health
    checkHealth: async () => {
        try {
            const response = await api.get('/health');
            return response.data;
        } catch (error) {
            console.error('Health check failed:', error);
            throw error;
        }
    },

    // Get API info and validation rules
    getApiInfo: async () => {
        try {
            const response = await api.get('/api/info');
            return response.data;
        } catch (error) {
            console.error('Failed to fetch API info:', error);
            throw error;
        }
    },

    // Extract data from PDF files
    extractAndValidate: async (files) => {
        try {
            const formData = new FormData();
            files.forEach((file) => {
                formData.append('files', file);
            });

            const response = await api.post('/extract-and-validate-pdfs', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            return response.data;
        } catch (error) {
            console.error('Extraction failed:', error);
            throw error;
        }
    },

    // Validate JSON data directly
    validateJson: async (invoices) => {
        try {
            const response = await api.post('/validate-json', invoices);
            return response.data;
        } catch (error) {
            console.error('Validation failed:', error);
            throw error;
        }
    },
};
