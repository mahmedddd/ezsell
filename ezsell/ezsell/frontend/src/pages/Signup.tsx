import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { authService } from '@/lib/api';
import { useToast } from '@/components/ui/use-toast';
import { Check, X, Loader2, Store, Sparkles, Home } from 'lucide-react';

export default function Signup() {
  const [step, setStep] = useState(1); // 1: Email, 2: Verify Code, 3: Complete Registration
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
  });
  const [verificationCode, setVerificationCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [usernameStatus, setUsernameStatus] = useState<'idle' | 'checking' | 'available' | 'taken'>('idle');
  const usernameCheckTimeout = useRef<NodeJS.Timeout | null>(null);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    
    // Trigger username check when username field changes
    if (e.target.name === 'username') {
      checkUsernameAvailability(e.target.value);
    }
  };

  const checkUsernameAvailability = (username: string) => {
    // Clear previous timeout
    if (usernameCheckTimeout.current) {
      clearTimeout(usernameCheckTimeout.current);
    }

    // Reset status if username is empty or too short
    if (!username || username.length < 3) {
      setUsernameStatus('idle');
      return;
    }

    // Set checking status
    setUsernameStatus('checking');

    // Debounce the API call (wait 500ms after user stops typing)
    usernameCheckTimeout.current = setTimeout(async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/v1/check-username/${encodeURIComponent(username)}`);
        const data = await response.json();
        
        setUsernameStatus(data.available ? 'available' : 'taken');
      } catch (error) {
        console.error('Error checking username:', error);
        setUsernameStatus('idle');
      }
    }, 500);
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (usernameCheckTimeout.current) {
        clearTimeout(usernameCheckTimeout.current);
      }
    };
  }, []);

  const handleSendCode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.email) {
      toast({
        title: 'Email required',
        description: 'Please enter your email address',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/send-verification-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: formData.email }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to send code');
      }

      toast({
        title: 'Code sent!',
        description: 'Check your email for the verification code',
      });
      setStep(2);
    } catch (error: any) {
      toast({
        title: 'Failed to send code',
        description: error.message || 'Something went wrong',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!verificationCode) {
      toast({
        title: 'Code required',
        description: 'Please enter the verification code',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/verify-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: formData.email, code: verificationCode }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Invalid code');
      }

      toast({
        title: 'Email verified!',
        description: 'Please complete your registration',
      });
      setStep(3);
    } catch (error: any) {
      toast({
        title: 'Verification failed',
        description: error.message || 'Invalid or expired code',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      console.log('Attempting registration with:', formData);
      await authService.register(formData);
      
      // Auto-login after registration
      const loginResponse = await authService.login({
        username: formData.username,
        password: formData.password,
      });
      
      localStorage.setItem('authToken', loginResponse.access_token);
      
      const user = await authService.getCurrentUser();
      localStorage.setItem('user', JSON.stringify(user));
      
      toast({
        title: 'Account created!',
        description: 'Welcome to EZSell!',
      });
      
      navigate('/dashboard');
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Registration failed. Please try again.';
      toast({
        title: 'Registration Failed',
        description: errorMessage,
        variant: 'destructive',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#f5f5f0] to-[#e8e8dc] p-4">
      <Button 
        variant="ghost" 
        onClick={() => navigate('/')} 
        className="absolute top-4 left-4 text-[#143109] hover:bg-[#143109]/10"
      >
        <Home className="mr-2 h-4 w-4" />
        Back to Home
      </Button>
      <Card className="w-full max-w-md shadow-2xl border-2 border-[#143109]/20">
        <CardHeader className="space-y-4 bg-gradient-to-r from-[#143109] to-[#AAAE7F] text-white rounded-t-lg pb-8">
          <div className="flex flex-col items-center justify-center gap-3">
            <img src="/images/ezsell-logo.png" alt="EZSELL Logo" className="h-24 w-auto bg-white rounded-lg p-2" onError={(e) => { e.currentTarget.style.display = 'none'; e.currentTarget.nextElementSibling?.classList.remove('hidden'); }} />
            <div className="hidden flex-col items-center">
              <h1 className="text-4xl font-bold tracking-tight">EZ SELL</h1>
              <p className="text-lg text-white/90 font-medium">BAICH DIAAA !!!</p>
            </div>
          </div>
          <CardTitle className="text-2xl font-bold text-center text-white">Create an account</CardTitle>
          <CardDescription className="text-center text-white/90">
            {step === 1 && 'Step 1: Verify your email'}
            {step === 2 && 'Step 2: Enter verification code'}
            {step === 3 && 'Step 3: Complete your profile'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {step === 1 && (
            <form onSubmit={handleSendCode} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                />
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Sending code...' : 'Send Verification Code'}
              </Button>
            </form>
          )}

          {step === 2 && (
            <form onSubmit={handleVerifyCode} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="code">Verification Code</Label>
                <Input
                  id="code"
                  type="text"
                  placeholder="Enter 6-digit code"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                  maxLength={6}
                  required
                />
                <p className="text-sm text-muted-foreground">
                  Code sent to {formData.email}
                </p>
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Verifying...' : 'Verify Code'}
              </Button>
              <Button
                type="button"
                variant="ghost"
                className="w-full"
                onClick={() => setStep(1)}
              >
                Change email
              </Button>
            </form>
          )}

          {step === 3 && (
            <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <div className="relative">
                <Input
                  id="username"
                  name="username"
                  type="text"
                  placeholder="Choose a username"
                  value={formData.username}
                  onChange={handleChange}
                  className={
                    usernameStatus === 'available' ? 'pr-10 border-green-500' :
                    usernameStatus === 'taken' ? 'pr-10 border-red-500' : 'pr-10'
                  }
                  required
                  minLength={3}
                />
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  {usernameStatus === 'checking' && (
                    <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
                  )}
                  {usernameStatus === 'available' && (
                    <Check className="h-4 w-4 text-green-500" />
                  )}
                  {usernameStatus === 'taken' && (
                    <X className="h-4 w-4 text-red-500" />
                  )}
                </div>
              </div>
              {usernameStatus === 'available' && (
                <p className="text-sm text-green-600">Username is available!</p>
              )}
              {usernameStatus === 'taken' && (
                <p className="text-sm text-red-600">Username is already taken</p>
              )}
              {formData.username.length > 0 && formData.username.length < 3 && (
                <p className="text-sm text-gray-500">Username must be at least 3 characters</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email (Verified ✓)</Label>
              <Input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                disabled
                className="bg-muted"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="full_name">Full Name</Label>
              <Input
                id="full_name"
                name="full_name"
                type="text"
                placeholder="Enter your full name"
                value={formData.full_name}
                onChange={handleChange}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                name="password"
                type="password"
                placeholder="Choose a password"
                value={formData.password}
                onChange={handleChange}
                required
              />
            </div>
            <Button 
              type="submit" 
              className="w-full" 
              disabled={loading || usernameStatus === 'taken' || usernameStatus === 'checking'}
            >
              {loading ? 'Creating account...' : 'Sign up'}
            </Button>
          </form>
          )}
          
          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">Or continue with</span>
            </div>
          </div>
          
          <Button
            type="button"
            variant="outline"
            className="w-full"
            onClick={() => window.location.href = 'http://localhost:8000/api/v1/auth/google/login'}
          >
            <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
            </svg>
            Continue with Google
          </Button>
          
          <div className="mt-4 text-center text-sm">
            Already have an account?{' '}
            <Link to="/login" className="text-primary hover:underline">
              Login
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
