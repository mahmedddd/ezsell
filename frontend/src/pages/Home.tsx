import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Search, MapPin, Plus, Heart, ChevronRight, Loader2, TrendingUp, Shield, Zap } from "lucide-react";
import { listingService, getImageUrl, favoritesService, recommendationService, analyticsService } from "../lib/api.ts";
import { listingMatchesSearch } from "../lib/nlp";
import { useToast } from "@/components/ui/use-toast";

const CATEGORIES = [
  { id: "all", name: "All", icon: "📦" },
  { id: "mobiles", name: "Mobiles", icon: "📱" },
  { id: "laptops", name: "Laptops", icon: "💻" },
  { id: "furniture", name: "Furniture", icon: "🛋️" },
];

const CITIES = [
  { label: "🇵🇰 All Pakistan", value: "Pakistan" },
  { label: "Islamabad", value: "Islamabad" },
  { label: "Rawalpindi", value: "Rawalpindi" },
];

const ISB_AREAS = ["Bahria Town", "Blue Area", "DHA Phase 1", "DHA Phase 2", "F-6", "F-7", "F-8", "F-10", "F-11", "G-6", "G-7", "G-8", "G-9", "G-10", "G-11", "G-13", "G-14", "G-15", "I-8", "I-9", "I-10", "I-11", "I-14", "PWD Housing Scheme", "Sector B-17", "Sector C-18", "Sector D-12", "Sector E-11", "Zaraj Housing Society"].sort();
const RWP_AREAS = ["Adyala Road", "Airport Housing Society", "Bahria Town Phase 1", "Bahria Town Phase 2", "Bahria Town Phase 3", "Bahria Town Phase 4", "Bahria Town Phase 5", "Bahria Town Phase 6", "Bahria Town Phase 7", "Bahria Town Phase 8", "Chaklala Scheme 3", "DHA Phase 1", "DHA Phase 2", "Gulraiz Housing Scheme", "Gulshan-e-Abad", "National Police Foundation", "Rehmanabad", "Saddar", "Satellite Town", "Soan Garden", "Tench Bhatta", "Westridge"].sort();

const getConditionLabel = (condition: string | number) => {
  const c = typeof condition === "string" ? parseInt(condition) : condition;
  if (c >= 10) return "Brand New";
  if (c >= 9) return "Like New";
  if (c >= 7) return "Excellent";
  if (c >= 5) return "Good";
  if (c >= 3) return "Fair";
  return "Poor";
};

const getConditionColor = (c: number) => {
  if (c >= 9) return "bg-emerald-500";
  if (c >= 7) return "bg-green-500";
  if (c >= 5) return "bg-amber-500";
  return "bg-red-500";
};

