import { useState } from 'react';
import {
    Settings,
    Plus,
    Trash2,
    Edit2,
    Save,
    X
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { dataApi } from '../services/api';

const Appliances = () => {
    const { appliances, refreshAppliances } = useApp();
    const [editingId, setEditingId] = useState(null);
    const [editForm, setEditForm] = useState({});
    const [showAddForm, setShowAddForm] = useState(false);
    const [newAppliance, setNewAppliance] = useState({
        name: '',
        power_rating: '',
        quantity: 1,
        average_daily_hours: ''
    });
    const [loading, setLoading] = useState(false);

    const handleEdit = (appliance) => {
        setEditingId(appliance.id);
        setEditForm({ ...appliance });
    };

    const handleSaveEdit = async () => {
        setLoading(true);
        try {
            await dataApi.updateAppliance(editingId, {
                name: editForm.name,
                power_rating: parseInt(editForm.power_rating),
                quantity: parseInt(editForm.quantity),
                average_daily_hours: parseFloat(editForm.average_daily_hours)
            });
            await refreshAppliances();
            setEditingId(null);
        } catch (error) {
            console.error('Failed to update appliance:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleCancelEdit = () => {
        setEditingId(null);
        setEditForm({});
    };

    const handleDelete = async (id) => {
        if (!confirm('Delete this appliance?')) return;

        setLoading(true);
        try {
            await dataApi.deleteAppliance(id);
            await refreshAppliances();
        } catch (error) {
            console.error('Failed to delete appliance:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleAdd = async () => {
        if (!newAppliance.name || !newAppliance.power_rating) return;

        setLoading(true);
        try {
            await dataApi.addAppliance({
                name: newAppliance.name,
                power_rating: parseInt(newAppliance.power_rating),
                unit: 'W',
                quantity: parseInt(newAppliance.quantity) || 1,
                average_daily_hours: parseFloat(newAppliance.average_daily_hours) || 0
            });
            await refreshAppliances();
            setNewAppliance({ name: '', power_rating: '', quantity: 1, average_daily_hours: '' });
            setShowAddForm(false);
        } catch (error) {
            console.error('Failed to add appliance:', error);
        } finally {
            setLoading(false);
        }
    };

    // Calculate totals
    const totalMonthlyKwh = appliances.reduce((sum, app) => {
        return sum + (app.power_rating * app.average_daily_hours * (app.quantity || 1) * 30) / 1000;
    }, 0);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">Appliances</h1>
                    <p className="text-text-secondary mt-1">
                        Manage your household appliances and their usage
                    </p>
                </div>
                <button
                    onClick={() => setShowAddForm(true)}
                    className="btn-primary flex items-center gap-2"
                >
                    <Plus size={18} />
                    Add Appliance
                </button>
            </div>

            {/* Summary Card */}
            <div className="glass-card p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                        <p className="text-text-secondary text-sm">Total Appliances</p>
                        <p className="text-3xl font-bold mt-1">{appliances.length}</p>
                    </div>
                    <div>
                        <p className="text-text-secondary text-sm">Monthly Consumption</p>
                        <p className="text-3xl font-bold mt-1">{totalMonthlyKwh.toFixed(1)} kWh</p>
                    </div>
                    <div>
                        <p className="text-text-secondary text-sm">Est. Monthly Cost</p>
                        <p className="text-3xl font-bold mt-1 text-success">₹{(totalMonthlyKwh * 8).toFixed(0)}</p>
                    </div>
                </div>
            </div>

            {/* Add Form */}
            {showAddForm && (
                <div className="glass-card p-6">
                    <h3 className="text-lg font-semibold mb-4">Add New Appliance</h3>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div>
                            <label className="text-sm text-text-secondary">Name</label>
                            <input
                                type="text"
                                value={newAppliance.name}
                                onChange={(e) => setNewAppliance({ ...newAppliance, name: e.target.value })}
                                placeholder="e.g., Washing Machine"
                                className="input-field mt-1"
                            />
                        </div>
                        <div>
                            <label className="text-sm text-text-secondary">Power (Watts)</label>
                            <input
                                type="number"
                                value={newAppliance.power_rating}
                                onChange={(e) => setNewAppliance({ ...newAppliance, power_rating: e.target.value })}
                                placeholder="e.g., 500"
                                className="input-field mt-1"
                            />
                        </div>
                        <div>
                            <label className="text-sm text-text-secondary">Quantity</label>
                            <input
                                type="number"
                                value={newAppliance.quantity}
                                onChange={(e) => setNewAppliance({ ...newAppliance, quantity: e.target.value })}
                                placeholder="1"
                                className="input-field mt-1"
                            />
                        </div>
                        <div>
                            <label className="text-sm text-text-secondary">Daily Hours</label>
                            <input
                                type="number"
                                step="0.5"
                                value={newAppliance.average_daily_hours}
                                onChange={(e) => setNewAppliance({ ...newAppliance, average_daily_hours: e.target.value })}
                                placeholder="e.g., 1.5"
                                className="input-field mt-1"
                            />
                        </div>
                    </div>
                    <div className="flex gap-3 mt-4">
                        <button onClick={handleAdd} disabled={loading} className="btn-primary">
                            <Plus size={18} className="mr-2" />
                            Add
                        </button>
                        <button onClick={() => setShowAddForm(false)} className="btn-secondary">
                            Cancel
                        </button>
                    </div>
                </div>
            )}

            {/* Appliances Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {appliances.map((appliance) => {
                    const isEditing = editingId === appliance.id;
                    const monthlyKwh = (appliance.power_rating * appliance.average_daily_hours * (appliance.quantity || 1) * 30) / 1000;

                    return (
                        <div key={appliance.id} className="glass-card p-4">
                            {isEditing ? (
                                <div className="space-y-3">
                                    <input
                                        type="text"
                                        value={editForm.name}
                                        onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                                        className="input-field"
                                    />
                                    <div className="grid grid-cols-3 gap-2">
                                        <div>
                                            <label className="text-xs text-text-secondary">Power (W)</label>
                                            <input
                                                type="number"
                                                value={editForm.power_rating}
                                                onChange={(e) => setEditForm({ ...editForm, power_rating: e.target.value })}
                                                className="input-field mt-1"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-xs text-text-secondary">Qty</label>
                                            <input
                                                type="number"
                                                value={editForm.quantity}
                                                onChange={(e) => setEditForm({ ...editForm, quantity: e.target.value })}
                                                className="input-field mt-1"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-xs text-text-secondary">Hours</label>
                                            <input
                                                type="number"
                                                step="0.5"
                                                value={editForm.average_daily_hours}
                                                onChange={(e) => setEditForm({ ...editForm, average_daily_hours: e.target.value })}
                                                className="input-field mt-1"
                                            />
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        <button onClick={handleSaveEdit} className="btn-primary flex-1 py-2">
                                            <Save size={16} />
                                        </button>
                                        <button onClick={handleCancelEdit} className="btn-secondary flex-1 py-2">
                                            <X size={16} />
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <>
                                    <div className="flex items-center justify-between mb-3">
                                        <h4 className="font-semibold">{appliance.name}</h4>
                                        <div className="flex gap-1">
                                            <button
                                                onClick={() => handleEdit(appliance)}
                                                className="p-2 hover:bg-surface-light rounded-lg transition-colors"
                                            >
                                                <Edit2 size={16} className="text-text-secondary" />
                                            </button>
                                            <button
                                                onClick={() => handleDelete(appliance.id)}
                                                className="p-2 hover:bg-error/20 rounded-lg transition-colors"
                                            >
                                                <Trash2 size={16} className="text-error" />
                                            </button>
                                        </div>
                                    </div>

                                    <div className="space-y-2 text-sm">
                                        <div className="flex justify-between">
                                            <span className="text-text-secondary">Power Rating</span>
                                            <span>{appliance.power_rating} W</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-text-secondary">Quantity</span>
                                            <span>{appliance.quantity || 1}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-text-secondary">Daily Usage</span>
                                            <span>{appliance.average_daily_hours} hrs</span>
                                        </div>
                                        <div className="flex justify-between pt-2 border-t border-border">
                                            <span className="text-text-secondary">Monthly kWh</span>
                                            <span className="font-semibold text-success">{monthlyKwh.toFixed(1)}</span>
                                        </div>
                                    </div>
                                </>
                            )}
                        </div>
                    );
                })}
            </div>

            {appliances.length === 0 && (
                <div className="glass-card p-12 text-center">
                    <Settings size={48} className="mx-auto text-text-secondary mb-4" />
                    <p className="text-text-secondary">No appliances configured yet</p>
                    <button
                        onClick={() => setShowAddForm(true)}
                        className="btn-primary mt-4"
                    >
                        Add Your First Appliance
                    </button>
                </div>
            )}
        </div>
    );
};

export default Appliances;
