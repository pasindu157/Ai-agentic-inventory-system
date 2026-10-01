import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import AdminDashboard from './AdminDashboard';
import StoreOwnerDashboard from './StoreOwnerDashboard';
import api from '../services/api';
import './Dashboard.css';

const DashboardRouter = () => {
  const [role, setRole] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRole = async () => {
      try {
        const token = localStorage.getItem('access_token');
        if (!token) {
          setRole('NONE');
          return;
        }
        // Fetch user profile securely using their token
        const response = await api.get('users/me/', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setRole(response.data.role);
      } catch (err) {
        setRole('NONE');
      } finally {
        setLoading(false);
      }
    };
    fetchRole();
  }, []);

  if (loading) {
    return <div className="dashboard-loading">Loading secure dashboard...</div>;
  }

  // Display the appropriate Dashboard based on the API response Role
  if (role === 'ADMIN') {
    return <AdminDashboard />;
  } else if (role === 'STORE_OWNER') {
    return <StoreOwnerDashboard />;
  } else {
    // If not authenticated, boot them back to login
    return <Navigate to="/login" replace />;
  }
};

export default DashboardRouter;
