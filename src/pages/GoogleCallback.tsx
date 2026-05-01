import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useToast } from "@/components/ui/use-toast";
import { Loader2 } from "lucide-react";

export default function GoogleCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();

  useEffect(() => {
    const token = searchParams.get("token");
    const error = searchParams.get("error");
    const isNew = searchParams.get("is_new") === "1";
    const name = searchParams.get("name") || "";

    if (error) {
      toast({
        title: "Google sign-in failed",
        description: decodeURIComponent(error.replace(/\+/g, " ")),
        variant: "destructive",
      });
      navigate("/login");
      return;
    }

    if (!token) {
      toast({
        title: "Authentication Error",
        description: "No token received from Google. Please try again.",
        variant: "destructive",
      });
      navigate("/login");
      return;
    }

    // Store token immediately
    localStorage.setItem("authToken", token);

    // Fetch full user info
    fetch("/api/v1/me", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(res => {
        if (!res.ok) throw new Error("Failed to fetch user");
        return res.json();
      })
      .then(user => {
        localStorage.setItem("user", JSON.stringify(user));

        // New Google user with no phone/location → send to complete profile
        const needsProfile = isNew || !user.phone || !user.location;

        if (needsProfile) {
          toast({
            title: "Welcome to EzSell! 🎉",
            description: "Just one more step — complete your profile to get started.",
          });
          // Pass the token + prefilled name via state so the completion page can use them
          navigate("/complete-profile", {
            state: { prefill: { full_name: user.full_name || name, email: user.email, username: user.username } },
            replace: true,
          });
        } else {
          toast({
            title: `Welcome back, ${user.username}! 👋`,
            description: "You've been signed in with Google.",
          });
          navigate("/dashboard", { replace: true });
        }
      })
      .catch(() => {
        toast({
          title: "Error",
          description: "Failed to load your account. Please try again.",
          variant: "destructive",
        });
        localStorage.removeItem("authToken");
        navigate("/login");
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-[hsl(68,30%,97%)] to-[hsl(50,25%,95%)]">
      <div className="bg-white rounded-3xl shadow-[var(--shadow-xl)] border border-border/50 p-12 text-center max-w-sm w-full mx-4">
        {/* Logo */}
        <img
          src="/images/logo.jpg"
          alt="EzSell"
          className="h-16 w-auto rounded-2xl shadow-md mx-auto mb-6"
          onError={e => { e.currentTarget.style.display = "none"; }}
        />
        {/* Spinner */}
        <div className="flex items-center justify-center mb-4">
          <Loader2 className="h-10 w-10 text-primary animate-spin" />
        </div>
        <h2 className="text-xl font-black text-foreground mb-1">Signing you in…</h2>
        <p className="text-sm text-muted-foreground">Completing Google authentication</p>
      </div>
    </div>
  );
}
