import { useState, useRef } from 'react';
import {
    Camera,
    Upload,
    Zap,
    CheckCircle,
    AlertCircle,
    Loader,
    Image as ImageIcon,
    X,
    FileText,
    Download,
    Calculator,
    DollarSign
} from 'lucide-react';

const MeterReading = () => {
    const [selectedImage, setSelectedImage] = useState(null);
    const [previewUrl, setPreviewUrl] = useState(null);
    const [reading, setReading] = useState(null);
    const [loading, setLoading] = useState(false);
    const [generatingPdf, setGeneratingPdf] = useState(false);
    const [error, setError] = useState(null);
    const [pdfResult, setPdfResult] = useState(null);
    const fileInputRef = useRef(null);

    // Form fields for bill generation
    const [customerName, setCustomerName] = useState('');
    const [customerId, setCustomerId] = useState('');
    const [previousReading, setPreviousReading] = useState('');
    const [currentReading, setCurrentReading] = useState('');
    const [tariffRate, setTariffRate] = useState(8.0);
    const [showBillForm, setShowBillForm] = useState(false);

    // Calculate units from readings
    const calculatedUnits = currentReading && previousReading
        ? Math.max(0, parseFloat(currentReading) - parseFloat(previousReading))
        : 0;

    // Calculate estimated cost
    const estimatedCost = calculatedUnits * tariffRate;
    const fixedCharges = 50;
    const taxes = estimatedCost * 0.05;
    const totalAmount = estimatedCost + fixedCharges + taxes;

    const handleImageSelect = (e) => {
        const file = e.target.files[0];
        if (file) {
            setSelectedImage(file);
            setPreviewUrl(URL.createObjectURL(file));
            setReading(null);
            setError(null);
            setPdfResult(null);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            setSelectedImage(file);
            setPreviewUrl(URL.createObjectURL(file));
            setReading(null);
            setError(null);
            setPdfResult(null);
        }
    };

    const handleDragOver = (e) => {
        e.preventDefault();
    };

    const clearImage = () => {
        setSelectedImage(null);
        setPreviewUrl(null);
        setReading(null);
        setError(null);
        setPdfResult(null);
        setShowBillForm(false);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const extractReading = async () => {
        if (!selectedImage) return;

        setLoading(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append('file', selectedImage);

            const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/ocr/quick-extract`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to extract reading');
            }

            const data = await response.json();
            setReading(data);

            // Auto-fill current reading from OCR if available
            if (data.reading) {
                setCurrentReading(data.reading);
            }
        } catch (err) {
            setError(err.message || 'Failed to extract meter reading. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const generatePdfBill = async () => {
        if (!currentReading || !previousReading) {
            setError('Please enter both previous and current readings');
            return;
        }

        setGeneratingPdf(true);
        setError(null);

        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/bill/generate-from-ocr`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    previous_reading: parseFloat(previousReading),
                    current_reading: parseFloat(currentReading),
                    units: calculatedUnits,
                    tariff_rate: tariffRate,
                    customer_name: customerName || 'Customer',
                    customer_id: customerId,
                    billing_period: new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
                    city: 'Mumbai',
                    company: 'Electricity Provider'
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to generate PDF');
            }

            const data = await response.json();
            setPdfResult(data);
        } catch (err) {
            setError(err.message || 'Failed to generate PDF bill. Please try again.');
        } finally {
            setGeneratingPdf(false);
        }
    };

    const downloadPdf = () => {
        if (pdfResult?.download_url) {
            const url = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${pdfResult.download_url}`;
            window.open(url, '_blank');
        }
    };

    return (
        <div className="meter-reading-container">
            <div className="page-header">
                <div className="header-icon">
                    <Camera size={28} />
                </div>
                <div>
                    <h1>Meter Reading OCR</h1>
                    <p>Upload a photo of your electricity meter to extract the reading and generate a bill</p>
                </div>
            </div>

            <div className="meter-content-grid">
                {/* Upload Section */}
                <div className="upload-section">
                    <div
                        className={`upload-zone ${previewUrl ? 'has-image' : ''}`}
                        onDrop={handleDrop}
                        onDragOver={handleDragOver}
                        onClick={() => !previewUrl && fileInputRef.current?.click()}
                    >
                        {previewUrl ? (
                            <div className="preview-container">
                                <img src={previewUrl} alt="Meter preview" className="meter-preview" />
                                <button className="clear-btn" onClick={clearImage}>
                                    <X size={18} />
                                </button>
                            </div>
                        ) : (
                            <div className="upload-placeholder">
                                <div className="upload-icon">
                                    <ImageIcon size={48} />
                                </div>
                                <h3>Drop your meter image here</h3>
                                <p>or click to browse</p>
                                <span className="upload-hint">Supports JPG, PNG up to 10MB</span>
                            </div>
                        )}
                    </div>

                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleImageSelect}
                        accept="image/*"
                        className="hidden"
                    />

                    {previewUrl && (
                        <div className="action-buttons">
                            <button
                                onClick={() => fileInputRef.current?.click()}
                                className="btn-secondary"
                            >
                                <Upload size={18} />
                                Change Image
                            </button>
                            <button
                                onClick={extractReading}
                                disabled={loading}
                                className="btn-primary"
                            >
                                {loading ? (
                                    <>
                                        <Loader size={18} className="animate-spin" />
                                        Extracting...
                                    </>
                                ) : (
                                    <>
                                        <Zap size={18} />
                                        Extract Reading
                                    </>
                                )}
                            </button>
                        </div>
                    )}

                    {/* Bill Generation Form */}
                    <div className="bill-form-card">
                        <div className="form-header" onClick={() => setShowBillForm(!showBillForm)}>
                            <FileText size={20} />
                            <h3>Generate PDF Bill</h3>
                            <span className="toggle-icon">{showBillForm ? '−' : '+'}</span>
                        </div>

                        {showBillForm && (
                            <div className="form-content">
                                <div className="form-row">
                                    <div className="form-group">
                                        <label>Customer Name</label>
                                        <input
                                            type="text"
                                            className="input-field"
                                            value={customerName}
                                            onChange={(e) => setCustomerName(e.target.value)}
                                            placeholder="John Doe"
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>Customer ID</label>
                                        <input
                                            type="text"
                                            className="input-field"
                                            value={customerId}
                                            onChange={(e) => setCustomerId(e.target.value)}
                                            placeholder="CUST-001"
                                        />
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label>Previous Reading</label>
                                        <input
                                            type="number"
                                            className="input-field"
                                            value={previousReading}
                                            onChange={(e) => setPreviousReading(e.target.value)}
                                            placeholder="12345"
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>Current Reading</label>
                                        <input
                                            type="number"
                                            className="input-field"
                                            value={currentReading}
                                            onChange={(e) => setCurrentReading(e.target.value)}
                                            placeholder="12567"
                                        />
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label>Tariff Rate (₹/kWh)</label>
                                        <input
                                            type="number"
                                            step="0.1"
                                            className="input-field"
                                            value={tariffRate}
                                            onChange={(e) => setTariffRate(parseFloat(e.target.value) || 0)}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>Units Consumed</label>
                                        <div className="calculated-value">
                                            <Calculator size={16} />
                                            <span>{calculatedUnits.toFixed(2)} kWh</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Cost Preview */}
                                {calculatedUnits > 0 && (
                                    <div className="cost-preview">
                                        <div className="cost-header">
                                            <DollarSign size={18} />
                                            <span>Estimated Cost</span>
                                        </div>
                                        <div className="cost-breakdown">
                                            <div className="cost-row">
                                                <span>Energy Charges</span>
                                                <span>₹{estimatedCost.toFixed(2)}</span>
                                            </div>
                                            <div className="cost-row">
                                                <span>Fixed Charges</span>
                                                <span>₹{fixedCharges.toFixed(2)}</span>
                                            </div>
                                            <div className="cost-row">
                                                <span>Taxes (5%)</span>
                                                <span>₹{taxes.toFixed(2)}</span>
                                            </div>
                                            <div className="cost-row total">
                                                <span>Total Amount</span>
                                                <span>₹{totalAmount.toFixed(2)}</span>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                <button
                                    onClick={generatePdfBill}
                                    disabled={generatingPdf || !currentReading || !previousReading}
                                    className="btn-primary generate-btn"
                                >
                                    {generatingPdf ? (
                                        <>
                                            <Loader size={18} className="animate-spin" />
                                            Generating...
                                        </>
                                    ) : (
                                        <>
                                            <FileText size={18} />
                                            Generate PDF Bill
                                        </>
                                    )}
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* Results Section */}
                <div className="results-section">
                    {error && (
                        <div className="error-card">
                            <AlertCircle size={24} />
                            <div>
                                <h4>Error</h4>
                                <p>{error}</p>
                            </div>
                        </div>
                    )}

                    {reading && (
                        <div className="result-card">
                            <div className="result-header">
                                <CheckCircle size={24} className="text-green-500" />
                                <h3>Reading Extracted</h3>
                            </div>

                            <div className="reading-display">
                                <span className="reading-label">Meter Reading</span>
                                <span className="reading-value">{reading.reading || reading.value || 'N/A'}</span>
                                <span className="reading-unit">kWh</span>
                            </div>

                            {reading.confidence && (
                                <div className="confidence-bar">
                                    <span>Confidence</span>
                                    <div className="bar-container">
                                        <div
                                            className="bar-fill"
                                            style={{ width: `${reading.confidence * 100}%` }}
                                        />
                                    </div>
                                    <span>{Math.round(reading.confidence * 100)}%</span>
                                </div>
                            )}

                            <button
                                className="btn-secondary use-reading-btn"
                                onClick={() => {
                                    setCurrentReading(reading.reading || reading.value || '');
                                    setShowBillForm(true);
                                }}
                            >
                                Use for Bill Generation
                            </button>
                        </div>
                    )}

                    {pdfResult && (
                        <div className="result-card pdf-success">
                            <div className="result-header">
                                <CheckCircle size={24} className="text-green-500" />
                                <h3>PDF Generated!</h3>
                            </div>

                            <div className="pdf-details">
                                <p><strong>Bill ID:</strong> {pdfResult.bill_id}</p>
                                <p><strong>Total Units:</strong> {pdfResult.summary?.total_units} kWh</p>
                                <p><strong>Total Amount:</strong> ₹{pdfResult.summary?.total_amount?.toFixed(2)}</p>
                            </div>

                            <button onClick={downloadPdf} className="btn-primary download-btn">
                                <Download size={18} />
                                Download PDF
                            </button>
                        </div>
                    )}

                    {!reading && !error && !pdfResult && (
                        <div className="placeholder-card">
                            <Camera size={48} className="placeholder-icon" />
                            <h3>No Reading Yet</h3>
                            <p>Upload a meter image and click "Extract Reading" to get started</p>
                        </div>
                    )}

                    <div className="tips-card">
                        <h4>Tips for Best Results</h4>
                        <ul>
                            <li>Ensure good lighting on the meter display</li>
                            <li>Hold the camera steady and parallel to the meter</li>
                            <li>Make sure the digits are clearly visible</li>
                            <li>Avoid reflections or glare on the display</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MeterReading;
