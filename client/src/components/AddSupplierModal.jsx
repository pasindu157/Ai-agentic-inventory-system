import React, { useState } from 'react';
import { X } from 'lucide-react';
import api from '../services/api';
import './AddProductModal.css';

const AddSupplierModal = ({ isOpen, onClose, onSupplierAdded }) => {
  const [formData, setFormData] = useState({
    name: '',
    contact_email: '',
    contact_phone: '',
    lead_time_days: 7
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

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
      setError("Supplier Name must be at least 2 characters.");
      setLoading(false); return;
    }
    
    if (formData.contact_email) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.contact_email)) {
        setError("Please enter a valid email address.");
        setLoading(false); return;
      }
    }

    if (formData.contact_phone) {
      // Enforce the 10-digit Sri Lankan phone number limitation
      const phoneRegex = /^\d{10}$/;
      if (!phoneRegex.test(formData.contact_phone)) {
        setError("Sri Lankan phone numbers must be exactly 10 digits containing only numbers (e.g. 0765432134).");
        setLoading(false); return;
      }
    }

    if (formData.lead_time_days < 0 || formData.lead_time_days === '') {
      setError("Average Lead Time cannot be a negative value.");
      setLoading(false); return;
    }
    // ------------------------------------

    try {
      const token = localStorage.getItem('access_token');
      // POST securely using the token
      const response = await api.post('inventory/suppliers/', formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      onSupplierAdded(response.data); 
      onClose();
      
      // Reset form on success
      setFormData({ name: '', contact_email: '', contact_phone: '', lead_time_days: 7 });
    } catch (err) {
      console.error(err);
      setError('Failed to save supplier. Please check inputs.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{maxWidth: '500px'}}>
        <div className="modal-header">
          <h2>Add New Supplier</h2>
          <button onClick={onClose} className="close-btn"><X size={20} /></button>
        </div>

        {error && <div className="modal-error">{error}</div>}

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-row">
            <div className="form-group">
              <label>Supplier / Vendor Name</label>
              <input type="text" name="name" required value={formData.name} onChange={handleChange} placeholder="e.g. Apex Logistics" />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Contact Email (Optional)</label>
              <input type="email" name="contact_email" value={formData.contact_email} onChange={handleChange} placeholder="sales@apex.com" />
            </div>
            <div className="form-group">
              <label>Phone (Optional)</label>
              <input type="text" name="contact_phone" value={formData.contact_phone} onChange={handleChange} placeholder="+1-800-456-7890" />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Average Lead Time (Days)</label>
              <input type="number" name="lead_time_days" required min="1" value={formData.lead_time_days} onChange={handleChange} />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" onClick={onClose} className="btn-cancel">Cancel</button>
            <button type="submit" className="btn-save" disabled={loading}>
              {loading ? 'Saving...' : 'Save Supplier'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddSupplierModal;
