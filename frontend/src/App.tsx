import { useState, useEffect, lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { ThemeProvider } from './contexts/ThemeContext';
import { ToastProvider } from './contexts/ToastContext';
import ErrorBoundary from './components/ErrorBoundary/ErrorBoundary';
import OfflineBanner from './components/OfflineBanner/OfflineBanner';
import Navbar from './components/layout/Navbar';
import Sidebar from './components/layout/Sidebar';
import Footer from './components/layout/Footer';
import Container from './components/layout/Container';
import Spinner from './components/ui/Spinner';

// Lazy load route components for code splitting
const TextInput = lazy(() => import('./components/TextInput/TextInput'));
const HeatMap = lazy(() => import('./components/HeatMap/HeatMap'));
const ProfileManager = lazy(() => import('./components/ProfileManager/ProfileManager'));
const RewriteInterface = lazy(() => import('./components/RewriteInterface/RewriteInterface'));
const Login = lazy(() => import('./components/Login/Login'));
const Dashboard = lazy(() => import('./components/Dashboard/Dashboard'));
const History = lazy(() => import('./components/Dashboard/History'));
const BatchAnalysis = lazy(() => import('./components/BatchAnalysis/BatchAnalysis'));
const BatchResults = lazy(() => import('./components/BatchResults/BatchResults'));
const ApiDashboard = lazy(() => import('./components/ApiDashboard/ApiDashboard'));

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
      <OfflineBanner />
      <Navbar isAuthenticated={isAuthenticated} onLogout={handleLogout} />
      
      {isAuthenticated && <Sidebar />}
      
      <main className={isAuthenticated ? 'flex-1 lg:ml-64' : 'flex-1'}>
        <Suspense fallback={
          <div className="flex items-center justify-center min-h-[400px]">
            <Spinner size="lg" />
          </div>
        }>
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
              <Route
                path="/batch"
                element={
                  isAuthenticated ? (
                    <Container className="py-8">
                      <BatchAnalysis />
                    </Container>
                  ) : (
                    <Navigate to="/login" replace />
                  )
                }
              />
              <Route
                path="/batch/:jobId"
                element={
                  isAuthenticated ? (
                    <Container className="py-8">
                      <BatchResults />
                    </Container>
                  ) : (
                    <Navigate to="/login" replace />
                  )
                }
              />
              <Route
                path="/api-dash"
                element={
                  isAuthenticated ? (
                    <Container className="py-8">
                      <ApiDashboard />
                    </Container>
                  ) : (
                    <Navigate to="/login" replace />
                  )
                }
              />
            </Routes>
          </motion.div>
        </AnimatePresence>
        </Suspense>
      </main>
      
      {isAuthenticated && <Footer />}
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <ToastProvider>
          <Router>
            <AnimatedRoutes />
          </Router>
        </ToastProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
