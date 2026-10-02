import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import api from '../services/api';
import './AddProductModal.css';

const AddProductModal = ({ isOpen, onClose, onProductAdded }) => {
  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    current_stock: 0,
    reorder_level: 10,
    unit_cost: 0.00,
    description: '',
    supplier: ''
  });
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Automatically fetch the owner's suppliers when the modal opens
  useEffect(() => {
    if (isOpen) {
      const fetchSuppliers = async () => {
        try {
          const token = localStorage.getItem('access_token');
          const res = await api.get('inventory/suppliers/', {
             headers: { Authorization: `Bearer ${token}` }
          });
          setSuppliers(res.data);
        } catch (err) {
          console.error("Failed to fetch suppliers", err);
        }
      };
      fetchSuppliers();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // --- STRICT Frontend Validation ---
    if (!formData.name || formData.name.trim().length < 2) {
      setError("Product Name must be at least 2 characters.");
      setLoading(false); return;
    }
    if (!formData.sku || formData.sku.trim().length < 2) {
      setError("SKU (Barcode) must be at least 2 characters.");
      setLoading(false); return;
    }
    if (formData.current_stock < 0 || formData.current_stock === '') {
      setError("Initial Stock cannot be negative.");
      setLoading(false); return;
    }
    if (formData.reorder_level < 0 || formData.reorder_level === '') {
      setError("Low Stock Warning Level cannot be negative.");
      setLoading(false); return;
    }
    if (formData.unit_cost < 0 || formData.unit_cost === '') {
      setError("Unit Cost cannot be negative.");
      setLoading(false); return;
    }
    // ------------------------------------

    try {
      const payload = { ...formData };
      
      // Django's ForeignKey expects a valid integer or strictly `null` (not an empty string)
      if (!payload.supplier) {
        payload.supplier = null;
      }

      const token = localStorage.getItem('access_token');
      const response = await api.post('inventory/products/', payload, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      onProductAdded(response.data); 
      onClose();
      // Master reset
      setFormData({ name: '', sku: '', current_stock: 0, reorder_level: 10, unit_cost: 0, description: '', supplier: '' });
    } catch (err) {
      console.error(err);
      setError('Failed to add product. Please check your inputs (SKU must be unique).');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Add New Product</h2>
          <button onClick={onClose} className="close-btn"><X size={20} /></button>
        </div>

        {error && <div className="modal-error">{error}</div>}

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-row">
            <div className="form-group">
              <label>Product Name</label>
              <input type="text" name="name" required value={formData.name} onChange={handleChange} placeholder="e.g. Wireless Mouse" />
            </div>
            <div className="form-group">
              <label>SKU (Barcode)</label>
              <input type="text" name="sku" required value={formData.sku} onChange={handleChange} placeholder="e.g. MS-001" />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Initial Stock</label>
              <input type="number" name="current_stock" required min="0" value={formData.current_stock} onChange={handleChange} />
            </div>
            <div className="form-group">
              <label>Low Stock Warning Level</label>
              <input type="number" name="reorder_level" required min="0" value={formData.reorder_level} onChange={handleChange} />
            </div>
            <div className="form-group">
              <label>Unit Cost ($)</label>
              <input type="number" step="0.01" name="unit_cost" required min="0" value={formData.unit_cost} onChange={handleChange} />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Supplier (Optional)</label>
              <select name="supplier" value={formData.supplier} onChange={handleChange} className="modal-select">
                <option value="">No Supplier / Produced In-House</option>
                {suppliers.map(sup => (
                  <option key={sup.id} value={sup.id}>{sup.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Description</label>
              <textarea 
                name="description" 
                value={formData.description} 
                onChange={handleChange} 
                placeholder="Product attributes and details..."
                rows="3"
                className="modal-textarea"
              />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" onClick={onClose} className="btn-cancel">Cancel</button>
            <button type="submit" className="btn-save" disabled={loading}>
              {loading ? 'Saving...' : 'Save Product'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddProductModal;
