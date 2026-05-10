import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import ForgotPassword from "./pages/ForgotPassword";
import Listings from "./pages/Listings";
import ProductDetail from "./pages/ProductDetail";
import Dashboard from "./pages/Dashboard";
import AdminDashboard from "./pages/AdminDashboard";
import GoogleCallback from "./pages/GoogleCallback";
import Messages from "./pages/Messages";
import CreateListing from "./pages/CreateListing";
import EditListing from "./pages/EditListing";
import Favorites from "./pages/Favorites";
import Profile from "./pages/Profile";
import NotFound from "./pages/NotFound";
import CompleteProfile from "./pages/CompleteProfile";

import Navigation from "./components/Navigation";
import EzSellChatbot from "./components/EzSellChatbot";
import { useLocation } from "react-router-dom";

const queryClient = new QueryClient();

const HIDE_ON = ["/login", "/signup", "/forgot-password", "/complete-profile"];

const NavigationLayout = ({ children }: { children: React.ReactNode }) => {
  const location = useLocation();
  const shouldHide = HIDE_ON.includes(location.pathname);

  return (
    <>
      {!shouldHide && <Navigation />}
      {children}
      {/* EzSell AI Assistant — persistent on all non-auth pages */}
      {!shouldHide && <EzSellChatbot />}
    </>
  );
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <NavigationLayout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/listings" element={<Listings />} />
            <Route path="/product/:id" element={<ProductDetail />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/create-listing" element={<CreateListing />} />
            <Route path="/edit-listing/:id" element={<EditListing />} />
            <Route path="/messages" element={<Messages />} />
            <Route path="/favorites" element={<Favorites />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/profile/:id" element={<Profile />} />
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/auth/google/callback" element={<GoogleCallback />} />
            <Route path="/complete-profile" element={<CompleteProfile />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </NavigationLayout>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
