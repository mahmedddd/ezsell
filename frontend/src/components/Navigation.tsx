import { Link, useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import Avatar, { parseAvatarUrl } from "@/components/ui/avatar";
import {
  Store, User, LogOut, Plus, Package, MessageCircle, Home,
  Search, Grid, Heart, ChevronLeft, ChevronRight, RotateCw,
  Bell, Sparkles, ShoppingBag, Check, EyeOff, Menu, X,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useEffect, useState } from "react";
import { messageService, listingService, analyticsService, notificationService, getImageUrl, authService } from '../lib/api';

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const token = localStorage.getItem("authToken");
  const [user, setUser] = useState<any>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [listings, setListings] = useState<any[]>([]);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [imgError, setImgError] = useState(false);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [unreadNotificationsCount, setUnreadNotificationsCount] = useState(0);

  useEffect(() => {
    const loadUser = () => {
      const userData = localStorage.getItem("user");
      if (userData) {
        try { setUser(JSON.parse(userData)); } catch (e) { /* ignore */ }
      }
    };
    loadUser();
    window.addEventListener("user-updated", loadUser);
    return () => window.removeEventListener("user-updated", loadUser);
  }, [token]);

  useEffect(() => {
    setImgError(false);
  }, [user?.avatar_url]);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    if (token) {
      loadUnreadCount();
      loadMyListings();
      loadNotifications();
      const interval = setInterval(() => {
        loadUnreadCount();
        loadMyListings();
        loadNotifications();
      }, 10000);
      return () => clearInterval(interval);
    }
  }, [token]);

  // Close mobile menu on route change
  useEffect(() => { setMobileMenuOpen(false); }, [location.pathname]);

  const loadMyListings = async () => {
    if (!token) return;
    try { setListings(await listingService.getMyListings()); } catch { /* silent */ }
  };

  const loadUnreadCount = async () => {
    if (!token) return;
    try {
      const data = await messageService.getUnreadCount();
      setUnreadCount(data.unread_count || 0);
    } catch (error: any) {
      if (error.response?.status !== 401 && error.response?.status !== 404) {
        console.error("Failed to load unread count:", error);
      }
      setUnreadCount(0);
    }
  };

  const loadNotifications = async () => {
    if (!token) return;
    try {
      const notes = await notificationService.getNotifications();
      setNotifications(notes);
      const { count } = await notificationService.getUnreadCount();
      setUnreadNotificationsCount(count);
    } catch (error) {
      console.error("Failed to load notifications:", error);
    }
  };

  const handleMarkAsRead = async (id: number) => {
    try {
      await notificationService.markAsRead(id);
      loadNotifications();
    } catch (error) {
      console.error("Error marking notification as read:", error);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await notificationService.markAllAsRead();
      loadNotifications();
    } catch (error) {
      console.error("Error marking all notifications as read:", error);
    }
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
    navigate("/login");
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const q = searchQuery.trim();
    if (q) {
      analyticsService.trackActivity({ activity_type: "search", search_query: q }).catch(() => { });
      navigate(`/listings?search=${encodeURIComponent(q)}`);
      setMobileMenuOpen(false);
    }
  };

  const isActive = (path: string) => location.pathname === path;

  /* ── derived stats ── */
  const liveCount = listings.filter(l => (l.is_active || l.is_active == null) && !l.is_sold && (l.approval_status === "approved" || !l.approval_status)).length;
  const soldCount = listings.filter(l => l.is_sold).length;
  const pendingCount = listings.filter(l => l.approval_status === "pending").length;
  const hiddenCount = listings.filter(l => l.is_active === false && !l.is_sold && (l.approval_status === "approved" || !l.approval_status)).length;

  /* ── shared nav link component ── */
  const NavLink = ({ to, icon: Icon, label, badge }: { to: string; icon: any; label: string; badge?: number }) => (
    <Link to={to}>
      <button
        className={`group relative flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${isActive(to)
          ? "bg-primary text-primary-foreground shadow-md shadow-primary/30"
          : "text-foreground/70 hover:text-foreground hover:bg-foreground/5"
          }`}
      >
        <Icon className="w-4 h-4 flex-shrink-0" />
        <span className="hidden lg:inline">{label}</span>
        {badge && badge > 0 && (
          <span className={`absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-black text-white shadow-sm ring-2 ring-white ${isActive(to) ? "bg-white text-primary" : "bg-red-500"
            }`}>
            {badge}
          </span>
        )}
      </button>
    </Link>
  );

  return (
    <>
      {/* ────────── Desktop / Tablet Nav ────────── */}
      <nav
        className={`sticky top-0 z-50 transition-all duration-300 ${scrolled
          ? "glass shadow-[var(--shadow-nav)] border-b border-white/60"
          : "bg-white/80 backdrop-blur-sm border-b border-border/50"
          }`}
      >
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16 gap-3">

            {/* Left: browser-back + logo */}
            <div className="flex items-center gap-2 flex-shrink-0">
              {/* Browser nav (desktop only) */}
              <div className="hidden sm:flex items-center gap-0.5 mr-1">
                <button
                  onClick={() => navigate(-1)}
                  className="h-8 w-8 flex items-center justify-center rounded-lg text-foreground/50 hover:text-foreground hover:bg-foreground/5 transition-all"
                  title="Go Back"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={() => navigate(1)}
                  className="h-8 w-8 flex items-center justify-center rounded-lg text-foreground/50 hover:text-foreground hover:bg-foreground/5 transition-all"
                  title="Go Forward"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
                <button
                  onClick={() => window.location.reload()}
                  className="h-8 w-8 flex items-center justify-center rounded-lg text-foreground/50 hover:text-foreground hover:bg-foreground/5 transition-all"
                  title="Refresh"
                >
                  <RotateCw className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Logo */}
              <Link to="/" className="flex items-center gap-2 group">
                <div className="relative">
                  <img
                    src="/images/logo.jpg"
                    alt="EzSell"
                    className="h-9 w-auto rounded-xl ring-2 ring-transparent group-hover:ring-primary/30 transition-all duration-200 shadow-sm"
                    onError={(e) => {
                      e.currentTarget.style.display = "none";
                      (e.currentTarget.nextElementSibling as HTMLElement)?.classList.remove("hidden");
                    }}
                  />
                  <div className="hidden items-center justify-center bg-gradient-to-br from-primary to-accent w-9 h-9 rounded-xl shadow-md">
                    <Store className="w-5 h-5 text-white" />
                  </div>
                </div>
                <div className="hidden sm:block">
                  <span className="text-lg font-black text-primary tracking-tight leading-none">EzSell</span>
                  <div className="text-[9px] text-muted-foreground font-medium tracking-widest uppercase leading-none mt-0.5">Marketplace</div>
                </div>
              </Link>
            </div>

            {/* Centre: main nav links (logged in, md+) */}
            {token && (
              <div className="hidden md:flex items-center gap-1">
                <NavLink to="/" icon={Home} label="Home" />

                {/* Categories dropdown */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button className="group flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-semibold text-foreground/70 hover:text-foreground hover:bg-foreground/5 transition-all duration-200">
                      <Grid className="w-4 h-4" />
                      <span className="hidden lg:inline">Categories</span>
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="w-52 rounded-2xl shadow-xl border-0 bg-white/95 backdrop-blur-xl p-1.5">
                    {[
                      { label: "📱 Mobile Phones", val: "mobile" },
                      { label: "💻 Laptops", val: "laptop" },
                      { label: "🛋️ Furniture", val: "furniture" },
                    ].map(({ label, val }) => (
                      <DropdownMenuItem
                        key={val}
                        onClick={() => navigate(`/listings?category=${val}`)}
                        className="rounded-xl font-medium cursor-pointer py-2.5 px-3 focus:bg-primary/8"
                      >
                        {label}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>

                <NavLink to="/messages" icon={MessageCircle} label="Inbox" badge={unreadCount} />
                <NavLink to="/favorites" icon={Heart} label="Saved" />
                <NavLink
                  to={user?.is_admin ? "/admin" : "/dashboard"}
                  icon={Package}
                  label={user?.is_admin ? "Admin" : "My Ads"}
                />
              </div>
            )}

            {/* Centre-right: search (hidden on mobile, shown md+) */}
            <form onSubmit={handleSearch} className="flex-1 max-w-xs hidden md:block">
              <div className="relative group premium-input">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                <Input
                  type="text"
                  placeholder="Search anything..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 h-10 rounded-xl border-border/60 bg-white/70 focus:bg-white text-sm transition-all focus:border-primary/50 focus:ring-2 focus:ring-primary/10"
                />
              </div>
            </form>

            {/* Right actions */}
            <div className="flex items-center gap-2 flex-shrink-0">
              {/* SELL CTA */}
              <Link to="/create-listing">
                <Button
                  className="hidden sm:flex items-center gap-1.5 bg-primary hover:bg-primary/90 text-white font-bold px-4 h-9 rounded-xl shadow-md shadow-primary/25 hover:shadow-lg hover:shadow-primary/30 transition-all duration-200 hover:-translate-y-0.5"
                >
                  <Plus className="w-4 h-4" />
                  <span className="text-sm">Sell</span>
                </Button>
              </Link>

              {token ? (
                <>
                  {/* Notification bell */}
                  <Popover>
                    <PopoverTrigger asChild>
                      <button className="relative h-9 w-9 flex items-center justify-center rounded-xl text-foreground/60 hover:text-foreground hover:bg-foreground/5 transition-all">
                        <Bell className="h-5 w-5" />
                        {(pendingCount > 0 || unreadNotificationsCount > 0) && (
                          <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] font-black text-white ring-2 ring-white shadow-sm">
                            {pendingCount + unreadNotificationsCount}
                          </span>
                        )}
                      </button>
                    </PopoverTrigger>
                    <PopoverContent className="w-80 p-0 rounded-2xl border-0 shadow-2xl overflow-hidden bg-white/97 backdrop-blur-xl" align="end">
                      <div className="hero-mesh p-4 text-white flex justify-between items-center">
                        <div>
                          <h3 className="font-bold text-base flex items-center gap-2">
                            <Sparkles className="h-4 w-4 text-yellow-300" />
                            Notifications & Insights
                          </h3>
                          <p className="text-[11px] text-white/70 mt-0.5">Live snapshot of your marketplace</p>
                        </div>
                        {unreadNotificationsCount > 0 && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleMarkAllAsRead}
                            className="h-7 text-[10px] text-white hover:bg-white/10 px-2 rounded-lg"
                          >
                            Clear All
                          </Button>
                        )}
                      </div>

                      {/* Notifications List */}
                      {notifications.length > 0 && (
                        <div className="max-h-60 overflow-y-auto border-b border-border/40">
                          {notifications.slice(0, 5).map((note) => (
                            <div
                              key={note.id}
                              onClick={() => {
                                if (!note.is_read) handleMarkAsRead(note.id);
                                if (note.link) navigate(note.link);
                              }}
                              className={`p-3 border-b border-border/30 last:border-0 cursor-pointer transition-colors ${note.is_read ? 'opacity-70 bg-transparent' : 'bg-primary/5 hover:bg-primary/10'}`}
                            >
                              <div className="flex justify-between items-start gap-2">
                                <h4 className={`text-xs font-bold ${note.is_read ? 'text-foreground/70' : 'text-primary'}`}>{note.title}</h4>
                                {!note.is_read && <div className="h-1.5 w-1.5 rounded-full bg-primary mt-1" />}
                              </div>
                              <p className="text-[11px] text-muted-foreground line-clamp-2 mt-0.5">{note.message}</p>
                              <p className="text-[9px] text-muted-foreground/60 mt-1 uppercase font-semibold">
                                {new Date(note.created_at).toLocaleDateString()}
                              </p>
                            </div>
                          ))}
                        </div>
                      )}

                      <div className="p-4 grid grid-cols-2 gap-2.5 bg-muted/20">
                        {[
                          { label: "Live & Active", sub: "Visible to buyers", count: liveCount, icon: Check, color: "green" },
                          { label: "Items Sold", sub: "Completed deals", count: soldCount, icon: ShoppingBag, color: "blue" },
                          { label: "Pending", sub: "Awaiting review", count: pendingCount, icon: RotateCw, color: "amber" },
                          { label: "Hidden", sub: "Off-market", count: hiddenCount, icon: EyeOff, color: "slate" },
                        ].map(({ label, sub, count, icon: Icon, color }) => (
                          <div key={label} className={`flex flex-col p-3 rounded-xl border bg-${color}-50 border-${color}-100`}>
                            <Icon className={`h-4 w-4 text-${color}-600 mb-2`} />
                            <span className={`text-2xl font-black text-${color}-700`}>{count}</span>
                            <span className={`text-xs font-semibold text-${color}-800 leading-tight`}>{label}</span>
                            <span className={`text-[10px] text-${color}-600/80`}>{sub}</span>
                          </div>
                        ))}
                      </div>
                      <div className="px-4 pb-3 text-center text-[10px] text-muted-foreground italic">
                        Keep ads fresh for maximum reach!
                      </div>
                    </PopoverContent>
                  </Popover>

                  {/* User menu */}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <div className="flex items-center gap-2.5 px-2 py-1.5 rounded-2xl hover:bg-foreground/5 transition-all outline-none">
                        {user?.avatar_url && !imgError && (user.avatar_url.startsWith('http') || user.avatar_url.startsWith('/uploads')) ? (
                          <img
                            src={getImageUrl(user.avatar_url)}
                            alt="Profile"
                            className="h-7 w-7 rounded-lg object-cover shadow-sm"
                            onError={() => setImgError(true)}
                          />
                        ) : (
                          <Avatar seed={user?.username || "U"} {...parseAvatarUrl(user?.avatar_url, user?.username)} size={28} className="shadow-sm" />
                        )}
                        <span className="hidden lg:inline max-w-[80px] truncate">{user?.username || "Account"}</span>
                      </div>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-52 rounded-2xl shadow-xl border-0 bg-white/97 backdrop-blur-xl p-1.5">
                      {/* User header */}
                      <div className="px-3 py-2 mb-1 border-b border-border/40">
                        <p className="font-bold text-sm text-foreground">{user?.full_name || user?.username}</p>
                        <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                      </div>
                      <DropdownMenuItem onClick={() => navigate("/dashboard")} className="rounded-xl cursor-pointer py-2.5 px-3">
                        <Package className="w-4 h-4 mr-2.5 text-muted-foreground" /> My Listings
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => navigate("/favorites")} className="rounded-xl cursor-pointer py-2.5 px-3">
                        <Heart className="w-4 h-4 mr-2.5 text-muted-foreground" /> Saved
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => navigate("/profile")} className="rounded-xl cursor-pointer py-2.5 px-3">
                        <User className="w-4 h-4 mr-2.5 text-muted-foreground" /> Profile & Support
                      </DropdownMenuItem>
                      {user?.is_admin && (
                        <>
                          <DropdownMenuSeparator className="my-1" />
                          <DropdownMenuItem onClick={() => navigate("/admin")} className="rounded-xl cursor-pointer py-2.5 px-3 text-purple-600 font-semibold">
                            <Sparkles className="w-4 h-4 mr-2.5" /> Admin Console
                          </DropdownMenuItem>
                        </>
                      )}
                      <DropdownMenuSeparator className="my-1" />
                      <DropdownMenuItem onClick={handleLogout} className="rounded-xl cursor-pointer py-2.5 px-3 text-red-600 focus:text-red-600 focus:bg-red-50">
                        <LogOut className="w-4 h-4 mr-2.5" /> Logout
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </>
              ) : (
                <div className="flex items-center gap-2">
                  <Link to="/login">
                    <Button variant="ghost" className="h-9 px-3 rounded-xl text-sm font-semibold hover:bg-foreground/5">
                      Login
                    </Button>
                  </Link>
                  <Link to="/signup">
                    <Button className="h-9 px-4 rounded-xl text-sm font-bold bg-primary hover:bg-primary/90 shadow-md shadow-primary/25 hover:shadow-lg hover:shadow-primary/30 hover:-translate-y-0.5 transition-all">
                      Sign Up
                    </Button>
                  </Link>
                </div>
              )}

              {/* Mobile hamburger */}
              <button
                className="md:hidden h-9 w-9 flex items-center justify-center rounded-xl text-foreground/60 hover:text-foreground hover:bg-foreground/5 transition-all"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile: search + dropdown menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-border/40 bg-white/97 backdrop-blur-xl animate-fade-in-down">
            <div className="container mx-auto px-4 py-3 space-y-3">
              {/* Mobile search */}
              <form onSubmit={handleSearch} className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="Search products..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 h-11 rounded-xl bg-muted/50 border-0 text-sm"
                />
              </form>

              {/* Mobile nav links */}
              {token && (
                <nav className="grid grid-cols-3 gap-2">
                  {[
                    { to: "/", icon: Home, label: "Home" },
                    { to: "/messages", icon: MessageCircle, label: "Inbox", badge: unreadCount },
                    { to: "/favorites", icon: Heart, label: "Saved" },
                    { to: user?.is_admin ? "/admin" : "/dashboard", icon: Package, label: user?.is_admin ? "Admin" : "My Ads" },
                    { to: "/profile", icon: User, label: "Profile" },
                  ].map(({ to, icon: Icon, label, badge }) => (
                    <Link key={to} to={to} onClick={() => setMobileMenuOpen(false)}>
                      <div className={`relative flex flex-col items-center gap-1 py-2.5 px-2 rounded-xl text-xs font-semibold transition-all ${isActive(to) ? "bg-primary text-white shadow-md" : "bg-muted/60 text-foreground/70 hover:bg-muted"
                        }`}>
                        <Icon className="w-5 h-5" />
                        {label}
                        {badge && badge > 0 && (
                          <span className="absolute -top-1 -right-1 h-4 w-4 flex items-center justify-center rounded-full bg-red-500 text-[9px] text-white font-black ring-2 ring-white">{badge}</span>
                        )}
                      </div>
                    </Link>
                  ))}
                  <Link to="/create-listing" onClick={() => setMobileMenuOpen(false)}>
                    <div className="flex flex-col items-center gap-1 py-2.5 px-2 rounded-xl text-xs font-bold bg-primary text-white shadow-md shadow-primary/30">
                      <Plus className="w-5 h-5" />
                      Sell Now
                    </div>
                  </Link>
                </nav>
              )}

              {/* Not logged in: CTA */}
              {!token && (
                <div className="flex gap-2">
                  <Link to="/login" className="flex-1" onClick={() => setMobileMenuOpen(false)}>
                    <Button className="w-full h-11 rounded-xl" variant="outline">Login</Button>
                  </Link>
                  <Link to="/signup" className="flex-1" onClick={() => setMobileMenuOpen(false)}>
                    <Button className="w-full h-11 rounded-xl bg-primary text-white shadow-md">Sign Up</Button>
                  </Link>
                </div>
              )}

              {token && (
                <div className="pt-1 border-t border-border/30 flex justify-between items-center">
                  <span className="text-xs text-muted-foreground">Logged in as <span className="font-semibold text-foreground">{user?.username}</span></span>
                  <button onClick={handleLogout} className="text-xs text-red-600 font-semibold flex items-center gap-1 hover:text-red-700">
                    <LogOut className="w-3.5 h-3.5" /> Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </nav>

      {/* ────────── Mobile Bottom Nav Bar ────────── */}
      {token && (
        <div className="mobile-nav fixed bottom-0 left-0 right-0 z-50 md:hidden safe-bottom">
          <div className="flex items-center justify-around h-16 px-2">
            {[
              { to: "/", icon: Home, label: "Home" },
              { to: "/listings", icon: Search, label: "Browse" },
              { to: "/messages", icon: MessageCircle, label: "Inbox", badge: unreadCount },
              { to: "/favorites", icon: Heart, label: "Saved" },
              { to: user?.is_admin ? "/admin" : "/dashboard", icon: Package, label: "My Ads" },
            ].map(({ to, icon: Icon, label, badge }) => {
              const active = location.pathname === to || (to !== "/" && location.pathname.startsWith(to));
              return (
                <Link key={to} to={to} className="flex-1">
                  <div className={`flex flex-col items-center gap-0.5 py-1 mx-auto w-fit transition-all duration-200 ${active ? "text-primary" : "text-foreground/45 hover:text-foreground/70"}`}>
                    <div className={`relative flex items-center justify-center w-8 h-8 rounded-xl transition-all duration-200 ${active ? "bg-primary/10 scale-110" : ""}`}>
                      <Icon className={`h-5 w-5 transition-all ${active ? "stroke-[2.5]" : "stroke-[1.8]"}`} />
                      {badge && badge > 0 && (
                        <span className="absolute -top-1 -right-1 h-4 w-4 flex items-center justify-center rounded-full bg-red-500 text-[9px] text-white font-black ring-1 ring-white">{badge}</span>
                      )}
                    </div>
                    <span className={`text-[10px] font-semibold leading-none ${active ? "text-primary" : ""}`}>{label}</span>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </>
  );
};

export default Navigation;
