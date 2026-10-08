import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CheckCircle } from 'lucide-react';
import api from '../services/api';

const PaymentSuccess = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [countdown, setCountdown] = useState(5);
  const sessionId = searchParams.get('session_id');

  useEffect(() => {
    const handleLocalUpgrade = async () => {
      const pendingPlan = localStorage.getItem('pending_stripe_plan');
      if (pendingPlan) {
        try {
          const token = localStorage.getItem('access_token');
          await api.post('users/upgrade-plan/', { plan: pendingPlan }, {
            headers: { Authorization: `Bearer ${token}` }
          });
          localStorage.removeItem('pending_stripe_plan');
        } catch (e) {
          console.error("Local fast-upgrade failed:", e);
        }
      }
    };
    handleLocalUpgrade();

    const timer = setInterval(() => {
      setCountdown((prev) => prev - 1);
    }, 1000);

    setTimeout(() => {
      navigate('/dashboard');
    }, 5000);

    return () => clearInterval(timer);
  }, [navigate]);

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center', 
      justifyContent: 'center', height: '100vh', backgroundColor: '#f0fdf4',
      fontFamily: 'Inter, sans-serif'
    }}>
      <div style={{
        backgroundColor: 'white', padding: '3rem', borderRadius: '1rem', 
        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)', textAlign: 'center',
        maxWidth: '400px'
      }}>
        <CheckCircle size={64} color="#10b981" style={{ marginBottom: '1.5rem', margin: '0 auto', display: 'block' }} />
        <h1 style={{ color: '#065f46', fontSize: '1.5rem', marginBottom: '1rem' }}>Payment Successful!</h1>
        <p style={{ color: '#4b5563', marginBottom: '1.5rem', lineHeight: '1.5' }}>
          Thank you for upgrading! Your subscription plan has been successfully activated.
        </p>
        <p style={{ color: '#9ca3af', fontSize: '0.875rem' }}>
          Redirecting to your dashboard in {countdown} seconds...
        </p>
        <button 
          onClick={() => navigate('/dashboard')}
          style={{
            marginTop: '1.5rem', width: '100%', padding: '0.75rem',
            backgroundColor: '#10b981', color: 'white', border: 'none',
            borderRadius: '0.5rem', fontWeight: 'bold', cursor: 'pointer'
          }}
        >
          Go to Dashboard Now
        </button>
      </div>
    </div>
  );
};

export default PaymentSuccess;