export default function Home() {
  const [listings, setListings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [city, setCity] = useState("");
  const [area, setArea] = useState("");
  const [favoriteIds, setFavoriteIds] = useState<Set<number>>(new Set());
  const [togglingFavorite, setTogglingFavorite] = useState<number | null>(null);
  const navigate = useNavigate();
  const { toast } = useToast();
  const currentUser = JSON.parse(localStorage.getItem("user") || "{}");

  useEffect(() => { loadListings(); if (currentUser?.id) loadFavorites(); }, [selectedCategory, city, area]);

  useEffect(() => {
    const onFocus = () => { loadListings(); if (currentUser?.id) loadFavorites(); };
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [selectedCategory, city, area]);

  const loadListings = async () => {
    try {
      setLoading(true);
      let results = [];
      if (searchQuery || selectedCategory !== "all" || city || area) {
        const params = selectedCategory !== "all" ? { category: selectedCategory } : {};
        const data = await listingService.getListings(params);
        results = Array.isArray(data) ? data : [];
      } else {
        const data = await recommendationService.getForYou({ limit: 40 }); // Fetch more for better experience
        results = data.items.map((item: any) => ({ ...item, id: item.listing_id }));
      }

      // Deduplicate locally as a final safety measure
      const seen = new Set();
      const unique = results.filter(item => {
        if (seen.has(item.id)) return false;
        seen.add(item.id);
        return true;
      });

      setListings(unique);
    } catch (error: any) {
      setListings([]);
      toast({ title: "Error loading listings", description: error.response?.data?.detail || "Failed to load listings", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const loadFavorites = async () => {
    try {
      const favs = await favoritesService.getFavorites();
      setFavoriteIds(new Set(favs.map((f: any) => f.id)));
    } catch { /* silent */ }
  };

  const getListingImage = (listing: any): string | null => {
    if (listing?.images) {
      try {
        const imgs = typeof listing.images === "string" ? JSON.parse(listing.images) : listing.images;
        if (Array.isArray(imgs) && imgs.length > 0) return imgs[0];
      } catch { /* ignore */ }
    }
    return listing?.image_url || null;
  };

  const toggleFavorite = async (listingId: number, e: React.MouseEvent) => {
    e.preventDefault(); e.stopPropagation();
    if (!currentUser?.id) {
      toast({ title: "Login Required", description: "Please login to save listings", variant: "destructive" });
      navigate("/login");
      return;
    }
    setTogglingFavorite(listingId);
    try {
      if (favoriteIds.has(listingId)) {
        await favoritesService.removeFavorite(listingId);
        setFavoriteIds(prev => { const s = new Set(prev); s.delete(listingId); return s; });
        toast({ title: "Removed", description: "Removed from your saved listings" });
      } else {
        await favoritesService.addFavorite(listingId);
        setFavoriteIds(prev => new Set([...prev, listingId]));
        const listing = listings.find(l => l.id === listingId);
        if (listing) analyticsService.trackActivity({ activity_type: "favorite", listing_id: listingId, category: listing.category }).catch(() => { });
        toast({ title: "Saved!", description: "Added to your saved listings" });
      }
    } catch { toast({ title: "Error", description: "Failed to update favorites", variant: "destructive" }); }
    finally { setTogglingFavorite(null); }
  };

  const handleSearch = () => {
    const q = searchQuery.trim();
    if (q) {
      analyticsService.trackActivity({ activity_type: "search", search_query: q, category: selectedCategory === "all" ? undefined : selectedCategory }).catch(() => { });
      navigate(`/listings?search=${encodeURIComponent(searchQuery)}`);
    }
  };

  const filteredListings = listings.filter(listing => {
    if (searchQuery.trim() && !listingMatchesSearch(listing, searchQuery)) return false;
    if (city && city !== "Pakistan") {
      const loc = listing.location || "";
      if (!loc.includes(city)) return false;
      if (area?.trim() && !loc.includes(area)) return false;
    }
    return true;
  });

  return (
    <div className="min-h-screen page-content">

      {/* ── Hero Section ── */}
      <section className="relative overflow-hidden">
        <div className="hero-mesh min-h-[340px] md:min-h-[420px] flex items-center">
          {/* Decorative circles */}
          <div className="absolute top-8 right-8 w-64 h-64 rounded-full bg-white/5 blur-3xl pointer-events-none" />
          <div className="absolute -bottom-12 -left-12 w-80 h-80 rounded-full bg-black/10 blur-3xl pointer-events-none" />

          <div className="container mx-auto px-4 py-14 md:py-20 relative z-10">
            <div className="text-center max-w-3xl mx-auto">
              {/* Logo */}
              <div className="flex justify-center mb-6">
                <div className="relative animate-fade-in-up">
                  <img
                    src="/images/logo.jpg"
                    alt="EzSell"
                    className="h-20 md:h-28 w-auto rounded-2xl shadow-2xl ring-4 ring-white/20"
                    onError={(e) => { e.currentTarget.style.display = "none"; }}
                  />
                </div>
              </div>

              <h1 className="animate-fade-in-up delay-100 text-4xl md:text-6xl font-black text-white leading-[1.1] mb-4 tracking-tight drop-shadow-md">
                Buy &amp; Sell{" "}
                <span className="gradient-text-hero">With Confidence</span>
              </h1>
              <p className="animate-fade-in-up delay-200 text-white/70 text-base md:text-xl mb-8 max-w-xl mx-auto">
                Pakistan's smartest marketplace for mobiles, laptops, furniture &amp; more
              </p>

              {/* Search bar */}
              <div className="animate-fade-in-up delay-300 max-w-2xl mx-auto">
                <div className="flex gap-2 bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl p-2 border border-white/60">
                  <div className="flex-1 relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                    <Input
                      type="text"
                      placeholder="What are you looking for today?"
                      value={searchQuery}
                      onChange={e => setSearchQuery(e.target.value)}
                      onKeyDown={e => e.key === "Enter" && handleSearch()}
                      className="pl-11 h-12 text-base border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 font-medium"
                    />
                  </div>
                  <Button
                    onClick={handleSearch}
                    className="px-6 h-12 rounded-xl text-base font-bold bg-primary hover:bg-primary/90 shadow-lg shadow-primary/30 hover:shadow-primary/40 hover:-translate-y-0.5 transition-all"
                  >
                    <Search className="h-5 w-5 mr-2" />
                    Search
                  </Button>
                </div>
              </div>

              {/* Stats row */}
              <div className="animate-fade-in-up delay-400 flex items-center justify-center gap-6 mt-8">
                {[
                  { icon: TrendingUp, label: `${listings.length} Active Listings` },
                  { icon: Shield, label: "Verified Sellers" },
                  { icon: Zap, label: "Instant Messaging" },
                ].map(({ icon: Icon, label }) => (
                  <div key={label} className="flex items-center gap-1.5 text-white/80 text-sm font-medium">
                    <Icon className="w-4 h-4 text-white/60" />
                    {label}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Category Pills ── */}
      <section className="bg-white/80 backdrop-blur-md border-b border-border/50 shadow-sm sticky top-16 z-40">
        <div className="container mx-auto px-4">
          <div className="flex items-center gap-2 overflow-x-auto py-3 scrollbar-hide -mx-1 px-1">
            {CATEGORIES.map((cat, i) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                style={{ animationDelay: `${i * 60}ms` }}
                className={`animate-fade-in-up flex-shrink-0 flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold border transition-all duration-200 ${selectedCategory === cat.id
                  ? "bg-primary text-white border-primary shadow-md shadow-primary/25 scale-105"
                  : "bg-white border-border text-foreground/70 hover:border-primary/40 hover:text-primary hover:bg-primary/5"
                  }`}
              >
                <span className="text-base">{cat.icon}</span>
                {cat.name}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ── Location Filter ── */}
      <section className="bg-white/60 backdrop-blur-sm border-b border-border/30 py-3 px-4">
        <div className="container mx-auto">
          <div className="flex flex-wrap gap-2 items-center">
            <div className="flex items-center gap-1.5 text-sm font-semibold text-foreground/70">
              <MapPin className="h-4 w-4 text-primary" />
              Location:
            </div>
            <div className="flex gap-2 flex-wrap">
              {CITIES.map(({ label, value }) => (
                <button
                  key={value}
                  onClick={() => { setCity(value); setArea(""); }}
                  className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${(!city && value === "Pakistan") || city === value
                    ? "bg-primary text-white border-primary shadow-sm"
                    : "bg-white border-border text-foreground/60 hover:border-primary/40 hover:text-primary"
                    }`}
                >
                  {label}
                </button>
              ))}
              {city && city !== "Pakistan" && (
                <select
                  value={area}
                  onChange={e => setArea(e.target.value)}
                  className="px-3 py-1.5 rounded-full text-xs font-semibold border border-border bg-white text-foreground/70 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary/50 transition-all"
                >
                  <option value="">All {city}</option>
                  {(city === "Islamabad" ? ISB_AREAS : RWP_AREAS).map(a => <option key={a} value={a}>{a}</option>)}
                </select>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ── Listings Grid ── */}
      <section className="py-8 px-4">
        <div className="container mx-auto">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-2xl md:text-3xl font-black text-foreground">
                {searchQuery ? `Results for "${searchQuery}"` : "Fresh Recommendations"}
              </h2>
              <p className="text-sm text-muted-foreground mt-0.5">
                {loading ? "Finding the best deals..." : `${filteredListings.length} listings found`}
              </p>
            </div>
            <Link to="/listings">
              <Button variant="outline" className="hidden sm:flex items-center gap-1.5 rounded-xl font-semibold hover:bg-primary hover:text-white hover:border-primary transition-all">
                View All <ChevronRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>

          {/* Loading skeleton */}
          {loading && (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {[...Array(10)].map((_, i) => (
                <div key={i} className="rounded-2xl overflow-hidden bg-white shadow-sm border border-border/50 animate-pulse">
                  <div className="aspect-square bg-muted shimmer" />
                  <div className="p-3 space-y-2">
                    <div className="h-3.5 bg-muted rounded-full shimmer w-4/5" />
                    <div className="h-4 bg-muted rounded-full shimmer w-3/5" />
                    <div className="h-3 bg-muted rounded-full shimmer w-2/5" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Empty state */}
          {!loading && filteredListings.length === 0 && (
            <div className="text-center py-20">
              <div className="text-6xl mb-4">🔍</div>
              <h3 className="text-xl font-bold text-foreground mb-2">No listings found</h3>
              <p className="text-muted-foreground mb-6">Try a different search or browse all categories</p>
              <Link to="/create-listing">
                <Button className="rounded-xl bg-primary hover:bg-primary/90 shadow-md shadow-primary/25">
                  <Plus className="h-4 w-4 mr-2" /> Post Your Ad
                </Button>
              </Link>
            </div>
          )}

          {/* Listings grid */}
          {!loading && filteredListings.length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {filteredListings.slice(0, 20).map((listing, i) => {
                const imgRaw = getListingImage(listing);
                const imgUrl = imgRaw ? getImageUrl(imgRaw) : null;
                const isFav = favoriteIds.has(listing.id);
                const cond = typeof listing.condition === "string" ? parseInt(listing.condition) : listing.condition;
                const condOk = !isNaN(cond);

                return (
                  <Link
                    key={listing.id}
                    to={`/product/${listing.id}`}
                    className="group"
                    style={{ animationDelay: `${Math.min(i * 40, 400)}ms` }}
                  >
                    <div className="relative bg-white rounded-2xl overflow-hidden border border-border/50 shadow-[var(--shadow-xs)] hover:shadow-[var(--shadow-lg)] hover:-translate-y-1 hover:border-primary/20 transition-all duration-300 ease-out h-full flex flex-col">
                      {/* Image */}
                      <div className="relative aspect-square overflow-hidden bg-muted flex-shrink-0">
                        {imgUrl ? (
                          <img
                            src={imgUrl}
                            alt={listing.title}
                            loading="lazy"
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 ease-out"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-4xl bg-gradient-to-br from-muted to-muted/50">📦</div>
                        )}

                        {/* Overlay gradient */}
                        <div className="absolute inset-0 bg-gradient-to-t from-black/30 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                        {/* Badges top-left */}
                        <div className="absolute top-2 left-2 flex flex-col gap-1">
                          {listing.is_featured && (
                            <span className="badge-pill bg-yellow-400 text-yellow-900 shadow-sm">⭐ Featured</span>
                          )}
                          {listing.location && (
                            <span className="badge-pill bg-white/90 text-foreground shadow-sm backdrop-blur-sm text-[10px]">
                              📍 {listing.location.split(",")[0]}
                            </span>
                          )}
                        </div>

                        {/* Condition badge */}
                        {condOk && (
                          <div className={`absolute bottom-2 left-2 flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold text-white shadow-sm ${getConditionColor(cond)}`}>
                            {cond}/10 · {getConditionLabel(cond)}
                          </div>
                        )}

                        {/* Favourite button */}
                        <button
                          className={`absolute top-2 right-2 h-8 w-8 flex items-center justify-center rounded-full shadow-md border border-white/60 backdrop-blur-sm transition-all duration-200 z-10 ${isFav ? "bg-red-50 scale-110" : "bg-white/90 opacity-0 group-hover:opacity-100 hover:scale-110"
                            }`}
                          onClick={e => toggleFavorite(listing.id, e)}
                          disabled={togglingFavorite === listing.id}
                        >
                          {togglingFavorite === listing.id ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin text-gray-500" />
                          ) : (
                            <Heart className={`h-3.5 w-3.5 transition-colors ${isFav ? "text-red-500 fill-red-500" : "text-foreground/60 hover:text-red-500"}`} />
                          )}
                        </button>
                      </div>

                      {/* Info */}
                      <div className="p-3 flex flex-col gap-1 flex-1">
                        <h3 className="text-sm font-semibold text-foreground line-clamp-2 leading-snug group-hover:text-primary transition-colors">
                          {listing.title}
                        </h3>
                        <p className="text-base font-black text-primary mt-0.5">
                          PKR {listing.price?.toLocaleString()}
                        </p>
                        <div className="flex items-center justify-between mt-auto pt-1 border-t border-border/30">
                          <span className="text-[10px] text-muted-foreground/60 ml-auto">
                            {new Date(listing.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                          </span>
                        </div>
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          )}

          {/* View all CTA */}
          {!loading && filteredListings.length > 0 && (
            <div className="text-center mt-10">
              <Link to="/listings">
                <Button variant="outline" className="rounded-xl px-8 h-11 font-bold border-2 hover:bg-primary hover:text-white hover:border-primary transition-all">
                  View All Listings <ChevronRight className="ml-1.5 h-4 w-4" />
                </Button>
              </Link>
            </div>
          )}
        </div>
      </section>

      {/* ── Floating Sell Button (mobile) ── */}
      <Link to="/create-listing" className="md:hidden">
        <div className="fixed bottom-20 right-4 z-40 h-14 w-14 flex items-center justify-center rounded-full bg-primary text-white shadow-xl shadow-primary/40 hover:scale-110 active:scale-95 transition-all duration-200 ring-4 ring-white">
          <Plus className="h-6 w-6 stroke-[2.5]" />
        </div>
      </Link>
    </div>
  );
}
