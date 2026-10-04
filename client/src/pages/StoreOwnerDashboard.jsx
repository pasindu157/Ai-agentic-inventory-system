import React, { useState, useEffect } from 'react';
import { Package, TrendingDown, TrendingUp, AlertTriangle, CheckCircle, LogOut, ShieldCheck, Zap, Crown, BarChart2 } from 'lucide-react';
import api from '../services/api';
import AddProductModal from '../components/AddProductModal';
import AddSupplierModal from '../components/AddSupplierModal';
import EditProductModal from '../components/EditProductModal';
import UpgradePlanModal from '../components/UpgradePlanModal';
import StoreStatistics from './StoreStatistics';
import './Dashboard.css';

const StoreOwnerDashboard = () => {
  const [recommendations, setRecommendations] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSupplierModalOpen, setIsSupplierModalOpen] = useState(false);
  const [showAI, setShowAI] = useState(false);
  const [generatingAI, setGeneratingAI] = useState(false);
  
  // Edit Specific Modes
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);

  // Interactive Chat States
  const [aiQuery, setAiQuery] = useState('');
  const [askingAI, setAskingAI] = useState(false);
  const [aiResponse, setAiResponse] = useState('');

  // Subscription Plan State
  const [subscriptionPlan, setSubscriptionPlan] = useState('STARTER');
  const [isUpgradeModalOpen, setIsUpgradeModalOpen] = useState(false);

  // Active Navigation Tab ('PRODUCTS' | 'STATS')
  const [activeTab, setActiveTab] = useState('PRODUCTS');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const headers = { Authorization: `Bearer ${token}` };

        const [recRes, prodRes, userRes] = await Promise.all([
          api.get('agents/recommendations/', { headers }),
          api.get('inventory/products/', { headers }),
          api.get('users/me/', { headers }).catch(() => null)
        ]);

        setRecommendations(recRes.data.sort((a,b) => new Date(b.created_at) - new Date(a.created_at)));
        setProducts(prodRes.data);
        if (userRes && userRes.data && userRes.data.store) {
          setSubscriptionPlan(userRes.data.store.subscription_plan || 'STARTER');
        }
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  useEffect(() => {
    if (subscriptionPlan !== 'ENTERPRISE') {
      setShowAI(false);
    }
  }, [subscriptionPlan]);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  };

  const handleProductAdded = (newProduct) => {
    // Magic: Instantly inject the newly inserted product to the top of our table list!
    setProducts([newProduct, ...products]);
  };

  const handleEditClick = (product) => {
    setEditingProduct(product);
    setIsEditModalOpen(true);
  };

  const handleProductUpdated = (updatedProduct) => {
    // Smoothly intercept the old product element mapped in the current state and override strictly the updated values.
    setProducts(products.map(p => p.id === updatedProduct.id ? updatedProduct : p));
  };

  const handleDeleteProduct = async (productId, productName) => {
    if (!window.confirm(`Are you sure you want to soft-delete "${productName}"?\n\nIt will be archived and removed from active inventory, but all historical sales data will remain intact for AI analytics.`)) {
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      await api.delete(`inventory/products/${productId}/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      // Immediately remove the soft-deleted item from state
      setProducts(products.filter(p => p.id !== productId));
    } catch (err) {
      console.error("Soft delete failed:", err);
      alert("Failed to delete product. Please try again.");
    }
  };

  const handleAddProductClick = () => {
    if (subscriptionPlan === 'STARTER' && products.length >= 5) {
      alert("⚠️ You have reached the 5-product limit on the Starter Plan.\n\nPlease upgrade to Pro or Enterprise for unlimited products!");
      setIsUpgradeModalOpen(true);
      return;
    }
    setIsModalOpen(true);
  };

  const handleToggleAI = () => {
    if (showAI) {
      setShowAI(false);
      return;
    }
    if (subscriptionPlan !== 'ENTERPRISE') {
      alert("🔒 Agentic AI Insights & Ask Analyst Chat are exclusive to the Enterprise AI Plan.\n\nPlease upgrade your subscription to unlock Gemini!");
      setIsUpgradeModalOpen(true);
      return;
    }
    fetchFreshRecommendations();
  };

  const fetchFreshRecommendations = async () => {
    try {
      setGeneratingAI(true);
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };
      
      // 1. Ask Django backend to fire the Gemini AI pipeline explicitly
      await api.post('agents/recommendations/generate/', {}, { headers });
      
      // 2. Fetch the newly generated DB objects dynamically
      const recRes = await api.get('agents/recommendations/', { headers });
      setRecommendations(recRes.data.sort((a,b) => new Date(b.created_at) - new Date(a.created_at)));
      
      setShowAI(true);
    } catch (error) {
      console.error(error);
      alert("Failed to generate Agentic AI insights.");
    } finally {
      setGeneratingAI(false);
    }
  };

  const handleAskAI = async (e) => {
    e.preventDefault();
    if (subscriptionPlan !== 'ENTERPRISE') {
      alert("🔒 Gemini AI Analyst Chat is exclusive to the Enterprise AI Plan.\n\nPlease upgrade your subscription to consult the AI Analyst!");
      setIsUpgradeModalOpen(true);
      return;
    }

    setAskingAI(true);
    setAiResponse('');

    try {
      const token = localStorage.getItem('access_token');
      const response = await api.post('agents/recommendations/ask/', { question: aiQuery }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAiResponse(response.data.answer);
    } catch (err) {
      console.error(err);
      setAiResponse("⚠️ Failed to connect to Gemini. Please check your internet or API key.");
    } finally {
      setAskingAI(false);
    }
  };

  const getStatusIcon = (type) => {
    switch (type) {
      case 'URGENT_REORDER': return <AlertTriangle className="icon-urgent" size={24} />;
      case 'OVERSTOCK': return <TrendingDown className="icon-overstock" size={24} />;
      case 'OPTIMAL': return <CheckCircle className="icon-optimal" size={24} />;
      default: return <Package className="icon-default" size={24} />;
    }
  };

  const getStockStatusBadge = (product) => {
    const stock = Number(product.current_stock);
    const reorder = Number(product.reorder_level);

    if (stock <= reorder) {
      return <span className="status-pill status-pill-urgent">⚠️ Urgent Reorder</span>;
    } else if (stock <= reorder * 1.5) {
      return <span className="status-pill status-pill-low">📉 Low Stock</span>;
    } else {
      return <span className="status-pill status-pill-optimal">✓ Optimal</span>;
    }
  };

  const renderPlanBadge = () => {
    switch (subscriptionPlan) {
      case 'PRO':
        return (
          <button onClick={() => setIsUpgradeModalOpen(true)} className="plan-badge pro" title="Click to view subscription plans">
            <Zap size={15} /> Pro Growth ($29/mo)
          </button>
        );
      case 'ENTERPRISE':
        return (
          <button onClick={() => setIsUpgradeModalOpen(true)} className="plan-badge enterprise" title="Click to view subscription plans">
            <Crown size={15} /> Enterprise AI ($79/mo)
          </button>
        );
      default:
        return (
          <button onClick={() => setIsUpgradeModalOpen(true)} className="plan-badge starter" title="Click to view subscription plans">
            <ShieldCheck size={15} /> Starter Plan (Free) — <span>Upgrade</span>
          </button>
        );
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
          <nav style={{display:'flex', gap:'0.5rem', marginLeft:'2rem'}}>
            <button 
              onClick={() => setActiveTab('PRODUCTS')}
              style={{
                padding:'0.45rem 0.9rem',
                borderRadius:'8px',
                border: activeTab === 'PRODUCTS' ? '1px solid var(--primary)' : '1px solid #cbd5e1',
                background: activeTab === 'PRODUCTS' ? '#eff6ff' : 'white',
                color: activeTab === 'PRODUCTS' ? 'var(--primary)' : '#475569',
                fontWeight:'600',
                fontSize:'0.85rem',
                cursor:'pointer',
                display:'flex',
                alignItems:'center',
                gap:'0.4rem'
              }}
            >
              <Package size={15} /> Product Master
            </button>
            <button 
              onClick={() => setActiveTab('STATS')}
              style={{
                padding:'0.45rem 0.9rem',
                borderRadius:'8px',
                border: activeTab === 'STATS' ? '1px solid var(--primary)' : '1px solid #cbd5e1',
                background: activeTab === 'STATS' ? '#eff6ff' : 'white',
                color: activeTab === 'STATS' ? 'var(--primary)' : '#475569',
                fontWeight:'600',
                fontSize:'0.85rem',
                cursor:'pointer',
                display:'flex',
                alignItems:'center',
                gap:'0.4rem'
              }}
            >
              <BarChart2 size={15} /> Analytics & Stats
            </button>
          </nav>
        </div>
        <div className="header-actions">
          {renderPlanBadge()}
          <button onClick={handleLogout} className="logout-btn">
            <LogOut size={16} /> Logout
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        {activeTab === 'STATS' ? (
          <StoreStatistics />
        ) : (
          <>
            {/* Core Product Tracking is now the FIRST thing the user sees */}
        <div className="dashboard-bottom-section">
          
          <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom: '1.25rem'}}>
            <h2 style={{margin:0}}>Product Master File ({products.length} Items)</h2>
            
            <div style={{display: 'flex', gap: '1rem'}}>
              <button 
                  onClick={handleToggleAI} 
                  className="btn-save" 
                  disabled={generatingAI}
                  style={{
                    padding:'0.5rem 1rem', 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '0.5rem', 
                    background: subscriptionPlan !== 'ENTERPRISE' ? '#94a3b8' : showAI ? '#64748b' : 'var(--primary)', 
                    border: 'none', 
                    color: 'white', 
                    borderRadius: '8px', 
                    cursor: generatingAI ? 'wait' : 'pointer', 
                    fontWeight: '600', 
                    transition: 'all 0.2s', 
                    boxShadow: '0 4px 6px -1px rgba(37, 99, 235, 0.2)'
                  }}
              >
                {subscriptionPlan !== 'ENTERPRISE' ? '🔒 AI Insights (Enterprise)' : generatingAI ? '✨ AI is Analyzing Stock...' : showAI ? '✨ Hide AI Insights' : '✨ Generate AI Insights'}
              </button>
              <button onClick={() => setIsSupplierModalOpen(true)} className="logout-btn" style={{color: '#475569', borderColor: '#cbd5e1', fontWeight: '600'}}>
                + Add Supplier
              </button>
              <button 
                onClick={handleAddProductClick} 
                className="logout-btn" 
                style={{color: 'var(--primary)', borderColor: '#bfdbfe', fontWeight: '600'}}
              >
                + Add Product {subscriptionPlan === 'STARTER' && products.length >= 5 ? '(Limit 5)' : ''}
              </button>
            </div>
          </div>
          
          <div className="products-table-container">
            <table className="products-table">
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Product Name</th>
                  <th>Status</th>
                  <th>Current Stock</th>
                  <th>Reorder Level</th>
                  <th>Unit Cost</th>
                  <th style={{textAlign: 'center'}}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {products.length > 0 ? (
                   products.map(product => (
                    <tr key={product.id}>
                      <td>{product.sku}</td>
                      <td>{product.name}</td>
                      <td>{getStockStatusBadge(product)}</td>
                      <td><strong>{product.current_stock}</strong></td>
                      <td>{product.reorder_level}</td>
                      <td>${Number(product.unit_cost).toFixed(2)}</td>
                      <td style={{textAlign: 'center', display: 'flex', justifyContent: 'center', gap: '0.5rem'}}>
                        <button 
                           onClick={() => handleEditClick(product)} 
                           style={{background: 'transparent', border: '1px solid #cbd5e1', padding: '0.35rem 0.85rem', borderRadius: '6px', cursor: 'pointer', color: '#475569', fontWeight: '600', fontSize: '0.85rem', transition: 'all 0.15s'}}
                           onMouseOver={(e) => { e.currentTarget.style.backgroundColor = '#f1f5f9'; e.currentTarget.style.borderColor = '#94a3b8'; e.currentTarget.style.color = '#0f172a'; }}
                           onMouseOut={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.borderColor = '#cbd5e1'; e.currentTarget.style.color = '#475569'; }}
                        >
                          Edit
                        </button>
                        <button 
                           onClick={() => handleDeleteProduct(product.id, product.name)} 
                           style={{background: 'transparent', border: '1px solid #fecaca', padding: '0.35rem 0.85rem', borderRadius: '6px', cursor: 'pointer', color: '#dc2626', fontWeight: '600', fontSize: '0.85rem', transition: 'all 0.15s'}}
                           onMouseOver={(e) => { e.currentTarget.style.backgroundColor = '#fef2f2'; e.currentTarget.style.borderColor = '#fca5a5'; }}
                           onMouseOut={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.borderColor = '#fecaca'; }}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" style={{textAlign: 'center', padding: '2rem', color: '#64748b'}}>No Products found in your database.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Hidden AI Recommendations Section */}
        {showAI && (
          <div className="dashboard-top-section" style={{marginTop: '3.5rem', animation: 'slideUp 0.3s ease-out'}}>
            <h2 style={{fontSize: '1.5rem', color: 'var(--text-main)', marginBottom: '0.25rem', fontWeight: '600'}}>AI Recommendations & Agentic Chat</h2>
            <p style={{color: 'var(--text-muted)', marginBottom: '1.5rem'}}>Powered by Realtime Mathematical Modeling & Google Gemini</p>
            
            {/* New: ChatGPT-style Query Bar */}
            <div style={{backgroundColor: 'white', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', border: '1px solid #e2e8f0', marginBottom: '2rem'}}>
               <form onSubmit={handleAskAI} style={{display: 'flex', gap: '1rem'}}>
                  <input 
                     type="text" 
                     value={aiQuery}
                     onChange={(e) => setAiQuery(e.target.value)}
                     placeholder="Ask Gemini anything specific about your live inventory stock..." 
                     style={{flex: 1, padding: '0.85rem 1.25rem', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.95rem', outline: 'none', backgroundColor: '#f8fafc', transition: 'all 0.2s'}} 
                     required
                  />
                  <button type="submit" disabled={askingAI} className="btn-save" style={{padding: '0.5rem 1.5rem', minWidth: '140px'}}>
                      {askingAI ? 'Consulting AI...' : 'Ask Analyst'}
                  </button>
               </form>
               
               {aiResponse && (
                  <div style={{marginTop: '1.5rem', padding: '1.25rem', backgroundColor: '#f0fdf4', borderRadius: '8px', borderLeft: '4px solid #10b981', color: '#166534', lineHeight: '1.6'}}>
                     <h4 style={{marginTop: 0, marginBottom: '0.5rem', color: '#047857'}}>Gemini Response:</h4>
                     <p style={{margin: 0, whiteSpace: 'pre-wrap'}}>{aiResponse}</p>
                  </div>
               )}
            </div>

            <div className="recommendations-list">
              {recommendations.length > 0 ? (
                recommendations.map(rec => (
                  <div key={rec.id} className={`rec-list-item status-${rec.recommendation_type.toLowerCase()}`}>
                    <div className="rec-icon-wrapper">
                      {getStatusIcon(rec.recommendation_type)}
                    </div>
                    <div className="rec-content">
                      <div className="rec-title-row">
                        <h3>{rec.product_name}</h3>
                        {rec.recommended_order_quantity > 0 && (
                          <span className="reorder-badge">
                            Order: {rec.recommended_order_quantity} Units
                          </span>
                        )}
                      </div>
                      <p className="rec-text">{rec.explanation}</p>
                    </div>
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
          </div>
        )}
          </>
        )}
      </main>

      <AddProductModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onProductAdded={handleProductAdded} 
      />
      <AddSupplierModal 
        isOpen={isSupplierModalOpen} 
        onClose={() => setIsSupplierModalOpen(false)} 
        onSupplierAdded={() => alert('Supplier successfully added! You can now select them from the Add Product menu.')} 
      />
      <EditProductModal 
        isOpen={isEditModalOpen} 
        onClose={() => setIsEditModalOpen(false)} 
        product={editingProduct} 
        onProductUpdated={handleProductUpdated} 
      />
      <UpgradePlanModal
        isOpen={isUpgradeModalOpen}
        onClose={() => setIsUpgradeModalOpen(false)}
        currentPlan={subscriptionPlan}
        onPlanUpgraded={(newPlan) => setSubscriptionPlan(newPlan)}
      />
    </div>
  );
};

export default StoreOwnerDashboard;
