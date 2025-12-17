import { useLocation, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { Button } from '@/components/ui/button';
import { Home } from 'lucide-react';

const NotFound = () => {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-[#f5f5f0] to-[#e8e8dc]">
      <div className="text-center">
        <h1 className="mb-4 text-6xl font-bold text-[#143109]">404</h1>
        <p className="mb-8 text-2xl text-slate-700">Oops! Page not found</p>
        <Button 
          onClick={() => navigate('/')} 
          className="bg-[#143109] hover:bg-[#143109]/90 text-white"
        >
          <Home className="mr-2 h-4 w-4" />
          Back to Home
        </Button>
      </div>
    </div>
  );
};

export default NotFound;
