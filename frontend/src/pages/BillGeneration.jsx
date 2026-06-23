import { useState } from 'react';
import {
    FileText,
    Download,
    Eye,
    Loader2,
    CheckCircle
} from 'lucide-react';
import { billApi } from '../services/api';
import { useApp } from '../context/AppContext';

const BillGeneration = () => {
    const { appliances, tariffRate } = useApp();

    const [formData, setFormData] = useState({
        user_name: '',
        billing_period: new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
        city: 'Mumbai',
        company: 'Electricity Provider',
        previous_reading: '',
        current_reading: ''
    });

    const [preview, setPreview] = useState(null);
    const [generatedBill, setGeneratedBill] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const cities = ['Mumbai', 'Delhi', 'Chennai', 'Kolkata', 'Hyderabad', 'Bangalore', 'Pune', 'Ahmedabad'];
    const companies = ['Tata Power', 'Reliance Energy', 'Adani Power', 'NHPC', 'NTPC', 'State Electricity Board'];

    const handleInputChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const handlePreview = async () => {
        setLoading(true);
        setError(null);

        try {
            const data = {
                ...formData,
                tariff_rate: tariffRate
            };

            if (formData.previous_reading && formData.current_reading) {
                data.meter_reading = {
                    previous: parseInt(formData.previous_reading),
                    current: parseInt(formData.current_reading),
                    units: parseInt(formData.current_reading) - parseInt(formData.previous_reading)
                };
            }

            const res = await billApi.preview(data);
            setPreview(res.preview);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerate = async () => {
        setLoading(true);
        setError(null);

        try {
            const data = {
                ...formData,
                tariff_rate: tariffRate
            };

            if (formData.previous_reading && formData.current_reading) {
                data.meter_reading = {
                    previous: parseInt(formData.previous_reading),
                    current: parseInt(formData.current_reading),
                    units: parseInt(formData.current_reading) - parseInt(formData.previous_reading)
                };
            }

            const res = await billApi.generate(data);
            setGeneratedBill(res);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = () => {
        if (generatedBill?.bill_id) {
            window.open(billApi.download(generatedBill.bill_id), '_blank');
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold">Generate Bill</h1>
                <p className="text-text-secondary mt-1">
                    Create a detailed PDF electricity bill
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Form */}
                <div className="space-y-6">
                    <div className="glass-card p-6">
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <FileText size={20} />
                            Bill Details
                        </h3>

                        <div className="space-y-4">
                            <div>
                                <label className="text-sm text-text-secondary">Customer Name</label>
                                <input
                                    type="text"
                                    value={formData.user_name}
                                    onChange={(e) => handleInputChange('user_name', e.target.value)}
                                    placeholder="Enter customer name"
                                    className="input-field mt-1"
                                />
                            </div>

                            <div>
                                <label className="text-sm text-text-secondary">Billing Period</label>
                                <input
                                    type="text"
                                    value={formData.billing_period}
                                    onChange={(e) => handleInputChange('billing_period', e.target.value)}
                                    placeholder="e.g., December 2024"
                                    className="input-field mt-1"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-sm text-text-secondary">City</label>
                                    <select
                                        value={formData.city}
                                        onChange={(e) => handleInputChange('city', e.target.value)}
                                        className="input-field mt-1"
                                    >
                                        {cities.map((city) => (
                                            <option key={city} value={city}>{city}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="text-sm text-text-secondary">Company</label>
                                    <select
                                        value={formData.company}
                                        onChange={(e) => handleInputChange('company', e.target.value)}
                                        className="input-field mt-1"
                                    >
                                        {companies.map((company) => (
                                            <option key={company} value={company}>{company}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            <div className="border-t border-border pt-4 mt-4">
                                <p className="text-sm text-text-secondary mb-3">Meter Readings (Optional)</p>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-xs text-text-secondary">Previous Reading</label>
                                        <input
                                            type="number"
                                            value={formData.previous_reading}
                                            onChange={(e) => handleInputChange('previous_reading', e.target.value)}
                                            placeholder="e.g., 15000"
                                            className="input-field mt-1"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-xs text-text-secondary">Current Reading</label>
                                        <input
                                            type="number"
                                            value={formData.current_reading}
                                            onChange={(e) => handleInputChange('current_reading', e.target.value)}
                                            placeholder="e.g., 15250"
                                            className="input-field mt-1"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="flex gap-3 mt-6">
                            <button
                                onClick={handlePreview}
                                disabled={loading}
                                className="btn-secondary flex-1 flex items-center justify-center gap-2"
                            >
                                <Eye size={18} />
                                Preview
                            </button>
                            <button
                                onClick={handleGenerate}
                                disabled={loading}
                                className="btn-primary flex-1 flex items-center justify-center gap-2"
                            >
                                {loading ? (
                                    <Loader2 className="animate-spin" size={18} />
                                ) : (
                                    <FileText size={18} />
                                )}
                                Generate PDF
                            </button>
                        </div>

                        {error && (
                            <div className="mt-4 p-3 bg-error/10 border border-error/30 rounded-lg text-error text-sm">
                                {error}
                            </div>
                        )}
                    </div>

                    {/* Appliances Summary */}
                    <div className="glass-card p-6">
                        <h3 className="text-lg font-semibold mb-4">Configured Appliances</h3>
                        <div className="space-y-2 max-h-60 overflow-y-auto">
                            {appliances.map((app) => (
                                <div key={app.id} className="flex justify-between p-2 glass-card-light rounded-lg">
                                    <span>{app.name}</span>
                                    <span className="text-text-secondary">{app.power_rating}W × {app.average_daily_hours}hrs</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Preview / Result */}
                <div className="space-y-6">
                    {generatedBill ? (
                        <div className="glass-card p-6">
                            <div className="text-center mb-6">
                                <div className="w-16 h-16 rounded-full gradient-success flex items-center justify-center mx-auto">
                                    <CheckCircle size={32} className="text-white" />
                                </div>
                                <h3 className="text-xl font-semibold mt-4">Bill Generated!</h3>
                                <p className="text-text-secondary mt-1">Bill ID: {generatedBill.bill_id}</p>
                            </div>

                            <div className="glass-card-light p-4 rounded-xl mb-6">
                                <div className="space-y-2">
                                    <div className="flex justify-between">
                                        <span className="text-text-secondary">Total Units</span>
                                        <span>{generatedBill.summary?.total_units} kWh</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-text-secondary">Energy Charges</span>
                                        <span>₹{generatedBill.summary?.energy_charges}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-text-secondary">Fixed Charges</span>
                                        <span>₹{generatedBill.summary?.fixed_charges}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-text-secondary">Taxes</span>
                                        <span>₹{generatedBill.summary?.taxes}</span>
                                    </div>
                                    <div className="flex justify-between pt-2 border-t border-border font-bold text-lg">
                                        <span>Total Amount</span>
                                        <span className="text-success">₹{generatedBill.summary?.total_amount}</span>
                                    </div>
                                </div>
                            </div>

                            <button
                                onClick={handleDownload}
                                className="btn-primary w-full flex items-center justify-center gap-2"
                            >
                                <Download size={20} />
                                Download PDF
                            </button>
                        </div>
                    ) : preview ? (
                        <div className="glass-card p-6">
                            <h3 className="text-lg font-semibold mb-4">Bill Preview</h3>

                            <div className="space-y-4">
                                <div className="glass-card-light p-4 rounded-xl">
                                    <p className="text-text-secondary text-sm">Customer</p>
                                    <p className="font-medium">{preview.user_name || 'Not specified'}</p>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="glass-card-light p-4 rounded-xl">
                                        <p className="text-text-secondary text-sm">Period</p>
                                        <p className="font-medium">{preview.billing_period}</p>
                                    </div>
                                    <div className="glass-card-light p-4 rounded-xl">
                                        <p className="text-text-secondary text-sm">Tariff</p>
                                        <p className="font-medium">₹{preview.tariff_rate}/kWh</p>
                                    </div>
                                </div>

                                <div className="glass-card-light p-4 rounded-xl">
                                    <p className="text-lg font-semibold mb-3">Consumption</p>
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="text-text-secondary">
                                                <th className="text-left pb-2">Appliance</th>
                                                <th className="text-right pb-2">kWh</th>
                                                <th className="text-right pb-2">Cost</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {preview.appliances?.map((app, i) => (
                                                <tr key={i}>
                                                    <td className="py-1">{app.name}</td>
                                                    <td className="text-right">{app.monthly_kwh}</td>
                                                    <td className="text-right">₹{app.cost}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>

                                <div className="gradient-primary p-4 rounded-xl text-white">
                                    <div className="flex justify-between items-center">
                                        <span className="text-lg">Total Amount</span>
                                        <span className="text-3xl font-bold">₹{preview.summary?.total_amount?.toFixed(2)}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="glass-card p-6 text-center">
                            <FileText size={48} className="mx-auto text-text-secondary mb-4" />
                            <p className="text-text-secondary">
                                Fill in the bill details and click "Preview" to see a summary or "Generate PDF" to create the bill
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default BillGeneration;