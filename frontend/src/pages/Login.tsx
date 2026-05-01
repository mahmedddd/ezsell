import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authService, rotateSessionId } from '../lib/api.ts';
import { useToast } from "@/components/ui/use-toast";
import { Eye, EyeOff, ArrowLeft, Lock, User, Sparkles } from "lucide-react";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await authService.login({ username, password });
      localStorage.setItem("authToken", response.access_token);
      const user = await authService.getCurrentUser();
      localStorage.setItem("user", JSON.stringify(user));
      rotateSessionId(); // Clear previous anonymous user context
      toast({ title: "Welcome back! 👋", description: `Logged in as ${user.username}` });
      navigate("/dashboard");
    } catch (error: any) {
      let msg = "Invalid username or password";
      const detail = error.response?.data?.detail;
      if (detail) {
        msg = Array.isArray(detail) ? detail.map((e: any) => e.msg || JSON.stringify(e)).join(", ") : typeof detail === "string" ? detail : JSON.stringify(detail);
      } else if (error.response?.status === 401) { msg = "Incorrect username or password. Please try again."; }
      else if (error.response?.status === 404) { msg = "User not found. Please check your username or sign up."; }
      else if (!error.response) { msg = "Unable to connect to server."; }
      toast({ title: "Login Failed", description: msg, variant: "destructive", duration: 5000 });
    } finally { setLoading(false); }
  };

  const googleLogin = () => { window.location.href = "/api/v1/auth/google/login"; };

  return (
    <div className="min-h-screen flex">
      {/* ── Left panel: brand ── */}
      <div className="hidden lg:flex lg:w-1/2 hero-mesh flex-col items-center justify-center p-12 relative overflow-hidden">
        {/* decorative circles */}
        <div className="absolute top-0 right-0 w-80 h-80 rounded-full bg-white/5 blur-3xl" />
        <div className="absolute bottom-0 left-0 w-96 h-96 rounded-full bg-black/10 blur-3xl" />

        <div className="relative z-10 text-center max-w-xs">
          <img src="/images/logo.jpg" alt="EzSell" className="h-28 w-auto rounded-3xl shadow-2xl ring-4 ring-white/20 mx-auto mb-8 animate-float"
            onError={e => { e.currentTarget.style.display = "none"; }} />
          <h2 className="text-4xl font-black text-white mb-4 leading-tight">
            Pakistan's Smartest Marketplace
          </h2>
          <p className="text-white/70 text-base leading-relaxed">
            Buy and sell mobiles, laptops, furniture and more — safely, quickly, and for free.
          </p>

          <div className="mt-10 grid grid-cols-2 gap-4 text-center">
            {[
              { n: "5K+", l: "Active Listings" },
              { n: "100%", l: "Verified Sellers" },
              { n: "24/7", l: "Support" },
              { n: "Free", l: "To Use" },
            ].map(({ n, l }) => (
              <div key={l} className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/15">
                <div className="text-2xl font-black text-white">{n}</div>
                <div className="text-xs text-white/60 font-medium mt-0.5">{l}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Right panel: form ── */}
      <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-[hsl(68,30%,97%)] to-[hsl(50,25%,95%)] p-6">
        <div className="w-full max-w-md animate-scale-in">
          {/* Back button */}
          <button
            onClick={() => navigate("/")}
            className="mb-6 flex items-center gap-2 text-sm font-semibold text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Home
          </button>

          {/* Card */}
          <div className="bg-white rounded-3xl shadow-[var(--shadow-xl)] border border-border/50 overflow-hidden">
            {/* Card header */}
            <div className="px-8 pt-8 pb-6">
              {/* Mobile logo */}
              <div className="lg:hidden flex justify-center mb-6">
                <img src="/images/logo.jpg" alt="EzSell" className="h-16 w-auto rounded-2xl shadow-lg"
                  onError={e => { e.currentTarget.style.display = "none"; }} />
              </div>

              <div className="flex items-center gap-2 mb-1">
                <div className="h-8 w-8 rounded-xl bg-primary/10 flex items-center justify-center">
                  <Sparkles className="h-4 w-4 text-primary" />
                </div>
                <h1 className="text-2xl font-black text-foreground">Welcome back</h1>
              </div>
              <p className="text-sm text-muted-foreground">Sign in to your EzSell account</p>
            </div>

            <div className="px-8 pb-8 space-y-5">
              {/* Google */}
              <button
                onClick={googleLogin}
                className="w-full flex items-center justify-center gap-3 h-12 rounded-2xl border-2 border-border hover:border-primary/40 hover:bg-primary/5 font-semibold text-sm text-foreground/80 hover:text-foreground transition-all duration-200"
              >
                <svg className="h-5 w-5" viewBox="0 0 24 24">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                </svg>
                Continue with Google
              </button>

              {/* Divider */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center"><span className="w-full border-t border-border/50" /></div>
                <div className="relative flex justify-center text-xs text-muted-foreground">
                  <span className="bg-white px-3 uppercase tracking-wider">or</span>
                </div>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="username" className="text-sm font-semibold">Username</Label>
                  <div className="relative">
                    <User className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input id="username" type="text" placeholder="Enter your username" value={username}
                      onChange={e => setUsername(e.target.value)} required
                      className="pl-10 h-12 rounded-xl border-border/60 focus:border-primary/50 focus:ring-2 focus:ring-primary/10 transition-all font-medium" />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="password" className="text-sm font-semibold">Password</Label>
                    <Link to="/forgot-password" className="text-xs text-primary hover:underline font-medium">Forgot password?</Link>
                  </div>
                  <div className="relative">
                    <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input id="password" type={showPw ? "text" : "password"} placeholder="Enter your password" value={password}
                      onChange={e => setPassword(e.target.value)} required
                      className="pl-10 pr-10 h-12 rounded-xl border-border/60 focus:border-primary/50 focus:ring-2 focus:ring-primary/10 transition-all font-medium" />
                    <button type="button" onClick={() => setShowPw(!showPw)}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors">
                      {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <Button type="submit" disabled={loading}
                  className="w-full h-12 rounded-2xl bg-primary hover:bg-primary/90 font-bold text-base shadow-lg shadow-primary/25 hover:shadow-primary/35 hover:-translate-y-0.5 transition-all duration-200">
                  {loading ? (
                    <span className="flex items-center gap-2"><span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Signing in...</span>
                  ) : "Sign In"}
                </Button>
              </form>

              <p className="text-center text-sm text-muted-foreground">
                Don&apos;t have an account?{" "}
                <Link to="/signup" className="text-primary font-bold hover:underline">Create one free</Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
