import React, { useState, useEffect } from 'react';
import { 
  Building2, Package, ShieldCheck, Zap, Crown, DollarSign, 
  LogOut, Search, RefreshCw, User, Mail, Calendar 
} from 'lucide-react';
import api from '../services/api';
import './Dashboard.css';

const AdminDashboard = () => {
  const [kpis, setKpis] = useState({
    total_stores: 0,
    total_active_products: 0,
    starter_count: 0,
    pro_count: 0,
    enterprise_count: 0,
    mrr: 0
  });
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [updatingStoreId, setUpdatingStoreId] = useState(null);

  const fetchAdminData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const response = await api.get('users/admin/overview/', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setKpis(response.data.kpis);
      setStores(response.data.stores);
    } catch (error) {
      console.error("Failed to fetch admin dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminData();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  };

  const handlePlanChange = async (storeId, newPlan) => {
    setUpdatingStoreId(storeId);
    try {
      const token = localStorage.getItem('access_token');
      const response = await api.post('users/admin/change-store-plan/', 
        { store_id: storeId, plan: newPlan },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Re-fetch overview data to recalculate KPIs & MRR dynamically
      await fetchAdminData();
      alert(`✅ ${response.data.message}`);
    } catch (err) {
      console.error("Failed to update store plan:", err);
      alert("Failed to change store plan.");
    } finally {
      setUpdatingStoreId(null);
    }
  };

  const filteredStores = stores.filter(store => 
    store.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    store.owner_username.toLowerCase().includes(searchTerm.toLowerCase()) ||
    store.owner_email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getPlanBadge = (plan) => {
    switch (plan) {
      case 'PRO':
        return <span className="status-pill status-pill-low" style={{display:'inline-flex', gap:'0.25rem', alignItems:'center'}}><Zap size={13}/> PRO ($29/mo)</span>;
      case 'ENTERPRISE':
        return <span className="status-pill status-pill-urgent" style={{display:'inline-flex', gap:'0.25rem', alignItems:'center', background:'#f3e8ff', color:'#7c3aed', borderColor:'#ddd6fe'}}><Crown size={13}/> ENTERPRISE ($79/mo)</span>;
      default:
        return <span className="status-pill status-pill-optimal" style={{display:'inline-flex', gap:'0.25rem', alignItems:'center', background:'#f1f5f9', color:'#475569', borderColor:'#cbd5e1'}}><ShieldCheck size={13}/> STARTER (Free)</span>;
    }
  };

  if (loading) {
    return <div className="dashboard-loading">Loading Admin Control Panel...</div>;
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div className="header-brand">
          <ShieldCheck size={28} className="brand-icon" style={{color: '#8b5cf6'}} />
          <h1>Admin <span>Control Panel</span></h1>
        </div>
        <div className="header-actions">
          <button onClick={fetchAdminData} className="logout-btn" style={{color:'#475569', borderColor:'#cbd5e1'}}>
            <RefreshCw size={15} /> Refresh
          </button>
          <button onClick={handleLogout} className="logout-btn">
            <LogOut size={16} /> Logout
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        {/* KPI Stat Cards Row */}
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-header">
              <span>Total Tenant Stores</span>
              <Building2 className="icon-optimal" size={24} />
            </div>
            <div className="metric-value">{kpis.total_stores}</div>
            <p className="metric-subtext">Registered store owners</p>
          </div>

          <div className="metric-card">
            <div className="metric-header">
              <span>Platform Active Products</span>
              <Package className="icon-default" size={24} style={{color: '#3b82f6'}} />
            </div>
            <div className="metric-value">{kpis.total_active_products}</div>
            <p className="metric-subtext">Across all store inventories</p>
          </div>

          <div className="metric-card">
            <div className="metric-header">
              <span>Paid SaaS Subscribers</span>
              <Zap className="icon-overstock" size={24} />
            </div>
            <div className="metric-value">{kpis.pro_count + kpis.enterprise_count}</div>
            <p className="metric-subtext">{kpis.pro_count} Pro • {kpis.enterprise_count} Enterprise</p>
          </div>

          <div className="metric-card" style={{borderLeft: '4px solid #10b981'}}>
            <div className="metric-header">
              <span>Estimated Monthly MRR</span>
              <DollarSign className="icon-optimal" size={24} />
            </div>
            <div className="metric-value" style={{color: '#059669'}}>${kpis.mrr}</div>
            <p className="metric-subtext">Recurring monthly subscription revenue</p>
          </div>
        </div>

        {/* Store Management Table Section */}
        <div className="dashboard-bottom-section">
          <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom: '1.25rem', flexWrap:'wrap', gap:'1rem'}}>
            <h2 style={{margin:0}}>All Stores Directory ({stores.length} Stores)</h2>
            
            <div style={{position: 'relative', width: '280px'}}>
              <Search size={16} style={{position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8'}} />
              <input 
                type="text" 
                placeholder="Search store or owner..." 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem 0.5rem 2.25rem',
                  borderRadius: '8px',
                  border: '1px solid #cbd5e1',
                  fontSize: '0.875rem'
                }}
              />
            </div>
          </div>

          <div className="products-table-container">
            <table className="products-table">
              <thead>
                <tr>
                  <th>Store Name</th>
                  <th>Owner</th>
                  <th>Active Products</th>
                  <th>Current Plan</th>
                  <th>Joined Date</th>
                  <th style={{textAlign: 'center'}}>Admin Action (Change Plan)</th>
                </tr>
              </thead>
              <tbody>
                {filteredStores.length > 0 ? (
                  filteredStores.map(store => (
                    <tr key={store.id}>
                      <td>
                        <strong>{store.name}</strong>
                      </td>
                      <td>
                        <div style={{display:'flex', flexDirection:'column', gap:'2px'}}>
                          <span style={{fontWeight:'600', color:'#334155'}}><User size={13} style={{display:'inline', marginRight:'4px'}} />{store.owner_username}</span>
                          <span style={{fontSize:'0.75rem', color:'#64748b'}}><Mail size={12} style={{display:'inline', marginRight:'4px'}} />{store.owner_email || 'No email'}</span>
                        </div>
                      </td>
                      <td><strong>{store.active_products_count}</strong> Products</td>
                      <td>{getPlanBadge(store.subscription_plan)}</td>
                      <td>
                        <span style={{fontSize:'0.8rem', color:'#64748b'}}>
                          <Calendar size={13} style={{display:'inline', marginRight:'4px'}} />
                          {new Date(store.created_at).toLocaleDateString()}
                        </span>
                      </td>
                      <td style={{textAlign: 'center'}}>
                        <select
                          disabled={updatingStoreId === store.id}
                          value={store.subscription_plan}
                          onChange={(e) => handlePlanChange(store.id, e.target.value)}
                          style={{
                            padding: '0.4rem 0.75rem',
                            borderRadius: '6px',
                            border: '1px solid #cbd5e1',
                            fontWeight: '600',
                            fontSize: '0.8rem',
                            background: 'white',
                            cursor: 'pointer'
                          }}
                        >
                          <option value="STARTER">Starter Plan (Free)</option>
                          <option value="PRO">Pro Growth ($29/mo)</option>
                          <option value="ENTERPRISE">Enterprise AI ($79/mo)</option>
                        </select>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="6" style={{textAlign: 'center', padding: '2rem', color: '#64748b'}}>
                      No stores match your search criteria.
                    </td>
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

export default AdminDashboard;
