import React from 'react';

const StoreOwnerDashboard = () => {
  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Store Dashboard</h1>
        <button onClick={handleLogout} className="logout-btn">Logout</button>
      </header>
      <main className="dashboard-main">
        <div className="dashboard-card">
          <h2>Inventory Highlights</h2>
          <p>Welcome to your personal store dashboard. AI recommendations and inventory tracking will automatically appear here soon.</p>
        </div>
      </main>
    </div>
  );
};

export default StoreOwnerDashboard;
