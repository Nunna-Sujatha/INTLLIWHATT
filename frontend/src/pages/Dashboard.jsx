import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Zap,
    Brain,
    Camera,
    MessageSquare,
    ArrowRight,
    Activity,
    Shield,
    Clock,
    ChevronDown,
    ChevronUp,
    Sliders,
    TrendingUp,
    TrendingDown,
    Minus,
    
  Layers,

  BarChart3,
  FileText
} from 'lucide-react';
import {
    PieChart,
    Pie,
    Cell,
    Tooltip,
    ResponsiveContainer
} from 'recharts';

/* ================= APPLIANCE CONFIG ================= */
const APPLIANCES = [
    { id: 'ac', name: 'AC', emoji: '❄️', power: 1500, maxCount: 5 },
    { id: 'fan', name: 'Fan', emoji: '🌀', power: 75, maxCount: 6 },
    { id: 'fridge', name: 'Refrigerator', emoji: '🧊', power: 200, maxCount: 1 },
    { id: 'tv', name: 'Television', emoji: '📺', power: 150, maxCount: 3 },
    { id: 'monitor', name: 'Monitor', emoji: '🖥️', power: 40, maxCount: 3 },
    { id: 'tube', name: 'Tube Light', emoji: '💡', power: 20, maxCount: 20 },
];

const BASELINE = {
    ac: { hours: 4, count: 1 },
    fan: { hours: 6, count: 2 },
    fridge: { hours: 24, count: 1 },
    tv: { hours: 4, count: 1 },
    monitor: { hours: 6, count: 1 },
    tube: { hours: 5, count: 4 }
};

