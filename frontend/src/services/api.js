/**
 * API Service for Electricity Bill Prediction System
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor
api.interceptors.request.use(
    (config) => {
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor
api.interceptors.response.use(
    (response) => response.data,
    (error) => {
        const message = error.response?.data?.detail || error.message || 'An error occurred';
        console.error('API Error:', message);
        return Promise.reject(new Error(message));
    }
);

// ============ ML Models API ============
export const modelsApi = {
    getAvailable: () => api.get('/api/models/available'),
    select: (modelId) => api.post('/api/models/select', { model_id: modelId }),
    predict: (data) => api.post('/api/models/predict', data),
    train: (forceRetrain = false) => api.post('/api/models/train', { force_retrain: forceRetrain }),
    getStatus: () => api.get('/api/models/status'),
};

// ============ Chatbot API ============
export const chatApi = {
    sendMessage: (message, conversationId = null) =>
        api.post('/api/chat/message', { message, conversation_id: conversationId }),
    getBudgetGuidance: (budget, currentUsage = 0, daysInCycle = 30) =>
        api.post('/api/chat/budget-guidance', {
            budget,
            current_usage: currentUsage,
            days_in_cycle: daysInCycle
        }),
    getTips: (category = null) => api.post('/api/chat/tips', { category }),
    getHistory: () => api.get('/api/chat/history'),
    clear: () => api.post('/api/chat/clear'),
    analyzeUsage: () => api.post('/api/chat/analyze'),
};

// ============ OCR API ============
export const ocrApi = {
    getStatus: () => api.get('/api/ocr/status'),
    uploadImages: (files) => {
        const formData = new FormData();
        files.forEach((file) => formData.append('files', file));
        return api.post('/api/ocr/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },
    extractReading: (readingId) => api.post(`/api/ocr/extract/${readingId}`),
    getResults: (readingId) => api.get(`/api/ocr/results/${readingId}`),
    getHistory: () => api.get('/api/ocr/history'),
    calculateUnits: (previousReading, currentReading) =>
        api.post('/api/ocr/calculate-units', {
            previous_reading: previousReading,
            current_reading: currentReading
        }),
    quickExtract: (file) => {
        const formData = new FormData();
        formData.append('file', file);
        return api.post('/api/ocr/quick-extract', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },
};

// ============ Bill Generation API ============
export const billApi = {
    getStatus: () => api.get('/api/bill/status'),
    generate: (data) => api.post('/api/bill/generate', data),
    download: (billId) => `${API_BASE_URL}/api/bill/download/${billId}`,
    list: () => api.get('/api/bill/list'),
    preview: (data) => api.post('/api/bill/preview', data),
};

// ============ Forecast API ============
export const forecastApi = {
    get3Months: (tariffRate = 8.0) => api.get(`/api/forecast/3-months?tariff_rate=${tariffRate}`),
    get6Months: (tariffRate = 8.0) => api.get(`/api/forecast/6-months?tariff_rate=${tariffRate}`),
    getCustom: (numMonths, tariffRate = 8.0, customConsumption = null) =>
        api.post('/api/forecast/custom', {
            num_months: numMonths,
            tariff_rate: tariffRate,
            custom_consumption_kwh: customConsumption
        }),
    getYearly: (tariffRate = 8.0) => api.get(`/api/forecast/yearly?tariff_rate=${tariffRate}`),
    getCurrentEstimate: (tariffRate = 8.0) =>
        api.get(`/api/forecast/current-estimate?tariff_rate=${tariffRate}`),
    getSeasonalFactors: () => api.get('/api/forecast/seasonal-factors'),
    compare: (tariffRate = 8.0) => api.get(`/api/forecast/compare?tariff_rate=${tariffRate}`),
};

// ============ Data Management API ============
export const dataApi = {
    getAppliances: () => api.get('/api/data/appliances'),
    addAppliance: (appliance) => api.post('/api/data/appliances', appliance),
    updateAppliance: (id, data) => api.put(`/api/data/appliances/${id}`, data),
    deleteAppliance: (id) => api.delete(`/api/data/appliances/${id}`),
    updateAppliancesBulk: (appliances) => api.post('/api/data/appliances/bulk', appliances),

    getHistory: () => api.get('/api/data/history'),
    addHistoricalRecord: (record) => api.post('/api/data/history', record),
    getHistorySummary: () => api.get('/api/data/history/summary'),

    getDashboard: () => api.get('/api/data/dashboard'),
};

// ============ Health Check ============
export const healthApi = {
    check: () => api.get('/health'),
    root: () => api.get('/'),
};

export default api;
