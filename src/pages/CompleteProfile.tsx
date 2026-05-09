import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/components/ui/use-toast";
import { Phone, MapPin, Sparkles, ArrowLeft } from "lucide-react";
import { API_BASE_URL } from "../lib/api";

export default function CompleteProfile() {
    const navigate = useNavigate();
    const location = useLocation();
    const { toast } = useToast();
    const prefill = (location.state as any)?.prefill || {};

    const [phone, setPhone] = useState("");
    const [loc, setLoc] = useState("Islamabad");
    const [loading, setLoading] = useState(false);

    const token = localStorage.getItem("authToken");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!phone.trim() || phone.length !== 11) {
            toast({ title: "Valid phone number required", description: "Please enter exactly 11 digits (e.g., 03xxxxxxxxx).", variant: "destructive" });
            return;
        }

        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/v1/me`, {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ phone, location: loc }),
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Failed to update profile");
            }

            const updated = await res.json();
            localStorage.setItem("user", JSON.stringify(updated));

            toast({ title: "Profile complete! 🎉", description: "Welcome to EzSell!" });
            navigate("/dashboard", { replace: true });
        } catch (err: any) {
            toast({ title: "Update failed", description: err.message, variant: "destructive" });
        } finally {
            setLoading(false);
        }
    };

    const handleBackToLogin = async () => {
        if (token) {
            try {
                await fetch(`${API_BASE_URL}/api/v1/me`, {
                    method: "DELETE",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });
            } catch (err) {
                console.error("Failed to delete incomplete profile:", err);
            }
        }
        localStorage.removeItem("authToken");
        localStorage.removeItem("user");
        navigate("/login", { replace: true });
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[hsl(68,30%,97%)] to-[hsl(50,25%,95%)] p-6">
            <div className="w-full max-w-md animate-scale-in">
            <button onClick={handleBackToLogin} className="mb-6 flex items-center gap-2 text-sm font-semibold text-muted-foreground hover:text-primary hover:bg-white/50 px-3 py-1.5 rounded-lg transition-all border border-transparent hover:border-primary/20 w-fit">
                <ArrowLeft className="w-4 h-4" /> Back to Login
            </button>
            <div className="bg-white rounded-3xl shadow-[var(--shadow-xl)] border border-border/50 overflow-hidden">
                    {/* Header */}
                    <div className="hero-mesh px-8 pt-10 pb-8 text-white text-center">
                        <img
                            src="/images/logo.jpg"
                            alt="EzSell"
                            className="h-16 w-auto rounded-2xl shadow-xl mx-auto mb-5 ring-4 ring-white/20 animate-float"
                            onError={e => { e.currentTarget.style.display = "none"; }}
                        />
                        <div className="flex items-center justify-center gap-2 mb-1">
                            <Sparkles className="h-5 w-5 text-yellow-300" />
                            <h1 className="text-2xl font-black">Almost There!</h1>
                        </div>
                        <p className="text-white/70 text-sm">
                            Complete your profile to start buying & selling
                        </p>

                        {/* Prefill badge */}
                        {prefill.full_name && (
                            <div className="mt-4 inline-flex items-center gap-2 bg-white/15 backdrop-blur-sm rounded-xl px-4 py-2 text-sm font-medium">
                                👋 Welcome, {prefill.full_name}!
                            </div>
                        )}
                    </div>

                    {/* Form */}
                    <div className="px-8 py-8 space-y-5">
                        {/* Prefilled read-only fields for context */}
                        {prefill.email && (
                            <div className="bg-emerald-50 border border-emerald-200 rounded-2xl px-4 py-3 flex items-center gap-3">
                                <div className="h-8 w-8 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600 font-bold text-sm">
                                    ✓
                                </div>
                                <div>
                                    <p className="text-xs text-emerald-600 font-semibold">Google Verified Email</p>
                                    <p className="text-sm font-bold text-emerald-900">{prefill.email}</p>
                                </div>
                            </div>
                        )}

                        <form onSubmit={handleSubmit} className="space-y-5">
                            {/* Phone */}
                            <div className="space-y-1.5">
                                <Label htmlFor="phone" className="text-sm font-semibold">
                                    Phone Number <span className="text-red-500">*</span>
                                </Label>
                                <div className="relative">
                                    <Phone className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        id="phone"
                                        type="tel"
                                        placeholder="03xxxxxxxxx"
                                        value={phone}
                                        onChange={e => {
                                            const val = e.target.value.replace(/\D/g, "").slice(0, 11);
                                            setPhone(val);
                                        }}
                                        required
                                        className="pl-10 h-12 rounded-xl border-border/60 focus:border-primary/50 focus:ring-2 focus:ring-primary/10 transition-all font-medium tracking-wider"
                                    />
                                </div>
                                <p className="text-[11px] text-muted-foreground flex items-center gap-1">
                                    <span>💡</span> Enter exactly 11 digits starting with 03
                                </p>
                            </div>

                            {/* Location */}
                            <div className="space-y-1.5">
                                <Label className="text-sm font-semibold flex items-center gap-1">
                                    <MapPin className="h-3.5 w-3.5" /> Your City
                                </Label>
                                <Select value={loc} onValueChange={setLoc}>
                                    <SelectTrigger className="h-12 rounded-xl border-border/60 font-medium focus:ring-2 focus:ring-primary/10">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent className="rounded-xl">
                                        <SelectItem value="Islamabad">Islamabad</SelectItem>
                                        <SelectItem value="Rawalpindi">Rawalpindi</SelectItem>
                                    </SelectContent>
                                </Select>
                                <p className="text-[11px] text-primary font-medium">
                                    🏙️ Currently serving Twin Cities (Islamabad / Rawalpindi)
                                </p>
                            </div>

                            <Button
                                type="submit"
                                disabled={loading}
                                className="w-full h-12 rounded-2xl bg-primary hover:bg-primary/90 font-bold text-base shadow-lg shadow-primary/25 hover:-translate-y-0.5 transition-all"
                            >
                                {loading ? (
                                    <span className="flex items-center gap-2">
                                        <span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                        Saving...
                                    </span>
                                ) : (
                                    "Complete My Profile →"
                                )}
                            </Button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
}
