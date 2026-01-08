import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import TextInput from './components/TextInput/TextInput';
import HeatMap from './components/HeatMap/HeatMap';
import ProfileManager from './components/ProfileManager/ProfileManager';
import RewriteInterface from './components/RewriteInterface/RewriteInterface';
import Login from './components/Login/Login';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    setIsAuthenticated(!!token);
    setLoading(false);
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <h1>Ghostwriter Forensic Analytics</h1>
          {isAuthenticated && (
            <button
              onClick={() => {
                localStorage.removeItem('access_token');
                setIsAuthenticated(false);
              }}
              className="logout-btn"
            >
              Logout
            </button>
          )}
        </nav>

        <Routes>
          <Route
            path="/login"
            element={
              isAuthenticated ? (
                <Navigate to="/" replace />
              ) : (
                <Login onLogin={() => setIsAuthenticated(true)} />
              )
            }
          />
          <Route
            path="/"
            element={
              isAuthenticated ? (
                <div className="main-content">
                  <TextInput />
                </div>
              ) : (
                <Navigate to="/login" replace />
              )
            }
          />
          <Route
            path="/analysis"
            element={
              isAuthenticated ? (
                <div className="main-content">
                  <HeatMap />
                </div>
              ) : (
                <Navigate to="/login" replace />
              )
            }
          />
          <Route
            path="/profile"
            element={
              isAuthenticated ? (
                <div className="main-content">
                  <ProfileManager />
                </div>
              ) : (
                <Navigate to="/login" replace />
              )
            }
          />
          <Route
            path="/rewrite"
            element={
              isAuthenticated ? (
                <div className="main-content">
                  <RewriteInterface />
                </div>
              ) : (
                <Navigate to="/login" replace />
              )
            }
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
