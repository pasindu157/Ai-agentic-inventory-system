import React, { useState, useEffect } from 'react';
import { X, Save } from 'lucide-react';
import api from '../services/api';
import './AddProductModal.css';

const EditProductModal = ({ isOpen, onClose, product, onProductUpdated }) => {
  const [formData, setFormData] = useState({
    name: '', sku: '', current_stock: 0, reorder_level: 10, unit_cost: 0.00, description: '', supplier: ''
  });
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Dynamically initialize the form the exact moment the product prop changes
  useEffect(() => {
    if (product) {
      setFormData({
        name: product.name || '',
        sku: product.sku || '',
        current_stock: product.current_stock ?? 0,
        reorder_level: product.reorder_level ?? 0,
        unit_cost: product.unit_cost ?? 0.00,
        description: product.description || '',
        supplier: product.supplier || ''
      });
    }
  }, [product, isOpen]);

  // Acquire supplier mappings quietly behind the scenes
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

  if (!isOpen || !product) return null;

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // --- STRICT Frontend Validation ---
    if (!formData.name || formData.name.trim().length < 2) {
      setError("Product Name must be at least 2 characters."); setLoading(false); return;
    }
    if (!formData.sku || formData.sku.trim().length < 2) {
      setError("SKU (Barcode) must be at least 2 characters."); setLoading(false); return;
    }
    if (formData.current_stock < 0 || formData.current_stock === '') {
      setError("Initial Stock cannot be negative."); setLoading(false); return;
    }
    if (formData.reorder_level < 0 || formData.reorder_level === '') {
      setError("Low Stock Warning Level cannot be negative."); setLoading(false); return;
    }
    if (formData.unit_cost < 0 || formData.unit_cost === '') {
      setError("Unit Cost cannot be negative."); setLoading(false); return;
    }

    try {
      const payload = { ...formData };
      if (!payload.supplier) {
        payload.supplier = null;
      }

      const token = localStorage.getItem('access_token');
      // Execute a dynamic PATCH instead of POST, updating ONLY the modified columns in Django
      const response = await api.patch(`inventory/products/${product.id}/`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      onProductUpdated(response.data); 
      onClose();
    } catch (err) {
      console.error(err);
      setError('Failed to update product details. Ensure your SKU remains unique.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Edit Stock Details: {product.name}</h2>
          <button onClick={onClose} className="close-btn"><X size={20} /></button>
        </div>

        {error && <div className="modal-error">{error}</div>}

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-row">
            <div className="form-group">
              <label>Product Name</label>
              <input type="text" name="name" required value={formData.name} onChange={handleChange} />
            </div>
            <div className="form-group">
              <label>SKU (Barcode)</label>
              <input type="text" name="sku" required value={formData.sku} onChange={handleChange} />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Current Stock Quantity</label>
              <input type="number" name="current_stock" required min="0" value={formData.current_stock} onChange={handleChange} />
            </div>
            <div className="form-group">
              <label>Low Stock Warning Limit</label>
              <input type="number" name="reorder_level" required min="0" value={formData.reorder_level} onChange={handleChange} />
            </div>
            <div className="form-group">
              <label>Unit Cost ($)</label>
              <input type="number" step="0.01" name="unit_cost" required min="0" value={formData.unit_cost} onChange={handleChange} />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Supplier Override</label>
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
              <label>Description Details</label>
              <textarea 
                name="description" 
                value={formData.description} 
                onChange={handleChange} 
                rows="3"
                className="modal-textarea"
              />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" onClick={onClose} className="btn-cancel">Cancel</button>
            <button type="submit" className="btn-save" disabled={loading} style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
              {loading ? 'Committing...' : <><Save size={16}/> Save Updates</>}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditProductModal;
