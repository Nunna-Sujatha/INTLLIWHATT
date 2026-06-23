import { useState, useEffect } from 'react';
import {
    TrendingUp,
    Calendar,
    ArrowUp,
    ArrowDown,
    RefreshCw
} from 'lucide-react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
    Area,
    AreaChart
} from 'recharts';
import { forecastApi } from '../services/api';
import { useApp } from '../context/AppContext';

const Forecast = () => {
    const { tariffRate } = useApp();
    const [forecastPeriod, setForecastPeriod] = useState('6');
    const [forecast, setForecast] = useState(null);
    const [seasonalFactors, setSeasonalFactors] = useState(null);
    const [loading, setLoading] = useState(false);
    const [comparison, setComparison] = useState(null);

    useEffect(() => {
        loadForecast();
    }, [forecastPeriod, tariffRate]);

    const loadForecast = async () => {
        setLoading(true);
        try {
            let forecastRes;
            if (forecastPeriod === '3') {
                forecastRes = await forecastApi.get3Months(tariffRate);
            } else if (forecastPeriod === '6') {
                forecastRes = await forecastApi.get6Months(tariffRate);
            } else if (forecastPeriod === '12') {
                forecastRes = await forecastApi.getYearly(tariffRate);
            } else {
                forecastRes = await forecastApi.getCustom(parseInt(forecastPeriod), tariffRate);
            }
            setForecast(forecastRes);

            // Load seasonal factors
            const factorsRes = await forecastApi.getSeasonalFactors();
            setSeasonalFactors(factorsRes.factors);

            // Load comparison
            const comparisonRes = await forecastApi.compare(tariffRate);
            setComparison(comparisonRes);

        } catch (error) {
            console.error('Failed to load forecast:', error);
        } finally {
            setLoading(false);
        }
    };

    const chartData = forecast?.forecasts?.map(f => ({
        month: f.month_name.substring(0, 3),
        bill: f.forecasted_bill,
        lower: f.lower_bound,
        upper: f.upper_bound,
        kwh: f.forecasted_kwh
    })) || [];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">Bill Forecast</h1>
                    <p className="text-text-secondary mt-1">
                        Predict future electricity bills based on usage patterns
                    </p>
                </div>
                <button
                    onClick={loadForecast}
                    disabled={loading}
                    className="btn-secondary flex items-center gap-2"
                >
                    <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
                    Refresh
                </button>
            </div>

            {/* Period Selection */}
            <div className="glass-card p-4">
                <div className="flex items-center gap-4 flex-wrap">
                    <span className="text-text-secondary flex items-center gap-2">
                        <Calendar size={18} />
                        Forecast Period:
                    </span>
                    {['3', '6', '12'].map((period) => (
                        <button
                            key={period}
                            onClick={() => setForecastPeriod(period)}
                            className={`px-4 py-2 rounded-lg transition-all ${forecastPeriod === period
                                    ? 'gradient-primary text-white'
                                    : 'bg-surface hover:bg-surface-light'
                                }`}
                        >
                            {period} Months
                        </button>
                    ))}
                </div>
            </div>

            {loading ? (
                <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                </div>
            ) : (
                <>
                    {/* Summary Cards */}
                    {forecast?.summary && (
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                            <div className="stats-card">
                                <p className="text-text-secondary text-sm">Total Forecast</p>
                                <p className="text-2xl font-bold mt-2">
                                    ₹{forecast.summary.total_forecasted_bill?.toFixed(0)}
                                </p>
                                <p className="text-xs text-text-secondary mt-1">
                                    Next {forecastPeriod} months
                                </p>
                            </div>
                            <div className="stats-card">
                                <p className="text-text-secondary text-sm">Average Monthly</p>
                                <p className="text-2xl font-bold mt-2">
                                    ₹{forecast.summary.average_monthly_bill?.toFixed(0)}
                                </p>
                                <div className="flex items-center gap-1 mt-1">
                                    {comparison?.change_percent > 0 ? (
                                        <ArrowUp size={14} className="text-error" />
                                    ) : (
                                        <ArrowDown size={14} className="text-success" />
                                    )}
                                    <span className={`text-xs ${comparison?.change_percent > 0 ? 'text-error' : 'text-success'
                                        }`}>
                                        {Math.abs(comparison?.change_percent || 0).toFixed(1)}% vs history
                                    </span>
                                </div>
                            </div>
                            <div className="stats-card">
                                <p className="text-text-secondary text-sm">Min Monthly</p>
                                <p className="text-2xl font-bold mt-2 text-success">
                                    ₹{forecast.summary.min_monthly?.toFixed(0)}
                                </p>
                            </div>
                            <div className="stats-card">
                                <p className="text-text-secondary text-sm">Max Monthly</p>
                                <p className="text-2xl font-bold mt-2 text-warning">
                                    ₹{forecast.summary.max_monthly?.toFixed(0)}
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Forecast Chart */}
                    <div className="glass-card p-6">
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <TrendingUp size={20} />
                            Forecasted Bills with Confidence Interval
                        </h3>
                        <div className="h-80">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={chartData}>
                                    <defs>
                                        <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                        </linearGradient>
                                        <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.2} />
                                            <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
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
                                        formatter={(value, name) => [
                                            `₹${value?.toFixed(2)}`,
                                            name === 'bill' ? 'Forecast' :
                                                name === 'lower' ? 'Lower Bound' :
                                                    'Upper Bound'
                                        ]}
                                    />
                                    <Legend />
                                    <Area
                                        type="monotone"
                                        dataKey="upper"
                                        stroke="#8b5cf6"
                                        fill="url(#colorConfidence)"
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
                                        fill="url(#colorForecast)"
                                        strokeWidth={2}
                                        name="Forecast"
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Detailed Breakdown */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Monthly Details */}
                        <div className="glass-card p-6">
                            <h3 className="text-lg font-semibold mb-4">Monthly Breakdown</h3>
                            <div className="space-y-3 max-h-80 overflow-y-auto">
                                {forecast?.forecasts?.map((f, index) => (
                                    <div key={index} className="flex items-center justify-between p-3 glass-card-light rounded-lg">
                                        <div>
                                            <p className="font-medium">{f.month_name} {f.year}</p>
                                            <p className="text-xs text-text-secondary">
                                                {f.forecasted_kwh} kWh • Season: {f.seasonal_factor}x
                                            </p>
                                        </div>
                                        <div className="text-right">
                                            <p className="font-bold">₹{f.forecasted_bill?.toFixed(0)}</p>
                                            <p className="text-xs text-text-secondary">
                                                ±{((f.upper_bound - f.lower_bound) / 2).toFixed(0)}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Seasonal Factors */}
                        <div className="glass-card p-6">
                            <h3 className="text-lg font-semibold mb-4">Seasonal Factors</h3>
                            <p className="text-sm text-text-secondary mb-4">
                                Consumption varies by season. Factor &gt; 1 means higher than average.
                            </p>
                            <div className="grid grid-cols-3 gap-2">
                                {seasonalFactors && Object.entries(seasonalFactors).map(([month, data]) => (
                                    <div
                                        key={month}
                                        className={`p-3 rounded-lg text-center ${data.factor >= 1.3 ? 'bg-error/20 border border-error/30' :
                                                data.factor >= 1.1 ? 'bg-warning/20 border border-warning/30' :
                                                    'bg-success/20 border border-success/30'
                                            }`}
                                    >
                                        <p className="text-xs text-text-secondary">{month.substring(0, 3)}</p>
                                        <p className="font-bold">{data.factor}x</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Quarterly Summary (for 12-month) */}
                    {forecast?.quarterly_summary && (
                        <div className="glass-card p-6">
                            <h3 className="text-lg font-semibold mb-4">Quarterly Summary</h3>
                            <div className="grid grid-cols-4 gap-4">
                                {Object.entries(forecast.quarterly_summary).map(([quarter, amount]) => (
                                    <div key={quarter} className="text-center p-4 glass-card-light rounded-xl">
                                        <p className="text-text-secondary">{quarter}</p>
                                        <p className="text-2xl font-bold mt-2">₹{amount?.toFixed(0)}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default Forecast;
