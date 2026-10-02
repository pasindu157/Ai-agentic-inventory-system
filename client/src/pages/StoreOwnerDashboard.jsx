import React, { useState, useEffect } from 'react';
import { Package, TrendingDown, TrendingUp, AlertTriangle, CheckCircle, LogOut } from 'lucide-react';
import api from '../services/api';
import './Dashboard.css';

const StoreOwnerDashboard = () => {
  const [recommendations, setRecommendations] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [recRes, prodRes] = await Promise.all([
          api.get('agents/recommendations/'),
          api.get('inventory/products/')
        ]);

        // Backend sorted recommendations newest first automatically? 
        // If not, sorting safely on frontend here:
        setRecommendations(recRes.data.sort((a,b) => new Date(b.created_at) - new Date(a.created_at)));
        setProducts(prodRes.data);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  };

  const getStatusIcon = (type) => {
    switch (type) {
      case 'URGENT_REORDER': return <AlertTriangle className="icon-urgent" size={24} />;
      case 'OVERSTOCK': return <TrendingDown className="icon-overstock" size={24} />;
      case 'OPTIMAL': return <CheckCircle className="icon-optimal" size={24} />;
      default: return <Package className="icon-default" size={24} />;
    }
  };

  const getStatusClass = (type) => {
    switch (type) {
      case 'URGENT_REORDER': return 'card-urgent';
      case 'OVERSTOCK': return 'card-overstock';
      case 'OPTIMAL': return 'card-optimal';
      default: return '';
    }
  };

  if (loading) {
    return <div className="dashboard-loading">Loading AI Dashboard Insights...</div>;
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div className="header-brand">
          <Package size={28} className="brand-icon"/>
          <h1>Agentic <span>Inventory</span></h1>
        </div>
        <button onClick={handleLogout} className="logout-btn">
          <LogOut size={16} /> Logout
        </button>
      </header>

      <main className="dashboard-main">
        <div className="dashboard-top-section">
          <h2>AI Recommendations</h2>
          <p>Powered by Realtime Agentic Modeling & Google Gemini</p>
        </div>

        <div className="recommendations-grid">
          {recommendations.length > 0 ? (
            recommendations.map(rec => (
              <div key={rec.id} className={`rec-card ${getStatusClass(rec.recommendation_type)}`}>
                <div className="rec-card-header">
                  {getStatusIcon(rec.recommendation_type)}
                  <h3>{rec.product_name}</h3>
                </div>
                <div className="rec-card-body">
                  <p>{rec.explanation}</p>
                </div>
                {rec.recommended_order_quantity > 0 && (
                  <div className="rec-card-footer">
                    <span className="reorder-badge">
                      Action Required: Order {rec.recommended_order_quantity} units
                    </span>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="empty-state">
              <CheckCircle size={48} />
              <h3>Your inventory is perfectly optimized!</h3>
              <p>The AI Agent has no critical insights at this time.</p>
            </div>
          )}
        </div>

        <div className="dashboard-bottom-section">
          <h2>Product Master File ({products.length} Items)</h2>
          <div className="products-table-container">
            <table className="products-table">
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Product Name</th>
                  <th>Current Stock</th>
                  <th>Reorder Level</th>
                  <th>Unit Cost</th>
                </tr>
              </thead>
              <tbody>
                {products.length > 0 ? (
                   उत्पादों.map(product => (
                    <tr key={product.id}>
                      <td>{product.sku}</td>
                      <td>{product.name}</td>
                      <td><strong>{product.current_stock}</strong></td>
                      <td>{product.reorder_level}</td>
                      <td>${Number(product.unit_cost).toFixed(2)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5">No Products found in your database.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
};

export default StoreOwnerDashboard;
