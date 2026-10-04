import React, { useState, useEffect } from 'react';
import { DollarSign, Package, AlertTriangle, CheckCircle, TrendingUp, RefreshCw, BarChart2, PieChart, Layers } from 'lucide-react';
import api from '../services/api';
import './Dashboard.css';

const StoreStatistics = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const response = await api.get('inventory/statistics/', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      console.error("Failed to fetch store statistics:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading) {
    return <div className="dashboard-loading">Calculating Inventory Analytics & Stats...</div>;
  }

  if (!stats) {
    return <div className="dashboard-loading">Failed to load statistics. Please try refreshing.</div>;
  }

  const { health } = stats;

  return (
    <div style={{ padding: '0' }}>
      {/* 4 Executive KPI Stat Cards */}
      <div className="metrics-grid">
        <div className="metric-card" style={{ borderLeft: '4px solid var(--primary)' }}>
          <div className="metric-header">
            <span>Total Capital Valuation</span>
            <DollarSign className="icon-optimal" size={24} />
          </div>
          <div className="metric-value" style={{ color: 'var(--primary)' }}>
            ${stats.total_valuation.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
          <p className="metric-subtext">Total capital tied up in active inventory</p>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span>Total Units in Stock</span>
            <Package className="icon-default" size={24} style={{ color: '#3b82f6' }} />
          </div>
          <div className="metric-value">{stats.total_units_in_stock.toLocaleString()}</div>
          <p className="metric-subtext">Across {stats.total_products_count} active product SKUs</p>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span>Average Unit Cost</span>
            <TrendingUp className="icon-overstock" size={24} />
          </div>
          <div className="metric-value">${stats.avg_unit_cost.toFixed(2)}</div>
          <p className="metric-subtext">Weighted average cost per physical item</p>
        </div>

        <div className="metric-card" style={{ borderLeft: health.urgent_reorder_count > 0 ? '4px solid #ef4444' : '4px solid #10b981' }}>
          <div className="metric-header">
            <span>Stock Health Status</span>
            {health.urgent_reorder_count > 0 ? (
              <AlertTriangle className="icon-urgent" size={24} />
            ) : (
              <CheckCircle className="icon-optimal" size={24} />
            )}
          </div>
          <div className="metric-value" style={{ color: health.urgent_reorder_count > 0 ? '#dc2626' : '#16a34a' }}>
            {health.optimal_pct}% Optimal
          </div>
          <p className="metric-subtext">
            {health.urgent_reorder_count} Urgent • {health.low_stock_count} Low • {health.optimal_count} Optimal
          </p>
        </div>
      </div>

      {/* Visual Stock Health Ratio Progress Bar */}
      <div className="dashboard-card" style={{ background: 'white', padding: '1.75rem', borderRadius: '14px', border: '1px solid #e2e8f0', marginBottom: '2.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ margin: 0, fontSize: '1.2rem', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <PieChart size={20} style={{ color: 'var(--primary)' }} /> Inventory Health Ratio Distribution
          </h3>
          <span style={{ fontSize: '0.85rem', color: '#64748b' }}>{stats.total_products_count} Total Active Products</span>
        </div>

        {/* Stacked Progress Bar */}
        <div style={{ display: 'flex', height: '24px', borderRadius: '9999px', overflow: 'hidden', background: '#f1f5f9', margin: '1rem 0' }}>
          {health.optimal_pct > 0 && (
            <div 
              style={{ width: `${health.optimal_pct}%`, background: '#10b981', transition: 'width 0.4s' }} 
              title={`Optimal Stock: ${health.optimal_count} items (${health.optimal_pct}%)`}
            />
          )}
          {health.low_pct > 0 && (
            <div 
              style={{ width: `${health.low_pct}%`, background: '#f59e0b', transition: 'width 0.4s' }} 
              title={`Low Stock: ${health.low_stock_count} items (${health.low_pct}%)`}
            />
          )}
          {health.urgent_pct > 0 && (
            <div 
              style={{ width: `${health.urgent_pct}%`, background: '#ef4444', transition: 'width 0.4s' }} 
              title={`Urgent Reorder: ${health.urgent_reorder_count} items (${health.urgent_pct}%)`}
            />
          )}
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap', marginTop: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
            <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#10b981' }} />
            <span>Optimal Stock: <strong>{health.optimal_count} ({health.optimal_pct}%)</strong></span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
            <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#f59e0b' }} />
            <span>Low Stock Warning: <strong>{health.low_stock_count} ({health.low_pct}%)</strong></span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
            <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ef4444' }} />
            <span>Urgent Reorder Critical: <strong>{health.urgent_reorder_count} ({health.urgent_pct}%)</strong></span>
          </div>
        </div>
      </div>

      {/* Top 5 Most Valuable Products Section */}
      <div className="dashboard-card" style={{ background: 'white', padding: '1.75rem', borderRadius: '14px', border: '1px solid #e2e8f0' }}>
        <h3 style={{ margin: '0 0 1.25rem 0', fontSize: '1.2rem', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <BarChart2 size={20} style={{ color: 'var(--primary)' }} /> Top 5 Highest Capital Valuation Products
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {stats.top_valuable_products.length > 0 ? (
            stats.top_valuable_products.map((item, index) => {
              const maxVal = stats.top_valuable_products[0].total_value || 1;
              const barWidth = Math.max((item.total_value / maxVal) * 100, 5);

              return (
                <div key={item.id} style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                    <span>
                      <strong style={{ color: 'var(--text-main)' }}>#{index + 1} {item.name}</strong> 
                      <span style={{ color: '#64748b', marginLeft: '0.5rem' }}>(SKU: {item.sku})</span>
                    </span>
                    <strong style={{ color: 'var(--primary)' }}>
                      ${item.total_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </strong>
                  </div>
                  
                  <div style={{ background: '#f1f5f9', height: '10px', borderRadius: '9999px', overflow: 'hidden' }}>
                    <div 
                      style={{ 
                        width: `${barWidth}%`, 
                        background: 'linear-gradient(90deg, #3b82f6, #2563eb)', 
                        height: '100%', 
                        borderRadius: '9999px',
                        transition: 'width 0.4s'
                      }} 
                    />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#64748b' }}>
                    <span>Stock: {item.current_stock} units</span>
                    <span>Cost: ${item.unit_cost.toFixed(2)} / unit</span>
                  </div>
                </div>
              );
            })
          ) : (
            <p style={{ color: '#64748b', textAlign: 'center', padding: '1rem 0' }}>No active products available to display valuation.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default StoreStatistics;
