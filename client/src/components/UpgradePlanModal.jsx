import React, { useState } from 'react';
import { ShieldCheck, Zap, Crown, Check, X } from 'lucide-react';
import api from '../services/api';
import './UpgradePlanModal.css';

const UpgradePlanModal = ({ isOpen, onClose, currentPlan, onPlanUpgraded }) => {
  const [upgrading, setUpgrading] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(currentPlan || 'STARTER');

  if (!isOpen) return null;

  const handleSelectPlan = async (planKey) => {
    if (planKey === currentPlan) return;
    setUpgrading(true);

    try {
      const token = localStorage.getItem('access_token');
      
      if (planKey === 'STARTER') {
        const response = await api.post('users/upgrade-plan/', { plan: planKey }, {
          headers: { Authorization: `Bearer ${token}` }
        });
        alert(`🎉 ${response.data.message}`);
        if (onPlanUpgraded) onPlanUpgraded('STARTER');
        onClose();
        setUpgrading(false);
        return;
      }

      const response = await api.post('users/payments/create-checkout-session/', { plan: planKey }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.checkout_url) {
        localStorage.setItem('pending_stripe_plan', planKey);
        window.location.href = response.data.checkout_url;
      } else {
        throw new Error("Missing checkout URL");
      }
    } catch (err) {
      console.error("Plan upgrade failed:", err);
      const msg = err.response?.data?.error || "Failed to initialize payment. Please try again.";
      alert(`⚠️ ${msg}`);
      setUpgrading(false);
    }
    // Note: finally { setUpgrading(false) } is removed because we want the button to stay loading while redirecting
  };

  const plans = [
    {
      key: 'STARTER',
      name: 'Starter Plan',
      price: '$0 / mo',
      icon: <ShieldCheck size={28} className="plan-icon starter" />,
      features: [
        'Up to 5 Products',
        'Basic Inventory Tracking',
        'Supplier Contact Directory',
        'Community Support'
      ]
    },
    {
      key: 'PRO',
      name: 'Pro Growth',
      price: '$29 / mo',
      popular: true,
      icon: <Zap size={28} className="plan-icon pro" />,
      features: [
        'Unlimited Products & Suppliers',
        'Soft Delete & Data Archiving',
        'Visual Stock Status Badges',
        'Export Data to CSV / Excel',
        'Priority Email Support'
      ]
    },
    {
      key: 'ENTERPRISE',
      name: 'Enterprise AI Agent',
      price: '$79 / mo',
      icon: <Crown size={28} className="plan-icon enterprise" />,
      features: [
        'Everything in Pro Plan',
        'Google Gemini 2.5 AI Insights Engine',
        'Ask Analyst Interactive AI Chat',
        'Automated 30-Day Velocity Projections',
        '24/7 Dedicated Support'
      ]
    }
  ];

  return (
    <div className="modal-overlay">
      <div className="upgrade-modal-content">
        <div className="upgrade-modal-header">
          <div>
            <h2>Choose Your Subscription Plan</h2>
            <p>Scale your retail store with automated AI inventory management</p>
          </div>
          <button onClick={onClose} className="close-btn"><X size={20} /></button>
        </div>

        <div className="plans-grid">
          {plans.map((plan) => {
            const isCurrent = currentPlan === plan.key;
            return (
              <div
                key={plan.key}
                className={`plan-card ${plan.popular ? 'popular' : ''} ${isCurrent ? 'active' : ''}`}
              >
                {plan.popular && <span className="popular-tag">MOST POPULAR</span>}
                <div className="plan-card-header">
                  {plan.icon}
                  <h3>{plan.name}</h3>
                  <div className="plan-price">{plan.price}</div>
                </div>

                <ul className="plan-features">
                  {plan.features.map((feat, idx) => (
                    <li key={idx}><Check size={16} className="check-icon" /> {feat}</li>
                  ))}
                </ul>

                <button
                  disabled={upgrading || isCurrent}
                  onClick={() => handleSelectPlan(plan.key)}
                  className={`plan-select-btn ${isCurrent ? 'btn-active' : plan.popular ? 'btn-popular' : ''}`}
                >
                  {isCurrent ? 'Current Plan' : upgrading ? 'Updating...' : `Select ${plan.name}`}
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default UpgradePlanModal;
