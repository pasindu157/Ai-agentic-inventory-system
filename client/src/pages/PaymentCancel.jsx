import React from 'react';
import { useNavigate } from 'react-router-dom';
import { XCircle } from 'lucide-react';

const PaymentCancel = () => {
  const navigate = useNavigate();

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center', 
      justifyContent: 'center', height: '100vh', backgroundColor: '#fef2f2',
      fontFamily: 'Inter, sans-serif'
    }}>
      <div style={{
        backgroundColor: 'white', padding: '3rem', borderRadius: '1rem', 
        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)', textAlign: 'center',
        maxWidth: '400px'
      }}>
        <XCircle size={64} color="#dc2626" style={{ marginBottom: '1.5rem', margin: '0 auto', display: 'block' }} />
        <h1 style={{ color: '#991b1b', fontSize: '1.5rem', marginBottom: '1rem' }}>Payment Canceled</h1>
        <p style={{ color: '#4b5563', marginBottom: '1.5rem', lineHeight: '1.5' }}>
          Your upgrade was not completed. You have not been charged.
        </p>
        <button 
          onClick={() => navigate('/dashboard')}
          style={{
            width: '100%', padding: '0.75rem',
            backgroundColor: '#ef4444', color: 'white', border: 'none',
            borderRadius: '0.5rem', fontWeight: 'bold', cursor: 'pointer'
          }}
        >
          Return to Dashboard
        </button>
      </div>
    </div>
  );
};

export default PaymentCancel;
