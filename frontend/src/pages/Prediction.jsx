import { useState, useEffect } from 'react';
import {
    Zap,
    Calculator,
    RefreshCw,
    Settings,
    ChevronDown,
    ChevronUp,
    Download,
    FileText,
    CheckCircle,
    TrendingUp,
    Calendar,
    ArrowUp,
    ArrowDown
} from 'lucide-react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Area,
    AreaChart,
    Legend
} from 'recharts';
import { useApp } from '../context/AppContext';
import { modelsApi, billApi, forecastApi } from '../services/api';

const Prediction = () => {
    const { appliances, availableModels, tariffRate, setTariffRate } = useApp();

    // Local state for selected model (immediate UI feedback)
    const [selectedModel, setSelectedModel] = useState('stacking');

    const [applianceInputs, setApplianceInputs] = useState({
        fan: { count: 2, hours: 8 },
        refrigerator: { count: 1, hours: 24 },
        air_conditioner: { count: 1, hours: 4 },
        television: { count: 2, hours: 5 },
        monitor: { count: 1, hours: 8 },
        motor_pump: { count: 0, hours: 1 },
    });

    // Validation state
    const [validationErrors, setValidationErrors] = useState([]);

    const [month, setMonth] = useState(new Date().getMonth() + 1);
    const [city, setCity] = useState('Mumbai');
    const [company, setCompany] = useState('Tata Power');
    const [customerName, setCustomerName] = useState('Customer');
    const [prediction, setPrediction] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [showAdvanced, setShowAdvanced] = useState(false);

    // PDF generation state
    const [generatingPdf, setGeneratingPdf] = useState(false);
    const [generatedBill, setGeneratedBill] = useState(null);

    // Forecast state - integrated into prediction flow
    const [forecast3Months, setForecast3Months] = useState(null);
    const [forecast6Months, setForecast6Months] = useState(null);
    const [loadingForecast, setLoadingForecast] = useState(false);

    const cities = ['Mumbai', 'Delhi', 'Chennai', 'Kolkata', 'Hyderabad', 'Bangalore', 'Pune', 'Ahmedabad'];
    const companies = ['Tata Power', 'Reliance Energy', 'Adani Power', 'NHPC', 'NTPC', 'Power Grid Corp'];
    const months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];

    // Sync with available models on load
    useEffect(() => {
        if (availableModels.length > 0) {
            const readyModels = availableModels.filter(m => m.status === 'ready');
            if (readyModels.length > 0 && !readyModels.find(m => m.id === selectedModel)) {
                setSelectedModel(readyModels[0].id);
            }
        }
    }, [availableModels]);

    const handleInputChange = (appliance, field, value) => {
        const numValue = parseFloat(value) || 0;
        let finalValue = numValue;

        // Validation logic: don't let user enter invalid combinations
        if (field === 'count' && appliance !== 'motor_pump') {
            finalValue = Math.max(0, numValue);
        }
        if (field === 'hours') {
            finalValue = Math.min(24, Math.max(0, numValue));
        }

        setApplianceInputs(prev => {
            const newState = {
                ...prev,
                [appliance]: {
                    ...prev[appliance],
                    [field]: finalValue
                }
            };

            // Proactive logic: if count is 0, set hours to 0
            if (field === 'count' && finalValue === 0) {
                newState[appliance].hours = 0;
            }
            // Proactive logic: if hours > 0, ensure count is at least 1
            if (field === 'hours' && finalValue > 0 && newState[appliance].count === 0) {
                newState[appliance].count = 1;
            }

            return newState;
        });

        setValidationErrors([]);
    };

    const handleModelSelect = (modelId) => {
        const model = availableModels.find(m => m.id === modelId);
        if (model && model.status === 'ready') {
            setSelectedModel(modelId);
            modelsApi.select(modelId).catch(console.error);
        }
    };

    const generatePdfBill = async (predictionResult) => {
        setGeneratingPdf(true);
        try {
            const appliancesForPdf = Object.entries(applianceInputs)
                .filter(([_, data]) => data.count > 0 || (data.hours > 0 && _ === 'refrigerator'))
                .map(([name, data]) => {
                    const powerRatings = {
                        fan: 75, refrigerator: 150, air_conditioner: 1500,
                        television: 100, monitor: 50, motor_pump: 750
                    };
                    return {
                        name: name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
                        power_rating: powerRatings[name] || 100,
                        quantity: data.count || 1,
                        average_daily_hours: data.hours
                    };
                });

            const billingPeriod = `${months[month - 1]} ${new Date().getFullYear()}`;

            const result = await billApi.generate({
                user_name: customerName || 'Customer',
                billing_period: billingPeriod,
                tariff_rate: tariffRate,
                city: city,
                company: company,
                appliances: appliancesForPdf
            });

            setGeneratedBill(result);
        } catch (err) {
            console.error('PDF generation failed:', err);
        } finally {
            setGeneratingPdf(false);
        }
    };

    // Calculate total consumption from appliance inputs
    const calculateTotalConsumption = () => {
        const powerRatings = {
            fan: 75, refrigerator: 150, air_conditioner: 1500,
            television: 100, monitor: 50, motor_pump: 750
        };
        let totalKwh = 0;
        Object.entries(applianceInputs).forEach(([key, data]) => {
            if (data.count > 0) {
                totalKwh += (powerRatings[key] * data.count * data.hours * 30) / 1000;
            }
        });
        return totalKwh;
    };

    const generateForecasts = async () => {
        setLoadingForecast(true);
        try {
            // Calculate consumption from current inputs for accurate forecasting
            const customConsumption = calculateTotalConsumption();

            // Fetch both 3-month and 6-month forecasts with custom consumption
            const [forecast3, forecast6] = await Promise.all([
                forecastApi.getCustom(3, tariffRate, customConsumption),
                forecastApi.getCustom(6, tariffRate, customConsumption)
            ]);
            setForecast3Months(forecast3);
            setForecast6Months(forecast6);
        } catch (err) {
            console.error('Forecast generation failed:', err);
        } finally {
            setLoadingForecast(false);
        }
    };

    // Validate inputs before prediction
    const validateInputs = () => {
        const errors = [];

        // Check if any appliance has hours > 0 but count = 0 (except motor_pump)
        Object.entries(applianceInputs).forEach(([key, data]) => {
            if (key !== 'motor_pump' && data.hours > 0 && data.count === 0) {
                const appName = applianceLabels[key];
                errors.push(`${appName}: Count cannot be 0 when Hours/Day is set`);
            }
        });

        // Check if at least one appliance has usage
        const hasAnyUsage = Object.values(applianceInputs).some(d => d.count > 0 && d.hours > 0);
        if (!hasAnyUsage) {
            errors.push('Please add at least one appliance with count and hours');
        }

        return errors;
    };

    const handlePredict = async () => {
        // Validate inputs first
        const errors = validateInputs();
        if (errors.length > 0) {
            setValidationErrors(errors);
            return;
        }

        setLoading(true);
        setError(null);
        setValidationErrors([]);
        setPrediction(null);
        setGeneratedBill(null);
        setForecast3Months(null);
        setForecast6Months(null);

        try {
            const result = await modelsApi.predict({
                ...applianceInputs,
                month,
                city,
                company,
                tariff_rate: tariffRate,
                model_id: selectedModel
            });

            setPrediction(result);

            // Automatically generate PDF and forecasts after successful prediction
            await Promise.all([
                generatePdfBill(result),
                generateForecasts()
            ]);

        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleDownloadPdf = () => {
        if (generatedBill?.bill_id) {
            window.open(billApi.download(generatedBill.bill_id), '_blank');
        }
    };

    const applianceIcons = {
        fan: '🌀', refrigerator: '🧊', air_conditioner: '❄️',
        television: '📺', monitor: '🖥️', motor_pump: '💧'
    };

    const applianceLabels = {
        fan: 'Fans', refrigerator: 'Refrigerator', air_conditioner: 'Air Conditioner',
        television: 'Television', monitor: 'Computer/Monitor', motor_pump: 'Motor Pump'
    };

    // Prepare chart data from forecasts
    const chartData = forecast6Months?.forecasts?.map(f => ({
        month: f.month_name.substring(0, 3),
        bill: f.forecasted_bill,
        lower: f.lower_bound,
        upper: f.upper_bound
    })) || [];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold">Bill Prediction & Forecast</h1>
                <p className="text-text-secondary mt-1">
                    Predict your electricity bill, generate PDF invoice, and view future forecasts
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Input Form */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Model Selection */}
                    <div className="glass-card p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold flex items-center gap-2">
                                <Settings size={20} />
                                ML Model Selection
                            </h3>
                            <span className="text-sm text-text-secondary">
                                Selected: <span className="text-primary font-medium">
                                    {availableModels.find(m => m.id === selectedModel)?.name || 'Unknown'}
                                </span>
                            </span>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            {availableModels.map((model) => (
                                <button
                                    key={model.id}
                                    onClick={() => handleModelSelect(model.id)}
                                    disabled={model.status !== 'ready'}
                                    className={`p-4 rounded-xl border-2 transition-all text-left ${selectedModel === model.id
                                        ? 'border-primary bg-primary/20 ring-2 ring-primary/30'
                                        : model.status === 'ready'
                                            ? 'border-border hover:border-primary/50 hover:bg-surface-light'
                                            : 'border-border opacity-50 cursor-not-allowed'
                                        }`}
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            {selectedModel === model.id && (
                                                <CheckCircle size={18} className="text-primary" />
                                            )}
                                            <span className="font-semibold">{model.name}</span>
                                        </div>
                                        <span className={`badge ${model.status === 'ready' ? 'badge-success' : 'badge-warning'}`}>
                                            {model.status}
                                        </span>
                                    </div>
                                    <p className="text-sm text-text-secondary mt-2">{model.description}</p>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Customer Details */}
                    <div className="glass-card p-6">
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <FileText size={20} />
                            Customer Details
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="text-sm text-text-secondary">Customer Name</label>
                                <input
                                    type="text"
                                    value={customerName}
                                    onChange={(e) => setCustomerName(e.target.value)}
                                    placeholder="Enter customer name"
                                    className="input-field mt-1"
                                />
                            </div>
                            <div>
                                <label className="text-sm text-text-secondary">Billing Month</label>
                                <select
                                    value={month}
                                    onChange={(e) => setMonth(parseInt(e.target.value))}
                                    className="input-field mt-1"
                                >
                                    {months.map((m, i) => (
                                        <option key={i} value={i + 1}>{m}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </div>

                    {/* Appliance Inputs */}
                    <div className="glass-card p-6">
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Zap size={20} />
                            Appliance Usage
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {Object.entries(applianceInputs).map(([key, value]) => (
                                <div key={key} className="glass-card-light p-4">
                                    <div className="flex items-center gap-2 mb-3">
                                        <span className="text-2xl">{applianceIcons[key]}</span>
                                        <span className="font-medium">{applianceLabels[key]}</span>
                                    </div>
                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <label className="text-xs text-text-secondary">Count</label>
                                            <input
                                                type="number"
                                                min="0"
                                                value={value.count}
                                                onChange={(e) => handleInputChange(key, 'count', e.target.value)}
                                                className="input-field mt-1"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-xs text-text-secondary">Hours/Day</label>
                                            <input
                                                type="number"
                                                min="0"
                                                max="24"
                                                value={value.hours}
                                                onChange={(e) => handleInputChange(key, 'hours', e.target.value)}
                                                className="input-field mt-1"
                                            />
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Advanced Options */}
                    <div className="glass-card p-6">
                        <button
                            onClick={() => setShowAdvanced(!showAdvanced)}
                            className="flex items-center justify-between w-full"
                        >
                            <h3 className="text-lg font-semibold">Advanced Options</h3>
                            {showAdvanced ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                        </button>

                        {showAdvanced && (
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                                <div>
                                    <label className="text-sm text-text-secondary">City</label>
                                    <select
                                        value={city}
                                        onChange={(e) => setCity(e.target.value)}
                                        className="input-field mt-1"
                                    >
                                        {cities.map((c) => (<option key={c} value={c}>{c}</option>))}
                                    </select>
                                </div>
                                <div>
                                    <label className="text-sm text-text-secondary">Company</label>
                                    <select
                                        value={company}
                                        onChange={(e) => setCompany(e.target.value)}
                                        className="input-field mt-1"
                                    >
                                        {companies.map((c) => (<option key={c} value={c}>{c}</option>))}
                                    </select>
                                </div>
                                <div>
                                    <label className="text-sm text-text-secondary">Tariff Rate (₹/kWh)</label>
                                    <input
                                        type="number"
                                        step="0.1"
                                        value={tariffRate}
                                        onChange={(e) => setTariffRate(parseFloat(e.target.value) || 8.0)}
                                        className="input-field mt-1"
                                    />
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Predict Button */}
                    <button
                        onClick={handlePredict}
                        disabled={loading || generatingPdf || loadingForecast}
                        className="btn-primary w-full flex items-center justify-center gap-2 text-lg py-4"
                    >
                        {loading ? (
                            <><RefreshCw size={20} className="animate-spin" /> Predicting...</>
                        ) : generatingPdf ? (
                            <><RefreshCw size={20} className="animate-spin" /> Generating PDF...</>
                        ) : loadingForecast ? (
                            <><RefreshCw size={20} className="animate-spin" /> Loading Forecasts...</>
                        ) : (
                            <><Calculator size={20} /> Predict, Generate PDF & Forecast</>
                        )}
                    </button>

                    {error && (
                        <div className="bg-error/10 border border-error/30 rounded-xl p-4 text-error">
                            {error}
                        </div>
                    )}

                    {validationErrors.length > 0 && (
                        <div className="bg-warning/10 border border-warning/30 rounded-xl p-4">
                            <p className="font-semibold text-warning mb-2">Please fix the following:</p>
                            <ul className="list-disc list-inside text-warning text-sm space-y-1">
                                {validationErrors.map((err, i) => (
                                    <li key={i}>{err}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>

                {/* Results Column */}
                <div className="space-y-6">
                    {prediction ? (
                        <>
                            {/* Main Prediction */}
                            <div className="glass-card p-6 text-center">
                                
                                <p className="text-text-secondary">Current Month Bill</p>
                                <p className="text-5xl font-bold mt-2 text-white">
                                    ₹{prediction.predicted_bill?.toFixed(2)}
                                </p>
                                
                                <div className="mt-4 pt-4 border-t border-border">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-text-secondary">Est. Consumption</span>
                                        <span className="font-medium">{prediction.estimated_consumption_kwh?.toFixed(2)} kWh</span>
                                    </div>
                                    <div className="flex justify-between text-sm mt-2">
                                        <span className="text-text-secondary">Tariff Rate</span>
                                        <span className="font-medium">₹{prediction.tariff_rate}/kWh</span>
                                    </div>
                                </div>
                            </div>

                            {/* PDF Download */}
                            {generatedBill && (
                                <div className="glass-card p-6">
                                    <div className="flex items-center gap-3 mb-4">
                                        <CheckCircle className="text-success" size={24} />
                                        <div>
                                            <h3 className="font-semibold">PDF Bill Ready!</h3>
                                            <p className="text-xs text-text-secondary">Bill ID: {generatedBill.bill_id}</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={handleDownloadPdf}
                                        className="btn-primary w-full flex items-center justify-center gap-2"
                                    >
                                        <Download size={18} />
                                        Download PDF Bill
                                    </button>
                                </div>
                            )}

                        </>
                    ) : (
                        <div className="glass-card p-6 text-center">
                            <div className="w-20 h-20 rounded-full bg-surface-light flex items-center justify-center mx-auto mb-4">
                                <Calculator size={40} className="text-text-secondary" />
                            </div>
                            <p className="text-text-secondary">
                                Configure your appliances and click "Predict" to see the estimated bill, PDF, and forecasts
                            </p>
                        </div>
                    )}
                </div>
            </div>

            {/* Forecasts Section - Shows after prediction */}
            {(forecast3Months || forecast6Months) && (
                <div className="space-y-6 mt-6">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-full gradient-accent flex items-center justify-center">
                            <TrendingUp size={24} className="text-white" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold">Future Bill Forecasts</h2>
                            <p className="text-text-secondary">Predicted bills for upcoming months based on your usage pattern</p>
                        </div>
                    </div>

                    {/* Forecast Summary Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="stats-card">
                            <p className="text-text-secondary text-sm">3-Month Total</p>
                            <p className="text-2xl font-bold mt-1">
                                ₹{forecast3Months?.summary?.total_forecasted_bill?.toFixed(0) || '---'}
                            </p>
                        </div>
                        <div className="stats-card">
                            <p className="text-text-secondary text-sm">6-Month Total</p>
                            <p className="text-2xl font-bold mt-1">
                                ₹{forecast6Months?.summary?.total_forecasted_bill?.toFixed(0) || '---'}
                            </p>
                        </div>
                        <div className="stats-card">
                            <p className="text-text-secondary text-sm">Avg Monthly</p>
                            <p className="text-2xl font-bold mt-1">
                                ₹{forecast6Months?.summary?.average_monthly_bill?.toFixed(0) || '---'}
                            </p>
                        </div>
                        <div className="stats-card">
                            <p className="text-text-secondary text-sm">Peak Month</p>
                            <p className="text-2xl font-bold mt-1 text-warning">
                                ₹{forecast6Months?.summary?.max_monthly?.toFixed(0) || '---'}
                            </p>
                        </div>
                    </div>

                    {/* Forecast Chart */}
                    <div className="glass-card p-6">
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Calendar size={20} />
                            6-Month Forecast Chart
                        </h3>
                        <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={chartData}>
                                    <defs>
                                        <linearGradient id="colorForecastPred" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                    <XAxis dataKey="month" stroke="#94a3b8" />
                                    <YAxis stroke="#94a3b8" />
                                    <Tooltip
                                        contentStyle={{
                                            background: '#1e293b',
                                            border: '1px solid #475569',
                                            borderRadius: '8px'
                                        }}
                                        formatter={(value) => [`₹${value?.toFixed(2)}`, 'Bill']}
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="upper"
                                        stroke="#8b5cf6"
                                        fill="none"
                                        strokeWidth={1}
                                        strokeDasharray="3 3"
                                        name="Upper Bound"
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="lower"
                                        stroke="#8b5cf6"
                                        fill="none"
                                        strokeWidth={1}
                                        strokeDasharray="3 3"
                                        name="Lower Bound"
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="bill"
                                        stroke="#3b82f6"
                                        fill="url(#colorForecastPred)"
                                        strokeWidth={2}
                                        name="Forecast"
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Monthly Forecast Details */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* 3-Month Forecast */}
                        <div className="glass-card p-6">
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <TrendingUp size={20} className="text-success" />
                                3-Month Forecast
                            </h3>
                            <div className="space-y-2">
                                {forecast3Months?.forecasts?.map((f, i) => (
                                    <div key={i} className="flex items-center justify-between p-3 glass-card-light rounded-lg">
                                        <div>
                                            <p className="font-medium">{f.month_name} {f.year}</p>
                                            <p className="text-xs text-text-secondary">{f.forecasted_kwh?.toFixed(0)} kWh</p>
                                        </div>
                                        <div className="text-right">
                                            <p className="font-bold text-lg">₹{f.forecasted_bill?.toFixed(0)}</p>
                                            <p className="text-xs text-text-secondary">
                                                ±{((f.upper_bound - f.lower_bound) / 2).toFixed(0)}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* 6-Month Forecast */}
                        <div className="glass-card p-6">
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <TrendingUp size={20} className="text-primary" />
                                6-Month Forecast
                            </h3>
                            <div className="space-y-2 max-h-64 overflow-y-auto">
                                {forecast6Months?.forecasts?.map((f, i) => (
                                    <div key={i} className="flex items-center justify-between p-3 glass-card-light rounded-lg">
                                        <div>
                                            <p className="font-medium">{f.month_name} {f.year}</p>
                                            <p className="text-xs text-text-secondary">
                                                Season: {f.seasonal_factor}x
                                            </p>
                                        </div>
                                        <div className="text-right">
                                            <p className="font-bold text-lg">₹{f.forecasted_bill?.toFixed(0)}</p>
                                            {i === 0 && prediction && (
                                                <p className={`text-xs flex items-center gap-1 justify-end ${f.forecasted_bill > prediction.predicted_bill ? 'text-error' : 'text-success'
                                                    }`}>
                                                    {f.forecasted_bill > prediction.predicted_bill ? (
                                                        <ArrowUp size={12} />
                                                    ) : (
                                                        <ArrowDown size={12} />
                                                    )}
                                                    vs current
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Prediction;