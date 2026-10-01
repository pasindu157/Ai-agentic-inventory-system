import { useState } from 'react';
import api from './api/axios';
import './App.css';

function App() {
  const [status, setStatus] = useState('No request sent yet.');

  const testConnection = async () => {
    try {
      // Trying to hit the base API or a healthy endpoint
      const response = await api.get('/'); 
      setStatus(`Success! Status Code: ${response.status} | Data: ${JSON.stringify(response.data)}`);
    } catch (error) {
      setStatus(`Error: ${error.message} - Make sure Django is running on port 8000!`);
    }
  };

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>React + Django Test</h1>
      <p>Click the button below to test Cross-Origin Resource Sharing (CORS) with the Django server.</p>
      <button 
        onClick={testConnection} 
        style={{ padding: '0.5rem 1rem', cursor: 'pointer', fontSize: '1rem' }}
      >
        Test Backend Connection
      </button>
      <div style={{ marginTop: '2rem', padding: '1rem', background: '#f5f5f5', borderRadius: '4px' }}>
        <strong>Response:</strong>
        <p>{status}</p>
      </div>
    </div>
  );
}

export default App;
