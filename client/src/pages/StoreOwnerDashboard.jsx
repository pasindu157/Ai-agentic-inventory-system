import React, { useState, useEffect } from 'react';
import { Package, TrendingDown, TrendingUp, AlertTriangle, CheckCircle, LogOut } from 'lucide-react';
import api from '../services/api';
import AddProductModal from '../components/AddProductModal';
import AddSupplierModal from '../components/AddSupplierModal';
import EditProductModal from '../components/EditProductModal';
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

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const headers = { Authorization: `Bearer ${token}` };

        const [recRes, prodRes] = await Promise.all([
          api.get('agents/recommendations/', { headers }),
          api.get('inventory/products/', { headers })
        ]);

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
        
        {/* Core Product Tracking is now the FIRST thing the user sees */}
        <div className="dashboard-bottom-section">
          
          <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom: '1.25rem'}}>
            <h2 style={{margin:0}}>Product Master File ({products.length} Items)</h2>
            
            <div style={{display: 'flex', gap: '1rem'}}>
              <button 
                  onClick={() => {
                    if (!showAI) {
                       fetchFreshRecommendations();
                    } else {
                       setShowAI(false);
                    }
                  }} 
                  className="btn-save" 
                  disabled={generatingAI}
                  style={{padding:'0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', background: showAI ? '#64748b' : 'var(--primary)', border: 'none', color: 'white', borderRadius: '8px', cursor: generatingAI ? 'wait' : 'pointer', fontWeight: '600', transition: 'all 0.2s', boxShadow: '0 4px 6px -1px rgba(37, 99, 235, 0.2)'}}
              >
                ✨ {generatingAI ? 'AI is Analyzing Stock...' : showAI ? 'Hide AI Insights' : 'Generate AI Insights'}
              </button>
              <button onClick={() => setIsSupplierModalOpen(true)} className="logout-btn" style={{color: '#475569', borderColor: '#cbd5e1', fontWeight: '600'}}>
                + Add Supplier
              </button>
              <button onClick={() => setIsModalOpen(true)} className="logout-btn" style={{color: 'var(--primary)', borderColor: '#bfdbfe', fontWeight: '600'}}>
                + Add Product
              </button>
            </div>
          </div>
          
          <div className="products-table-container">
            <table className="products-table">
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Product Name</th>
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
                      <td><strong>{product.current_stock}</strong></td>
                      <td>{product.reorder_level}</td>
                      <td>${Number(product.unit_cost).toFixed(2)}</td>
                      <td style={{textAlign: 'center'}}>
                        <button 
                           onClick={() => handleEditClick(product)} 
                           style={{background: 'transparent', border: '1px solid #cbd5e1', padding: '0.35rem 0.85rem', borderRadius: '6px', cursor: 'pointer', color: '#475569', fontWeight: '600', fontSize: '0.85rem', transition: 'all 0.15s'}}
                           onMouseOver={(e) => { e.currentTarget.style.backgroundColor = '#f1f5f9'; e.currentTarget.style.borderColor = '#94a3b8'; e.currentTarget.style.color = '#0f172a'; }}
                           onMouseOut={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.borderColor = '#cbd5e1'; e.currentTarget.style.color = '#475569'; }}
                        >
                          Edit
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
    </div>
  );
};

export default StoreOwnerDashboard;
