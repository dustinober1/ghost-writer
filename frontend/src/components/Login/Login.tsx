import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI, getErrorMessage } from '../../services/api';
import { useToast } from '../../contexts/ToastContext';
import Card, { CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card';
import Input from '../ui/Input';
import Button from '../ui/Button';
import Alert from '../ui/Alert';
import { Mail, Lock, Github, Chrome } from 'lucide-react';

interface LoginProps {
  onLogin: () => void;
}

export default function Login({ onLogin }: LoginProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { success, error: showError } = useToast();

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Email is invalid';
    }

    if (!password) {
      newErrors.password = 'Password is required';
    } else if (password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    if (!isLogin) {
      if (!confirmPassword) {
        newErrors.confirmPassword = 'Please confirm your password';
      } else if (password !== confirmPassword) {
        newErrors.confirmPassword = 'Passwords do not match';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      if (isLogin) {
        await authAPI.login(email, password);
        success('Login successful!');
        onLogin();
        navigate('/');
      } else {
        await authAPI.register(email, password);
        success('Registration successful! Please login.');
        setIsLogin(true);
        setPassword('');
        setConfirmPassword('');
      }
    } catch (err: any) {
      console.error('Login/Register error:', err);
      const errorMsg = getErrorMessage(err);
      showError(errorMsg);
      setErrors({ submit: errorMsg });
    } finally {
      setLoading(false);
    }
  };

  const handleSocialLogin = (provider: 'google' | 'github') => {
    // Placeholder for social login
    showError(`${provider.charAt(0).toUpperCase() + provider.slice(1)} login coming soon!`);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-primary-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-primary-600 to-primary-800 dark:from-primary-400 dark:to-primary-600 bg-clip-text text-transparent mb-2">
            Ghostwriter Forensic Analytics
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            {isLogin ? 'Sign in to your account' : 'Create a new account'}
          </p>
        </div>

        <Card variant="elevated">
          <CardHeader>
            <CardTitle className="text-2xl">{isLogin ? 'Welcome back' : 'Get started'}</CardTitle>
            <CardDescription>
              {isLogin
                ? 'Enter your credentials to access your account'
                : 'Create an account to start analyzing text'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Social Login Buttons */}
            <div className="grid grid-cols-2 gap-3 mb-6">
              <Button
                variant="outline"
                onClick={() => handleSocialLogin('google')}
                className="w-full"
                disabled={loading}
              >
                <Chrome className="h-4 w-4 mr-2" />
                Google
              </Button>
              <Button
                variant="outline"
                onClick={() => handleSocialLogin('github')}
                className="w-full"
                disabled={loading}
              >
                <Github className="h-4 w-4 mr-2" />
                GitHub
              </Button>
            </div>

            <div className="relative mb-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200 dark:border-gray-700" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400">
                  Or continue with email
                </span>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                type="email"
                label="Email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (errors.email) setErrors({ ...errors, email: '' });
                }}
                error={!!errors.email}
                helperText={errors.email}
                placeholder="you@example.com"
                disabled={loading}
                required
              />

              <div>
                <Input
                  type="password"
                  label="Password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (errors.password) setErrors({ ...errors, password: '' });
                  }}
                  error={!!errors.password}
                  helperText={errors.password || (!isLogin ? 'Must be at least 8 characters' : undefined)}
                  placeholder="••••••••"
                  disabled={loading}
                  required
                  minLength={8}
                />
              </div>

              {!isLogin && (
                <Input
                  type="password"
                  label="Confirm Password"
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value);
                    if (errors.confirmPassword) setErrors({ ...errors, confirmPassword: '' });
                  }}
                  error={!!errors.confirmPassword}
                  helperText={errors.confirmPassword}
                  placeholder="••••••••"
                  disabled={loading}
                  required
                />
              )}

              {isLogin && (
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <input
                      type="checkbox"
                      className="rounded border-gray-300 dark:border-gray-700 text-primary-600 focus:ring-primary-500"
                    />
                    Remember me
                  </label>
                  <button
                    type="button"
                    className="text-sm text-primary-600 dark:text-primary-400 hover:underline"
                  >
                    Forgot password?
                  </button>
                </div>
              )}

              {errors.submit && (
                <Alert variant="error" title="Error">
                  {errors.submit}
                </Alert>
              )}

              <Button
                type="submit"
                variant="primary"
                className="w-full"
                isLoading={loading}
                disabled={loading}
              >
                {isLogin ? 'Sign in' : 'Create account'}
              </Button>
            </form>

            <div className="mt-6 text-center text-sm">
              <span className="text-gray-600 dark:text-gray-400">
                {isLogin ? "Don't have an account? " : 'Already have an account? '}
              </span>
              <button
                type="button"
                onClick={() => {
                  setIsLogin(!isLogin);
                  setErrors({});
                  setPassword('');
                  setConfirmPassword('');
                }}
                className="text-primary-600 dark:text-primary-400 font-medium hover:underline"
              >
                {isLogin ? 'Sign up' : 'Sign in'}
              </button>
            </div>
          </CardContent>
        </Card>

        <p className="mt-6 text-center text-xs text-gray-500 dark:text-gray-400">
          By continuing, you agree to our Terms of Service and Privacy Policy
        </p>
      </div>
    </div>
  );
}
