import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useToast } from '@/components/ui/use-toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Home } from 'lucide-react';

export default function GoogleCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();

  useEffect(() => {
    const token = searchParams.get('token');
    const error = searchParams.get('error');

    if (error) {
      toast({
        title: 'Authentication failed',
        description: error,
        variant: 'destructive',
      });
      navigate('/login');
      return;
    }

    if (token) {
      // Store the token
      localStorage.setItem('authToken', token);

      // Fetch user info
      fetch('http://localhost:8000/api/v1/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
        .then(res => res.json())
        .then(user => {
          localStorage.setItem('user', JSON.stringify(user));
          toast({
            title: 'Login successful!',
            description: `Welcome, ${user.username}!`,
          });
          navigate('/dashboard');
        })
        .catch(() => {
          toast({
            title: 'Error',
            description: 'Failed to fetch user information',
            variant: 'destructive',
          });
          navigate('/login');
        });
    } else {
      toast({
        title: 'Error',
        description: 'No authentication token received',
        variant: 'destructive',
      });
      navigate('/login');
    }
  }, [searchParams, navigate, toast]);

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
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-center">Authenticating...</CardTitle>
        </CardHeader>
        <CardContent className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </CardContent>
      </Card>
    </div>
  );
}
