import React from 'react';

const AdminDashboard = () => {
  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Admin Control Panel</h1>
        <button onClick={handleLogout} className="logout-btn">Logout</button>
      </header>
      <main className="dashboard-main">
        <div className="dashboard-card">
          <h2>System Overview</h2>
          <p>Welcome, System Administrator. Here you can monitor all stores across the multitenant system.</p>
        </div>
      </main>
    </div>
  );
};

export default AdminDashboard;
