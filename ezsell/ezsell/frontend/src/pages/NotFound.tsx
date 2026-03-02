import { useLocation, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Home, ArrowLeft } from "lucide-react";

const NotFound = () => {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    console.error("404 Error: User navigated to non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6">
      {/* Animated 404 */}
      <div className="text-center max-w-md">
        <div className="relative mb-6">
          <div className="text-[120px] md:text-[160px] font-black leading-none gradient-text select-none animate-fade-in-up">
            404
          </div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-6xl animate-float">🔍</div>
          </div>
        </div>

        <h1 className="text-2xl md:text-3xl font-black text-foreground mb-3 animate-fade-in-up delay-100">
          Page Not Found
        </h1>
        <p className="text-muted-foreground mb-8 max-w-xs mx-auto animate-fade-in-up delay-200">
          The page at <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono">{location.pathname}</code> doesn't exist.
        </p>

        <div className="flex flex-col sm:flex-row gap-3 justify-center animate-fade-in-up delay-300">
          <Button
            onClick={() => navigate(-1)}
            variant="outline"
            className="rounded-xl h-11 px-6 font-bold border-2 hover:border-primary/50 hover:text-primary transition-all"
          >
            <ArrowLeft className="mr-2 h-4 w-4" /> Go Back
          </Button>
          <Button
            onClick={() => navigate("/")}
            className="rounded-xl h-11 px-6 font-bold bg-primary hover:bg-primary/90 shadow-lg shadow-primary/25 hover:-translate-y-0.5 transition-all"
          >
            <Home className="mr-2 h-4 w-4" /> Back to Home
          </Button>
        </div>
      </div>
    </div>
  );
};

export default NotFound;
