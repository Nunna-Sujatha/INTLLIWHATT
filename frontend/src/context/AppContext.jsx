import { createContext, useContext, useState, useEffect } from 'react';
import { dataApi, modelsApi } from '../services/api';

const AppContext = createContext(null);

export const useApp = () => {
    const context = useContext(AppContext);
    if (!context) {
        throw new Error('useApp must be used within AppProvider');
    }
    return context;
};

export const AppProvider = ({ children }) => {
    const [appliances, setAppliances] = useState([]);
    const [activeModel, setActiveModel] = useState('stacking');
    const [availableModels, setAvailableModels] = useState([]);
    const [loading, setLoading] = useState(true);
    const [tariffRate, setTariffRate] = useState(8.0);
    const [dashboardData, setDashboardData] = useState(null);
    const [sidebarOpen, setSidebarOpen] = useState(true);

    // Load initial data
    useEffect(() => {
        const loadInitialData = async () => {
            try {
                setLoading(true);

                // Load appliances
                const appliancesRes = await dataApi.getAppliances();
                setAppliances(appliancesRes.appliances || []);

                // Load models
                const modelsRes = await modelsApi.getAvailable();
                setAvailableModels(modelsRes.models || []);
                setActiveModel(modelsRes.active_model || 'stacking');

                // Load dashboard data
                const dashboardRes = await dataApi.getDashboard();
                setDashboardData(dashboardRes);

            } catch (error) {
                console.error('Failed to load initial data:', error);
            } finally {
                setLoading(false);
            }
        };

        loadInitialData();
    }, []);

    const refreshAppliances = async () => {
        try {
            const res = await dataApi.getAppliances();
            setAppliances(res.appliances || []);
        } catch (error) {
            console.error('Failed to refresh appliances:', error);
        }
    };

    const refreshDashboard = async () => {
        try {
            const res = await dataApi.getDashboard();
            setDashboardData(res);
        } catch (error) {
            console.error('Failed to refresh dashboard:', error);
        }
    };

    const selectModel = async (modelId) => {
        try {
            await modelsApi.select(modelId);
            setActiveModel(modelId);
        } catch (error) {
            console.error('Failed to select model:', error);
            throw error;
        }
    };

    const value = {
        appliances,
        setAppliances,
        refreshAppliances,
        activeModel,
        setActiveModel,
        selectModel,
        availableModels,
        loading,
        tariffRate,
        setTariffRate,
        dashboardData,
        refreshDashboard,
        sidebarOpen,
        setSidebarOpen,
    };

    return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export default AppContext;
