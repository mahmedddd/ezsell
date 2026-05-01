import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/components/ui/use-toast";
import { authService } from '../lib/api.ts';
import { ArrowLeft, Mail, Lock, Eye, EyeOff, Check, Sparkles } from "lucide-react";

const STEPS = ["Enter Email", "Verify Code", "New Password"];

export default function ForgotPassword() {
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authService.requestPasswordReset({ email });
      toast({ title: "Reset code sent! 📬", description: "Check your email" });
      setStep(2);
    } catch (err: any) { toast({ title: "Request Failed", description: err.message, variant: "destructive", duration: 5000 }); }
    finally { setLoading(false); }
  };

  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authService.verifyResetCode({ email, code });
      toast({ title: "Code verified! ✅", description: "Enter your new password" });
      setStep(3);
    } catch (err: any) { toast({ title: "Verification Failed", description: err.message, variant: "destructive", duration: 5000 }); }
    finally { setLoading(false); }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) { toast({ title: "Passwords do not match", variant: "destructive" }); return; }
    if (newPassword.length < 6) { toast({ title: "Password too short (min 6)", variant: "destructive" }); return; }
    setLoading(true);
    try {
      await authService.resetPassword({ email, code, new_password: newPassword });
      toast({ title: "Password reset! 🎉", description: "You can now login with your new password" });
      navigate("/login");
    } catch (err: any) { toast({ title: "Reset Failed", description: err.message, variant: "destructive", duration: 5000 }); }
    finally { setLoading(false); }
  };

  const Spinner = () => <span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[hsl(68,30%,97%)] to-[hsl(50,25%,95%)] p-6">
      <div className="w-full max-w-md animate-scale-in">
        <button onClick={() => navigate("/login")} className="mb-6 flex items-center gap-2 text-sm font-semibold text-muted-foreground hover:text-foreground transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Login
        </button>

        <div className="bg-white rounded-3xl shadow-[var(--shadow-xl)] border border-border/50 overflow-hidden">
          {/* Header */}
          <div className="px-8 pt-8 pb-6">
            <div className="flex justify-center mb-6">
              <img src="/images/logo.jpg" alt="EzSell" className="h-14 w-auto rounded-2xl shadow-lg" onError={e => { e.currentTarget.style.display = "none"; }} />
            </div>

            {/* Step progress */}
            <div className="flex items-center gap-1.5 mb-6">
              {STEPS.map((_, i) => (
                <div key={i} className={`h-1.5 flex-1 rounded-full transition-all duration-500 ${step > i ? "bg-primary" : "bg-muted"}`} />
              ))}
            </div>

            <div className="flex items-center gap-2 mb-0.5">
              <div className="h-8 w-8 rounded-xl bg-primary/10 flex items-center justify-center">
                <Sparkles className="h-4 w-4 text-primary" />
              </div>
              <h1 className="text-2xl font-black text-foreground">Reset Password</h1>
            </div>
            <p className="text-sm text-muted-foreground">
              {step === 1 && "Enter your email to receive a reset code"}
              {step === 2 && `Enter the 6-digit code sent to ${email}`}
              {step === 3 && "Choose your new password"}
            </p>
          </div>

          <div className="px-8 pb-8 space-y-4">
            {/* Step 1 */}
            {step === 1 && (
              <form onSubmit={handleRequestReset} className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="fp-email" className="text-sm font-semibold">Email Address</Label>
                  <div className="relative">
                    <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input id="fp-email" type="email" placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} required
                      className="pl-10 h-12 rounded-xl border-border/60 focus:border-primary/50 focus:ring-2 focus:ring-primary/10 transition-all font-medium" />
                  </div>
                </div>
                <Button type="submit" disabled={loading} className="w-full h-12 rounded-2xl bg-primary hover:bg-primary/90 font-bold text-base shadow-lg shadow-primary/25 hover:-translate-y-0.5 transition-all">
                  {loading ? <span className="flex items-center gap-2"><Spinner />Sending...</span> : "Send Reset Code →"}
                </Button>
              </form>
            )}

            {/* Step 2 */}
            {step === 2 && (
              <form onSubmit={handleVerifyCode} className="space-y-4">
                <div className="bg-primary/5 border border-primary/15 rounded-2xl px-4 py-3 text-sm">
                  <p className="font-semibold text-foreground mb-0.5">Code sent to:</p>
                  <p className="text-primary font-bold">{email}</p>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="fp-code" className="text-sm font-semibold">Reset Code</Label>
                  <Input id="fp-code" type="text" placeholder="Enter 6-digit code" value={code} onChange={e => setCode(e.target.value)} maxLength={6} required
                    className="h-14 rounded-xl border-border/60 text-center text-2xl font-black tracking-widest focus:border-primary/50 focus:ring-2 focus:ring-primary/10 transition-all" />
                </div>
                <Button type="submit" disabled={loading} className="w-full h-12 rounded-2xl bg-primary hover:bg-primary/90 font-bold text-base shadow-lg shadow-primary/25 hover:-translate-y-0.5 transition-all">
                  {loading ? <span className="flex items-center gap-2"><Spinner />Verifying...</span> : "Verify Code ✓"}
                </Button>
                <button type="button" onClick={() => setStep(1)} className="w-full h-10 rounded-2xl text-sm font-semibold text-muted-foreground hover:text-foreground hover:bg-muted transition-all">
                  ← Change email
                </button>
              </form>
            )}

            {/* Step 3 */}
            {step === 3 && (
              <form onSubmit={handleResetPassword} className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="fp-newpw" className="text-sm font-semibold">New Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input id="fp-newpw" type={showPw ? "text" : "password"} placeholder="New password" value={newPassword} onChange={e => setNewPassword(e.target.value)} required minLength={6}
                      className="pl-10 pr-10 h-12 rounded-xl border-border/60 focus:border-primary/50 focus:ring-2 focus:ring-primary/10 transition-all font-medium" />
                    <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                      {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="fp-confirm" className="text-sm font-semibold">Confirm Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input id="fp-confirm" type={showConfirm ? "text" : "password"} placeholder="Confirm new password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required minLength={6}
                      className={`pl-10 pr-10 h-12 rounded-xl border-2 focus:ring-2 focus:ring-primary/10 transition-all font-medium ${confirmPassword && newPassword === confirmPassword ? "border-emerald-400" : confirmPassword ? "border-red-400" : "border-border/60 focus:border-primary/50"}`} />
                    <button type="button" onClick={() => setShowConfirm(!showConfirm)} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                      {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                    {confirmPassword && newPassword === confirmPassword && (
                      <Check className="absolute right-10 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-500 pointer-events-none" />
                    )}
                  </div>
                </div>
                <Button type="submit" disabled={loading} className="w-full h-12 rounded-2xl bg-primary hover:bg-primary/90 font-bold text-base shadow-lg shadow-primary/25 hover:-translate-y-0.5 transition-all">
                  {loading ? <span className="flex items-center gap-2"><Spinner />Resetting...</span> : "Reset Password 🔑"}
                </Button>
              </form>
            )}

            <p className="text-center text-sm text-muted-foreground">
              <Link to="/login" className="text-primary font-bold hover:underline">← Back to Login</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
