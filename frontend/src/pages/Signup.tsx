import { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authService } from '../lib/api.ts';
import { useToast } from "@/components/ui/use-toast";
import { Check, X, Loader2, Eye, EyeOff, ArrowLeft, Mail, User, Phone, MapPin, Lock, Sparkles } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const STEPS = ["Verify Email", "Enter Code", "Complete Profile"];

export default function Signup() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({ username: "", email: "", password: "", full_name: "", phone: "", location: "Islamabad" });
  const [verificationCode, setVerificationCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);
  const [usernameStatus, setUsernameStatus] = useState<"idle" | "checking" | "available" | "taken">("idle");
  const usernameTimer = useRef<any>(null);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
    if (e.target.name === "username") checkUsername(e.target.value);
  };

  const checkUsername = (u: string) => {
    clearTimeout(usernameTimer.current);
    if (!u || u.length < 3) { setUsernameStatus("idle"); return; }
    setUsernameStatus("checking");
    usernameTimer.current = setTimeout(async () => {
      try {
        const res = await fetch(`/api/v1/check-username/${encodeURIComponent(u)}`);
        const data = await res.json();
        setUsernameStatus(data.available ? "available" : "taken");
      } catch { setUsernameStatus("idle"); }
    }, 500);
  };

  useEffect(() => () => clearTimeout(usernameTimer.current), []);

  const handleSendCode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.email) { toast({ title: "Email required", variant: "destructive" }); return; }
    setLoading(true);
    try {
      const res = await fetch("/api/v1/send-verification-code", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: formData.email }),
      });
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail || "Failed to send code"); }
      toast({ title: "Code sent! 📬", description: "Check your email for the verification code" });
      setStep(2);
    } catch (error: any) {
      let msg = "Failed to send verification code";
      if (error.message?.includes("Email already registered")) msg = "This email is already registered. Please login instead.";
      else if (error.message) msg = error.message;
      toast({ title: "Failed to send code", description: msg, variant: "destructive", duration: 7000 });
    } finally { setLoading(false); }
  };

  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!verificationCode) { toast({ title: "Code required", variant: "destructive" }); return; }
    setLoading(true);
    try {
      const res = await fetch("/api/v1/verify-code", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: formData.email, code: verificationCode }),
      });
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail || "Invalid code"); }
      toast({ title: "Email verified! ✅", description: "Complete your profile" });
      setStep(3);
    } catch (error: any) {
      toast({ title: "Verification failed", description: error.message || "Invalid or expired code", variant: "destructive" });
    } finally { setLoading(false); }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.phone.length !== 11) {
      toast({
        title: "Invalid phone number",
        description: "Please enter exactly 11 digits (e.g., 03123456789)",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);
    try {
      await authService.register(formData);
      const loginRes = await authService.login({ username: formData.username, password: formData.password });
      localStorage.setItem("authToken", loginRes.access_token);
      const user = await authService.getCurrentUser();
      localStorage.setItem("user", JSON.stringify(user));
      const { rotateSessionId } = await import('../lib/api.ts');
      rotateSessionId();
      toast({ title: "Account created! 🎉", description: "Welcome to EzSell!" });
      navigate("/dashboard");
    } catch (error: any) {
      let msg = "Registration failed. Please try again.";
      const detail = error.response?.data?.detail;
      if (detail) msg = Array.isArray(detail) ? detail.map((e: any) => e.msg || JSON.stringify(e)).join(", ") : typeof detail === "string" ? detail : JSON.stringify(detail);
      else if (error.message) msg = error.message;
      toast({ title: "Registration Failed", description: msg, variant: "destructive", duration: 5000 });
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen flex">
      {/* ── Left panel ── */}
      <div className="hidden lg:flex lg:w-2/5 hero-mesh flex-col items-center justify-center p-12 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 rounded-full bg-white/5 blur-3xl" />
        <div className="absolute bottom-0 left-0 w-96 h-96 rounded-full bg-black/10 blur-3xl" />
        <div className="relative z-10 text-center max-w-xs">
          <img src="/images/logo.jpg" alt="EzSell" className="h-24 w-auto rounded-3xl shadow-2xl ring-4 ring-white/20 mx-auto mb-8 animate-float"
            onError={e => { e.currentTarget.style.display = "none"; }} />
          <h2 className="text-3xl font-black text-white mb-4 leading-tight">Join EzSell Today</h2>
          <p className="text-white/70 text-base leading-relaxed">Start selling in minutes. Reach thousands of buyers in Twin Cities for free.</p>
          {/* Step progress visual */}
          <div className="mt-10 space-y-3">
            {STEPS.map((s, i) => (
              <div key={s} className={`flex items-center gap-3 px-4 py-3 rounded-2xl transition-all ${step > i + 1 ? "bg-white/20" : step === i + 1 ? "bg-white/15 ring-1 ring-white/30" : "bg-white/5 opacity-60"}`}>
                <div className={`h-7 w-7 rounded-full flex items-center justify-center text-xs font-black flex-shrink-0 ${step > i + 1 ? "bg-green-400 text-green-900" : step === i + 1 ? "bg-white text-primary" : "bg-white/20 text-white"}`}>
                  {step > i + 1 ? <Check className="h-4 w-4" /> : i + 1}
                </div>
                <span className="text-sm font-semibold text-white">{s}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Right panel ── */}
      <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-[hsl(68,30%,97%)] to-[hsl(50,25%,95%)] p-6 overflow-y-auto">
        <div className="w-full max-w-md animate-scale-in py-6">
          <button onClick={() => navigate("/")} className="mb-6 flex items-center gap-2 text-sm font-semibold text-muted-foreground hover:text-foreground transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back to Home
          </button>

          <div className="bg-white rounded-3xl shadow-[var(--shadow-xl)] border border-border/50 overflow-hidden">
            {/* Header */}
            <div className="px-8 pt-8 pb-5">
              <div className="lg:hidden flex justify-center mb-5">
                <img src="/images/logo.jpg" alt="EzSell" className="h-14 w-auto rounded-2xl shadow-lg"
                  onError={e => { e.currentTarget.style.display = "none"; }} />
              </div>
              {/* Mobile step indicator */}
              <div className="lg:hidden flex items-center gap-1.5 mb-5">
                {STEPS.map((_, i) => (
                  <div key={i} className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${step > i ? "bg-primary" : "bg-muted"}`} />
                ))}
              </div>
              <div className="flex items-center gap-2 mb-0.5">
                <div className="h-8 w-8 rounded-xl bg-primary/10 flex items-center justify-center"><Sparkles className="h-4 w-4 text-primary" /></div>
                <h1 className="text-2xl font-black text-foreground">Create Account</h1>
              </div>
              <p className="text-sm text-muted-foreground">Step {step} of 3 — {STEPS[step - 1]}</p>
            </div>

            <div className="px-8 pb-8 space-y-5">
              {/* Step 1: Email */}
              {step === 1 && (
                <form onSubmit={handleSendCode} className="space-y-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="email-s1" className="text-sm font-semibold">Email Address</Label>
                    <div className="relative">
                      <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input id="email-s1" name="email" type="email" placeholder="you@example.com" value={formData.email}
                        onChange={handleChange} required
                        className="pl-10 h-12 rounded-xl border-border/60 focus:border-primary/50 focus:ring-2 focus:ring-primary/10 transition-all font-medium" />
                    </div>
                  </div>
                  <Button type="submit" disabled={loading} className="w-full h-12 rounded-2xl bg-primary hover:bg-primary/90 font-bold text-base shadow-lg shadow-primary/25 hover:-translate-y-0.5 transition-all">
                    {loading ? <span className="flex items-center gap-2"><span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Sending...</span> : "Send Verification Code →"}
                  </Button>
                  <button type="button" onClick={googleLogin} className="w-full flex items-center justify-center gap-3 h-12 rounded-2xl border-2 border-border hover:border-primary/40 hover:bg-primary/5 font-semibold text-sm text-foreground/80 hover:text-foreground transition-all">
                    <GoogleIcon /> Continue with Google
                  </button>
                  <p className="text-center text-sm text-muted-foreground">Already have an account?{" "}<Link to="/login" className="text-primary font-bold hover:underline">Sign in</Link></p>
                </form>
              )}

              {/* Step 2: Code */}
              {step === 2 && (
                <form onSubmit={handleVerifyCode} className="space-y-4">
                  <div className="bg-primary/5 border border-primary/15 rounded-2xl px-4 py-3 text-sm">
                    <p className="font-semibold text-foreground mb-0.5">Code sent to:</p>
                    <p className="text-primary font-bold">{formData.email}</p>
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="code" className="text-sm font-semibold">Verification Code</Label>
                    <Input id="code" type="text" placeholder="Enter 6-digit code" value={verificationCode}
                      onChange={e => setVerificationCode(e.target.value)} maxLength={6} required
                      className="h-14 rounded-xl border-border/60 text-center text-2xl font-black tracking-widest focus:border-primary/50 focus:ring-2 focus:ring-primary/10 transition-all" />
                  </div>
                  <Button type="submit" disabled={loading} className="w-full h-12 rounded-2xl bg-primary hover:bg-primary/90 font-bold text-base shadow-lg shadow-primary/25 hover:-translate-y-0.5 transition-all">
                    {loading ? <span className="flex items-center gap-2"><span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Verifying...</span> : "Verify Code ✓"}
                  </Button>
                  <button type="button" onClick={() => setStep(1)} className="w-full h-10 rounded-2xl text-sm font-semibold text-muted-foreground hover:text-foreground hover:bg-muted transition-all">
                    ← Change email
                  </button>
                </form>
              )}

              {/* Step 3: Profile */}
              {step === 3 && (
                <form onSubmit={handleSubmit} className="space-y-4">
                  {/* Username */}
                  <div className="space-y-1.5">
                    <Label htmlFor="username-s3" className="text-sm font-semibold">Username</Label>
                    <div className="relative">
                      <User className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input id="username-s3" name="username" type="text" placeholder="Choose a username" value={formData.username}
                        onChange={handleChange} required minLength={3}
                        className={`pl-10 pr-10 h-12 rounded-xl border-2 focus:ring-2 focus:ring-primary/10 transition-all font-medium ${usernameStatus === "available" ? "border-emerald-400 focus:border-emerald-500" : usernameStatus === "taken" ? "border-red-400 focus:border-red-500" : "border-border/60 focus:border-primary/50"}`}
                      />
                      <div className="absolute right-3.5 top-1/2 -translate-y-1/2">
                        {usernameStatus === "checking" && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
                        {usernameStatus === "available" && <Check className="h-4 w-4 text-emerald-500" />}
                        {usernameStatus === "taken" && <X className="h-4 w-4 text-red-500" />}
                      </div>
                    </div>
                    {usernameStatus === "available" && <p className="text-xs text-emerald-600 font-semibold">✓ Username is available</p>}
                    {usernameStatus === "taken" && <p className="text-xs text-red-600 font-semibold">✗ Username is taken</p>}
                  </div>

                  {/* Email (verified) */}
                  <div className="space-y-1.5">
                    <Label className="text-sm font-semibold">Email <span className="text-emerald-600 font-normal">(Verified ✓)</span></Label>
                    <Input value={formData.email} disabled className="h-12 rounded-xl bg-emerald-50 border-emerald-200 text-emerald-800 font-medium" />
                  </div>

                  {/* Full name & phone */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label htmlFor="full_name" className="text-sm font-semibold">Full Name</Label>
                      <Input id="full_name" name="full_name" type="text" placeholder="Your name" value={formData.full_name}
                        onChange={handleChange} className="h-12 rounded-xl border-border/60 focus:border-primary/50 focus:ring-2 focus:ring-primary/10 transition-all font-medium" />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="phone" className="text-sm font-semibold">Phone <span className="text-red-500">*</span></Label>
                      <div className="relative">
                        <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="phone"
                          name="phone"
                          type="tel"
                          placeholder="03xxxxxxxxx"
                          value={formData.phone}
                          onChange={(e) => {
                            const val = e.target.value.replace(/\D/g, "").slice(0, 11);
                            setFormData(prev => ({ ...prev, phone: val }));
                          }}
                          required
                          maxLength={11}
                          className="pl-9 h-12 rounded-xl border-border/60 focus:border-primary/50 focus:ring-2 focus:ring-primary/10 transition-all font-medium tracking-wider"
                        />
                      </div>
                    </div>
                  </div>
                  <p className="text-[11px] text-muted-foreground -mt-2 flex items-center gap-1">
                    <span>💡</span> Enter exactly 11 digits starting with 03
                  </p>

                  {/* Location */}
                  <div className="space-y-1.5">
                    <Label className="text-sm font-semibold flex items-center gap-1"><MapPin className="h-3.5 w-3.5" /> Location</Label>
                    <Select value={formData.location} onValueChange={v => setFormData(p => ({ ...p, location: v }))}>
                      <SelectTrigger className="h-12 rounded-xl border-border/60 font-medium focus:ring-2 focus:ring-primary/10">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="rounded-xl">
                        <SelectItem value="Islamabad">Islamabad</SelectItem>
                        <SelectItem value="Rawalpindi">Rawalpindi</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-[11px] text-primary font-medium">🏙️ Currently serving Twin Cities (Islamabad / Rawalpindi)</p>
                  </div>

                  {/* Password */}
                  <div className="space-y-1.5">
                    <Label htmlFor="password-s3" className="text-sm font-semibold">Password</Label>
                    <div className="relative">
                      <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input id="password-s3" name="password" type={showPw ? "text" : "password"} placeholder="Choose a strong password" value={formData.password}
                        onChange={handleChange} required className="pl-10 pr-10 h-12 rounded-xl border-border/60 focus:border-primary/50 focus:ring-2 focus:ring-primary/10 transition-all font-medium" />
                      <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors">
                        {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>

                  <Button type="submit" disabled={loading || usernameStatus === "taken" || usernameStatus === "checking"}
                    className="w-full h-12 rounded-2xl bg-primary hover:bg-primary/90 font-bold text-base shadow-lg shadow-primary/25 hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none">
                    {loading ? <span className="flex items-center gap-2"><span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Creating account...</span> : "Create Account 🎉"}
                  </Button>
                  <p className="text-center text-sm text-muted-foreground">Already have an account?{" "}<Link to="/login" className="text-primary font-bold hover:underline">Sign in</Link></p>
                </form>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Google icon helper
function GoogleIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
    </svg>
  );
}

function googleLogin() { window.location.href = "/api/v1/auth/google/login"; }
