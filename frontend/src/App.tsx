import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { ThemeProvider } from './contexts/ThemeContext';
import { ToastProvider } from './contexts/ToastContext';
import TextInput from './components/TextInput/TextInput';
import HeatMap from './components/HeatMap/HeatMap';
import ProfileManager from './components/ProfileManager/ProfileManager';
import RewriteInterface from './components/RewriteInterface/RewriteInterface';
import Login from './components/Login/Login';
import Dashboard from './components/Dashboard/Dashboard';
import History from './components/Dashboard/History';
import Navbar from './components/layout/Navbar';
import Sidebar from './components/layout/Sidebar';
import Footer from './components/layout/Footer';
import Container from './components/layout/Container';
import Spinner from './components/ui/Spinner';

function AnimatedRoutes() {
  const location = useLocation();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    setIsAuthenticated(!!token);
    setLoading(false);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setIsAuthenticated(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner size="lg" />
      </div>
    );
  }

  const pageVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
  };

  const pageTransition = {
    type: 'tween',
    ease: 'anticipate',
    duration: 0.3,
  };

  return (
    <div className="flex min-h-screen flex-col bg-gray-50 dark:bg-gray-900">
      <Navbar isAuthenticated={isAuthenticated} onLogout={handleLogout} />
      
      {isAuthenticated && <Sidebar />}
      
      <main className={isAuthenticated ? 'flex-1 lg:ml-64' : 'flex-1'}>
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={location.pathname}
            initial="initial"
            animate="animate"
            exit="exit"
            variants={pageVariants}
            transition={pageTransition}
          >
            <Routes location={location}>
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
                    <Container className="py-8">
                      <Dashboard />
                    </Container>
                  ) : (
                    <Navigate to="/login" replace />
                  )
                }
              />
              <Route
                path="/analyze"
                element={
                  isAuthenticated ? (
                    <Container className="py-8">
                      <TextInput />
                    </Container>
                  ) : (
                    <Navigate to="/login" replace />
                  )
                }
              />
              <Route
                path="/analysis"
                element={
                  isAuthenticated ? (
                    <Container className="py-8">
                      <HeatMap />
                    </Container>
                  ) : (
                    <Navigate to="/login" replace />
                  )
                }
              />
              <Route
                path="/history"
                element={
                  isAuthenticated ? (
                    <Container className="py-8">
                      <History />
                    </Container>
                  ) : (
                    <Navigate to="/login" replace />
                  )
                }
              />
              <Route
                path="/profile"
                element={
                  isAuthenticated ? (
                    <Container className="py-8">
                      <ProfileManager />
                    </Container>
                  ) : (
                    <Navigate to="/login" replace />
                  )
                }
              />
              <Route
                path="/rewrite"
                element={
                  isAuthenticated ? (
                    <Container className="py-8">
                      <RewriteInterface />
                    </Container>
                  ) : (
                    <Navigate to="/login" replace />
                  )
                }
              />
            </Routes>
          </motion.div>
        </AnimatePresence>
      </main>
      
      {isAuthenticated && <Footer />}
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <Router>
          <AnimatedRoutes />
        </Router>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;
