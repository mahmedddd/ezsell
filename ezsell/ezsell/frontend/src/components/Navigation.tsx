import { Link, useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Store, User, LogOut, Plus, Package, MessageCircle, Home, Search, Grid } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useEffect, useState } from "react";
import { messageService } from "@/lib/api";

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const token = localStorage.getItem("authToken");
  const user = localStorage.getItem("user") ? JSON.parse(localStorage.getItem("user")!) : null;
  const [unreadCount, setUnreadCount] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    if (token) {
      loadUnreadCount();
      const interval = setInterval(loadUnreadCount, 10000); // Check every 10 seconds
      return () => clearInterval(interval);
    }
  }, [token]);

  const loadUnreadCount = async () => {
    if (!token) return; // Don't attempt if no token
    try {
      const data = await messageService.getUnreadCount();
      setUnreadCount(data.unread_count || 0);
    } catch (error: any) {
      // Silently fail - user might not be logged in or endpoint unavailable
      if (error.response?.status !== 401 && error.response?.status !== 404) {
        console.error('Failed to load unread count:', error);
      }
      setUnreadCount(0);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("authToken");
    localStorage.removeItem("user");
    navigate("/login");
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/listings?search=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="bg-gradient-to-r from-white via-[#f5f5f0] to-white border-b-2 border-[#143109]/20 sticky top-0 z-50 shadow-md backdrop-blur-sm">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16 gap-4">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2 hover:opacity-80 transition flex-shrink-0">
            <img src="/images/ezsell-logo.png" alt="EZSELL Logo" className="h-10 w-auto" onError={(e) => { e.currentTarget.style.display = 'none'; e.currentTarget.nextElementSibling?.classList.remove('hidden'); }} />
            <div className="hidden flex-col items-center">
              <span className="text-2xl font-bold text-[#143109]">EZ SELL</span>
              <span className="text-xs text-[#5B9BD5] font-medium tracking-wide">BAICH DIAAA !!!</span>
            </div>
          </Link>

          {/* Main Navigation Links */}
          {token && (
            <div className="hidden md:flex items-center space-x-2 flex-shrink-0">
              <Link to="/">
                <Button 
                  variant={isActive("/") ? "default" : "ghost"} 
                  className={`flex items-center gap-2 font-medium ${
                    isActive("/") 
                      ? "bg-[#143109] hover:bg-[#143109]/90 text-white" 
                      : "text-gray-700 hover:text-[#143109] hover:bg-gray-100"
                  }`}
                >
                  <Home className="w-5 h-5" />
                  <span className="text-sm font-semibold">Home</span>
                </Button>
              </Link>
              
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button 
                    variant="ghost" 
                    className="flex items-center gap-2 font-medium text-gray-700 hover:text-[#143109] hover:bg-gray-100"
                  >
                    <Grid className="w-5 h-5" />
                    <span className="text-sm font-semibold">Categories</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="w-48">
                  <DropdownMenuItem onClick={() => navigate("/listings?category=mobiles")}>
                    📱 Mobile Phones
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate("/listings?category=laptops")}>
                    💻 Laptops
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate("/listings?category=furniture")}>
                    🪑 Furniture
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              <Link to="/messages">
                <Button 
                  variant={isActive("/messages") ? "default" : "ghost"} 
                  className={`flex items-center gap-2 font-medium relative ${
                    isActive("/messages") 
                      ? "bg-[#143109] hover:bg-[#143109]/90 text-white" 
                      : "text-gray-700 hover:text-[#143109] hover:bg-gray-100"
                  }`}
                >
                  <MessageCircle className="w-5 h-5" />
                  <span className="text-sm font-semibold">Inbox</span>
                  {unreadCount > 0 && (
                    <Badge className="absolute -top-1 -right-1 bg-red-500 text-white text-xs h-5 w-5 flex items-center justify-center p-0 font-bold">
                      {unreadCount}
                    </Badge>
                  )}
                </Button>
              </Link>
            </div>
          )}

          {/* Search Bar */}
          <form onSubmit={handleSearch} className="flex-1 max-w-md hidden md:block">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                type="text"
                placeholder="Search products..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 w-full"
              />
            </div>
          </form>

          {/* Right Side Actions */}
          <div className="flex items-center space-x-3 flex-shrink-0">
            {token ? (
              <>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="flex items-center gap-2 text-gray-700 hover:text-[#143109] hover:bg-gray-100">
                      <User className="w-5 h-5" />
                      <span className="hidden lg:inline font-semibold">{user?.username || "Account"}</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-48">
                    <DropdownMenuItem onClick={() => navigate("/dashboard")}>
                      <Package className="w-4 h-4 mr-2" />
                      My Listings
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate("/dashboard")}>
                      <User className="w-4 h-4 mr-2" />
                      Profile
                    </DropdownMenuItem>
                    {user?.is_admin && (
                      <>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => navigate("/admin")} className="text-purple-600 font-semibold">
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                          </svg>
                          Admin Dashboard
                        </DropdownMenuItem>
                      </>
                    )}
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                      <LogOut className="w-4 h-4 mr-2" />
                      Logout
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            ) : (
              <>
                <Link to="/login">
                  <Button variant="ghost" className="font-semibold">
                    Login
                  </Button>
                </Link>
                <Link to="/dashboard">
                  <Button className="bg-primary hover:bg-primary/90 flex items-center gap-2 border-2 border-primary">
                    <Plus className="w-5 h-5" />
                    <span className="font-semibold">SELL</span>
                  </Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