/* ================= COMPONENT ================= */
const Homepage = () => {
    const navigate = useNavigate();
    const [showDetails, setShowDetails] = useState(false);
    const [tariffRate, setTariffRate] = useState(8);
    const [state, setState] = useState(BASELINE);

    /* ================= CALCULATION ================= */
    const simulatorResult = useMemo(() => {
        let totalKwh = 0;
        let baselineKwh = 0;

        APPLIANCES.forEach(app => {
            totalKwh +=
                (app.power * state[app.id].hours * state[app.id].count * 30) / 1000;
            baselineKwh +=
                (app.power * BASELINE[app.id].hours * BASELINE[app.id].count * 30) / 1000;
        });

        const bill = totalKwh * tariffRate;
        const baseBill = baselineKwh * tariffRate;
        const diff = bill - baseBill;

        return {
            totalKwh: Math.round(totalKwh),
            bill: Math.round(bill),
            baseBill: Math.round(baseBill),
            diff: Math.round(diff),
            percent: baseBill ? ((diff / baseBill) * 100).toFixed(1) : '0.0',
            inc: diff > 0,
            dec: diff < 0
        };
    }, [state, tariffRate]);

    /* ================= STATIC DATA ================= */
    const consumptionBreakdown = [
        { name: 'AC', value: 45, color: '#3b82f6' },
        { name: 'Fridge', value: 20, color: '#8b5cf6' },
        { name: 'Fans', value: 15, color: '#06b6d4' },
        { name: 'TV', value: 10, color: '#10b981' },
        { name: 'Others', value: 10, color: '#f59e0b' },
    ];

    const features = [
        { icon: Brain, title: 'AI Prediction', description: 'Accurate bill forecasts using ML models', action: '/prediction', color: 'bg-blue-500' },
        { icon: Camera, title: 'OCR Reader', description: 'Extract readings from meter photos', action: '/meter-reading', color: 'bg-purple-500' },
        { icon: MessageSquare, title: 'AI Assistant', description: 'Get personalized energy-saving tips', action: '/chatbot', color: 'bg-green-500' }
    ];

    const capabilities = [
        { icon: Activity, title: 'Real-time Analysis', desc: 'Instant power consumption breakdown' },
        { icon: Shield, title: 'Smart Forecasting', desc: 'High accuracy bill predictions' },
        { icon: Clock, title: 'Seasonal Insights', desc: 'Summer/winter adjustments' }
    ];

    return (
        <div className="homepage-container">

            {/* ================= HERO ================= */}
            <section className="hero-section">
                <div className="hero-content">
                    <h1 className="hero-title">
                        <span className="gradient-text">Predict Your Bills with AI</span>
                    </h1>
                    <p className="hero-subtitle">
                        Stop guessing your monthly expenses. Our AI analyzes your consumption patterns to forecast bills accurately.
                    </p>
                    <div className="hero-actions">
                        <button onClick={() => navigate('/prediction')} className="btn-primary hero-cta">
                            <Zap size={20} /> Start Prediction <ArrowRight size={18} />
                        </button>
                    </div>
                    <button onClick={() => navigate('/meter-reading')} className="hero-secondary-link">
                        <Camera size={16} /> Or scan your meter reading
                    </button>
                </div>
            </section>

            {/* ================= WHAT-IF SIMULATOR ================= */}
            <section className="simulator-section">
                <div className="section-divider" />
                <div className="simulator-header">
                    <div className="simulator-icon">
                        <Sliders size={28} className="text-white" />
                    </div>
                    <div>
                        <h2 className="section-title">What-If Scenario Simulator</h2>
                        <p className="simulator-subtitle">
                            Adjust the sliders to see how changes affect your bill instantly
                        </p>
                    </div>
                </div>

                <div className="simulator-card">
                    <div className="simulator-controls">

                        {APPLIANCES.map(app => (
                            <div key={app.id} className="grid grid-cols-1 md:grid-cols-3 gap-4 slider-group">

                                {/* Usage */}
                                <div className="md:col-span-2">
                                    <div className="slider-header">
                                        <label className="slider-label">
                                            <span className="slider-emoji">{app.emoji}</span>
                                            {app.name} Usage
                                        </label>
                                        <span className="slider-value">
                                            {state[app.id].hours} hrs/day
                                        </span>
                                    </div>
                                    <input
                                        type="range"
                                        min="0"
                                        max="24"
                                        value={state[app.id].hours}
                                        onChange={(e) =>
                                            setState({
                                                ...state,
                                                [app.id]: { ...state[app.id], hours: +e.target.value }
                                            })
                                        }
                                        className="simulator-slider"
                                    />
                                    <div className="slider-range">
                                        <span>0 hrs</span>
                                        <span>24 hrs</span>
                                    </div>
                                </div>

                                {/* Count */}
                                <div>
                                    <div className="slider-header">
                                        <label className="slider-label">
                                            Number of {app.name}s
                                        </label>
                                        <span className="slider-value">
                                            {state[app.id].count}
                                        </span>
                                    </div>
                                    <input
                                        type="range"
                                        min="1"
                                        max={app.maxCount}
                                        value={state[app.id].count}
                                        onChange={(e) =>
                                            setState({
                                                ...state,
                                                [app.id]: { ...state[app.id], count: +e.target.value }
                                            })
                                        }
                                        className="simulator-slider"
                                    />
                                    <div className="slider-range">
                                        <span>1</span>
                                        <span>{app.maxCount}</span>
                                    </div>
                                </div>

                            </div>
                        ))}

                        {/* Tariff */}
                        <div className="slider-group">
                            <div className="slider-header">
                                <label className="slider-label">💰 Tariff Rate</label>
                                <span className="slider-value">₹{tariffRate}/kWh</span>
                            </div>
                            <input
                                type="range"
                                min="3"
                                max="15"
                                step="0.5"
                                value={tariffRate}
                                onChange={(e) => setTariffRate(+e.target.value)}
                                className="simulator-slider"
                            />
                            <div className="slider-range">
                                <span>₹3</span>
                                <span>₹15</span>
                            </div>
                        </div>
                    </div>

                    {/* Results */}
                    <div className="simulator-results">
                        <div className="result-card main-result">
                            <p className="result-label">Estimated Monthly Bill</p>
                            <p className="result-value">₹{simulatorResult.bill}</p>
                            <p className="result-subtext">{simulatorResult.totalKwh} kWh consumption</p>
                        </div>

                        <div className="result-card comparison-result">
                            <p className="result-label">Compared to Baseline</p>
                            <div className={`comparison-badge ${simulatorResult.inc ? 'increase' : simulatorResult.dec ? 'decrease' : 'neutral'}`}>
                                {simulatorResult.inc ? <TrendingUp size={18} /> : simulatorResult.dec ? <TrendingDown size={18} /> : <Minus size={18} />}
                                ₹{simulatorResult.diff} ({simulatorResult.percent}%)
                            </div>
                            <p className="baseline-text">
                                Baseline: ₹{simulatorResult.baseBill}/month
                            </p>
                        </div>
                    </div>

                    <button onClick={() => navigate('/prediction')} className="simulator-cta">
                        <Zap size={18} /> Get Detailed Prediction <ArrowRight size={16} />
                    </button>
                </div>
            </section>

            {/* ================= FEATURES ================= */}
            <section className="features-section">
                <div className="section-divider" />
                <h2 className="section-title">What You Can Do</h2>
                <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12">

                    {features.map((f, i) => (
                        <div key={i} onClick={() => navigate(f.action)} className="feature-card">
                            <div className={`feature-icon ${f.color}`}>
                                <f.icon size={28} className="text-white" />
                            </div>
                            <h3 className="feature-title">{f.title}</h3>
                            <p className="feature-description">{f.description}</p>
                            <span className="feature-link">
                                Try Now <ArrowRight size={14} />
                            </span>
                        </div>
                    ))}
                </div>
            </section>

          {/* ================= PROJECT INSIGHTS ================= */}
{/* ================= ML & SYSTEM OVERVIEW ================= */}
<section className="features-section">
  <div className="section-divider" />

  {/* ===== ML MODELS + TECH STACK ===== */}
  {/* ===== ML MODELS + TECH STACK ===== */}
<div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12">

  {/* Machine Learning Models */}
  <div className="feature-card">
    <div className="feature-icon bg-blue-500">
      <Brain size={26} className="text-white" />
    </div>
    <h3 className="feature-title">Machine Learning Models</h3>
    <p className="feature-description">Trained on 45,347 records</p>

    <div className="mt-4 text-sm">
      <strong>Stacking Regressor</strong>
      <span className="ml-2 text-green-400">R² 99.9%</span>
      <ul className="list-disc pl-4 mt-2 opacity-80">
        <li>Linear Regression</li>
        <li>Ridge Regression</li>
        <li>Random Forest</li>
        <li>Meta-learner Optimization</li>
      </ul>
      <p className="text-xs mt-1 opacity-60">MAE: 8.5 · RMSE: 12.4</p>
    </div>

    <div className="mt-4 text-sm">
      <strong>MLP Neural Network</strong>
      <span className="ml-2 text-green-400">R² 99.8%</span>
      <ul className="list-disc pl-4 mt-2 opacity-80">
        <li>128-64-32 Hidden Layers</li>
        <li>Batch Normalization</li>
        <li>Dropout Regularization</li>
        <li>Early Stopping</li>
      </ul>
      <p className="text-xs mt-1 opacity-60">
        TensorFlow / Keras · GPU Optimized
      </p>
    </div>
  </div>

  {/* Technology Stack */}
  <div className="feature-card">
    <div className="feature-icon bg-purple-500">
      <Layers size={26} className="text-white" />
    </div>
    <h3 className="feature-title">Technology Stack</h3>
    <p className="feature-description">Modern full-stack architecture</p>

    <div className="grid grid-cols-2 gap-4 mt-4 text-sm opacity-80">
      <div>
        <strong>Frontend</strong>
        <ul className="list-disc pl-4 mt-1">
          <li>React 18 + Vite</li>
          <li>Tailwind CSS</li>
          <li>Recharts</li>
          <li>React Router</li>
        </ul>
      </div>

      <div>
        <strong>Backend</strong>
        <ul className="list-disc pl-4 mt-1">
          <li>Python (Flask)</li>
          <li>Scikit-learn</li>
          <li>TensorFlow / Keras</li>
          <li>REST APIs</li>
        </ul>
      </div>

      <div>
        <strong>OCR</strong>
        <ul className="list-disc pl-4 mt-1">
          <li>OpenCV</li>
          <li>EasyOCR</li>
          <li>Image Processing</li>
        </ul>
      </div>

      <div>
        <strong>PDF & Reports</strong>
        <ul className="list-disc pl-4 mt-1">
          <li>ReportLab</li>
          <li>Custom Templates</li>
          <li>Instant Download</li>
        </ul>
      </div>
    </div>
  </div>

</div>


  {/* ===== HOW IT WORKS ===== */}
  <div className="mt-16">
    <h2 className="section-title">How It Works</h2>
    <p className="section-subtitle">
      Simple 4-step process to predict your electricity bill
    </p>

    <div className="features-grid">
      <div className="feature-card">
        <div className="feature-icon bg-indigo-500">
          <Zap size={24} className="text-white" />
        </div>
        <h3 className="feature-title">Enter Appliances</h3>
        <p className="feature-description">
          Configure appliance count and daily usage hours
        </p>
      </div>

      <div className="feature-card">
        <div className="feature-icon bg-green-500">
          <Brain size={24} className="text-white" />
        </div>
        <h3 className="feature-title">Select ML Model</h3>
        <p className="feature-description">
          Choose Stacking Regressor or MLP Neural Network
        </p>
      </div>

      <div className="feature-card">
        <div className="feature-icon bg-blue-500">
          <BarChart3 size={24} className="text-white" />
        </div>
        <h3 className="feature-title">Get Prediction</h3>
        <p className="feature-description">
          Receive accurate bill prediction with breakdown
        </p>
      </div>

      <div className="feature-card">
        <div className="feature-icon bg-orange-500">
          <FileText size={24} className="text-white" />
        </div>
        <h3 className="feature-title">Download PDF</h3>
        <p className="feature-description">
          Auto-generated bill forecast & savings report
        </p>
      </div>
    </div>
  </div>
</section>


            {/* ================= CAPABILITIES ================= */}
            <section className="capabilities-section">
                <div className="section-divider" />
                <h2 className="section-title">Understand Your Usage</h2>
                <button onClick={() => setShowDetails(!showDetails)} className="expand-button">
                    {showDetails ? <>Hide Details <ChevronUp size={18} /></> : <>Show Details <ChevronDown size={18} /></>}
                </button>

                {showDetails && (
                    <div className="capabilities-grid">
                        {capabilities.map((c, i) => (
                            <div key={i} className="capability-card">
                                <c.icon size={22} className="text-blue-400" />
                                <div>
                                    <h4 className="capability-title">{c.title}</h4>
                                    <p className="capability-desc">{c.desc}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </section>
        </div>
    );
};

export default Homepage;