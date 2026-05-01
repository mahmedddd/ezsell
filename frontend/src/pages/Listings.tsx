import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { listingService, getImageUrl, favoritesService, analyticsService } from "../lib/api.ts";
import { Search, Filter, X, Heart, Loader2, Tag, SlidersHorizontal, ChevronDown, ChevronUp } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { formatCurrency } from "../lib/utils";

const conditions = ["new", "like-new", "good", "fair"];
const brands = ["Apple", "Samsung", "Huawei", "Oppo", "Vivo", "Xiaomi", "Realme", "OnePlus", "Google", "HP", "Dell", "Lenovo", "Asus", "Acer", "MSI"];
const ISB = ["Bahria Town", "Blue Area", "DHA Phase 1", "DHA Phase 2", "F-6", "F-7", "F-8", "F-10", "F-11", "G-6", "G-7", "G-8", "G-9", "G-10", "G-11", "G-13", "G-14", "G-15", "I-8", "I-9", "I-10", "I-11", "I-14", "PWD Housing Scheme", "Sector B-17", "Sector C-18", "Sector D-12", "Sector E-11", "Zaraj Housing Society"].sort();
const RWP = ["Adyala Road", "Airport Housing Society", "Bahria Town Phase 1", "Bahria Town Phase 2", "Bahria Town Phase 3", "Bahria Town Phase 4", "Bahria Town Phase 5", "Bahria Town Phase 6", "Bahria Town Phase 7", "Bahria Town Phase 8", "Chaklala Scheme 3", "DHA Phase 1", "DHA Phase 2", "Gulraiz Housing Scheme", "Gulshan-e-Abad", "National Police Foundation", "Rehmanabad", "Saddar", "Satellite Town", "Soan Garden", "Tench Bhatta", "Westridge"].sort();

const getConditionLabel = (c: number) => {
  if (c >= 9) return "Mint";
  if (c >= 7) return "Excellent";
  if (c >= 5) return "Good";
  if (c >= 3) return "Fair";
  return "Poor";
};
const condClass = (c: number) =>
  c >= 9 ? "bg-emerald-100 text-emerald-800 border-emerald-300"
    : c >= 7 ? "bg-green-100 text-green-800 border-green-300"
      : c >= 5 ? "bg-amber-100 text-amber-800 border-amber-300"
        : "bg-red-100 text-red-800 border-red-300";

export default function Listings() {
  const [listings, setListings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [selectedConditions, setSelectedConditions] = useState<string[]>([]);
  const [priceRange, setPriceRange] = useState<[number, number]>([0, 500000]);
  const [selectedBrands, setSelectedBrands] = useState<string[]>([]);
  const [city, setCity] = useState("");
  const [area, setArea] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [favoriteIds, setFavoriteIds] = useState<Set<number>>(new Set());
  const [togglingFavorite, setTogglingFavorite] = useState<number | null>(null);
  const [lastSearch, setLastSearch] = useState("");
  const [filterExpanded, setFilterExpanded] = useState({ cat: true, loc: true, cond: false, price: false, brand: false });
  const { toast } = useToast();
  const currentUser = JSON.parse(localStorage.getItem("user") || "{}");
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const urlSearch = searchParams.get("search");
    const urlCategory = searchParams.get("category");
    if (urlSearch) { setSearch(urlSearch); setLastSearch(urlSearch); }
    if (urlCategory) { setCategory(urlCategory); }
    fetchListings(urlSearch || undefined);
    if (currentUser?.id) fetchFavorites();
  }, [category, selectedConditions, priceRange, selectedBrands, city, area, searchParams]);

  const fetchListings = async (overrideSearch?: string) => {
    try {
      const params: any = {};
      if (category) params.category = category;
      const q = overrideSearch !== undefined ? overrideSearch : search;
      if (q) params.search = q;
      if (priceRange[0] > 0) params.min_price = priceRange[0];
      if (priceRange[1] < 500000) params.max_price = priceRange[1];
      let data = await listingService.getListings(params);
      if (selectedConditions.length > 0) data = data.filter((l: any) => selectedConditions.includes(l.condition));
      if (selectedBrands.length > 0) data = data.filter((l: any) => l.brand && selectedBrands.includes(l.brand));
      if (city && city !== "Pakistan") {
        data = data.filter((l: any) => {
          const loc = l.location || "";
          return loc.includes(city) && (!area || loc.includes(area));
        });
      }
      setListings(data);
    } catch { /* silent */ }
    finally { setLoading(false); }
  };

  const fetchFavorites = async () => {
    try {
      const favs = await favoritesService.getFavorites();
      setFavoriteIds(new Set(favs.map((f: any) => f.id)));
    } catch { /* silent */ }
  };

  const toggleFavorite = async (listingId: number, e: React.MouseEvent) => {
    e.preventDefault(); e.stopPropagation();
    if (!currentUser?.id) { toast({ title: "Login Required", description: "Please login to save listings", variant: "destructive" }); return; }
    setTogglingFavorite(listingId);
    try {
      if (favoriteIds.has(listingId)) {
        await favoritesService.removeFavorite(listingId);
        setFavoriteIds(prev => { const s = new Set(prev); s.delete(listingId); return s; });
        toast({ title: "Removed", description: "Removed from saved listings" });
      } else {
        await favoritesService.addFavorite(listingId);
        setFavoriteIds(prev => new Set([...prev, listingId]));
        const listing = listings.find(l => l.id === listingId);
        if (listing) analyticsService.trackActivity({ activity_type: "favorite", listing_id: listingId, category: listing.category }).catch(() => { });
        toast({ title: "Saved!", description: "Added to saved listings" });
      }
    } catch { toast({ title: "Error", description: "Failed to update favorites", variant: "destructive" }); }
    finally { setTogglingFavorite(null); }
  };

  const handleSearch = async () => {
    fetchListings();
    if (search.trim()) {
      setLastSearch(search.trim());
      try { await analyticsService.trackActivity({ activity_type: "search", search_query: search.trim(), category: category || undefined, session_id: "web-session" }); } catch { /* silent */ }
    }
  };

  const resetFilters = () => { setCategory(""); setSelectedConditions([]); setPriceRange([0, 500000]); setSelectedBrands([]); setCity(""); setArea(""); setSearch(""); };
  const activeFilterCount = selectedConditions.length + selectedBrands.length + (category ? 1 : 0) + (priceRange[0] > 0 || priceRange[1] < 500000 ? 1 : 0) + (city && city !== "Pakistan" ? 1 : 0);

  const FilterSection = ({ title, id, children }: { title: string; id: keyof typeof filterExpanded; children: React.ReactNode }) => (
    <div className="border-b border-border/40 last:border-0">
      <button
        onClick={() => setFilterExpanded(prev => ({ ...prev, [id]: !prev[id] }))}
        className="w-full flex items-center justify-between py-3 px-4 text-sm font-semibold text-foreground/80 hover:text-foreground transition-colors"
      >
        {title}
        {filterExpanded[id] ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
      </button>
      {filterExpanded[id] && <div className="pb-4 px-4">{children}</div>}
    </div>
  );

  return (
    <div className="min-h-screen page-content">
      {/* ── Page Header ── */}
      <div className="bg-white/80 backdrop-blur-md border-b border-border/50 shadow-sm">
        <div className="container mx-auto px-4 py-5">
          <h1 className="text-2xl md:text-3xl font-black text-foreground mb-4">Browse Listings</h1>
          {/* Search + filter toggle */}
          <div className="flex gap-2">
            <div className="flex-1 relative group premium-input">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
              <Input
                placeholder="Search products, brands, models..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                onKeyDown={e => e.key === "Enter" && handleSearch()}
                className="pl-10 h-11 rounded-xl border-border/60 bg-white/70 focus:bg-white text-sm focus:border-primary/50 focus:ring-2 focus:ring-primary/10 transition-all"
              />
            </div>
            <Button onClick={handleSearch} className="h-11 px-5 rounded-xl font-bold bg-primary hover:bg-primary/90 shadow-md shadow-primary/20">
              <Search className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
              className={`h-11 px-4 rounded-xl font-semibold lg:hidden transition-all border-2 ${showFilters ? "bg-primary text-white border-primary" : "border-border hover:border-primary/50"}`}
            >
              <SlidersHorizontal className="h-4 w-4 mr-2" />
              Filters {activeFilterCount > 0 && <Badge className="ml-1.5 h-5 w-5 p-0 flex items-center justify-center rounded-full bg-white text-primary text-[10px] font-black">{activeFilterCount}</Badge>}
            </Button>
          </div>
          {/* Active filter pills */}
          {activeFilterCount > 0 && (
            <div className="flex items-center gap-2 mt-3 flex-wrap animate-fade-in-up">
              {lastSearch && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-semibold border border-primary/20">
                  <Tag className="h-3 w-3" /> "{lastSearch}"
                  <button onClick={() => { setLastSearch(""); setSearch(""); fetchListings(); }} className="hover:text-red-600 ml-0.5">✕</button>
                </span>
              )}
              {category && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold border border-blue-200">
                  {category} <button onClick={() => setCategory("")} className="hover:text-red-600 ml-0.5">✕</button>
                </span>
              )}
              <button onClick={resetFilters} className="text-xs text-muted-foreground hover:text-destructive font-medium flex items-center gap-1 ml-auto">
                <X className="h-3 w-3" /> Clear all
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        <div className="flex gap-6">

          {/* ── Sidebar ── */}
          <aside className={`${showFilters ? "block" : "hidden"} lg:block w-full lg:w-64 flex-shrink-0`}>
            <div className="bg-white rounded-2xl border border-border/60 shadow-[var(--shadow-sm)] overflow-hidden lg:sticky lg:top-[130px]">
              {/* Header */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-border/40">
                <div className="flex items-center gap-2">
                  <Filter className="h-4 w-4 text-primary" />
                  <span className="font-bold text-sm">Filters</span>
                  {activeFilterCount > 0 && (
                    <span className="h-5 w-5 flex items-center justify-center rounded-full bg-primary text-white text-[10px] font-black">{activeFilterCount}</span>
                  )}
                </div>
                {activeFilterCount > 0 && (
                  <Button variant="ghost" size="sm" onClick={resetFilters} className="h-7 px-2 text-xs text-muted-foreground hover:text-destructive">
                    <X className="h-3 w-3 mr-1" /> Clear
                  </Button>
                )}
              </div>

              {/* Category */}
              <FilterSection title="Category" id="cat">
                <div className="space-y-1.5">
                  {[{ v: "", l: "All Categories" }, { v: "mobile", l: "📱 Mobile" }, { v: "laptop", l: "💻 Laptop" }, { v: "furniture", l: "🛋️ Furniture" }].map(({ v, l }) => (
                    <button
                      key={v}
                      onClick={() => setCategory(v)}
                      className={`w-full text-left px-3 py-2 rounded-xl text-sm font-medium transition-all ${category === v || (v === "" && !category) ? "bg-primary text-white shadow-sm" : "hover:bg-muted text-foreground/70"}`}
                    >
                      {l}
                    </button>
                  ))}
                </div>
              </FilterSection>

              {/* Location */}
              <FilterSection title="Location" id="loc">
                <div className="space-y-2">
                  <Select value={city} onValueChange={v => { setCity(v); setArea(""); }}>
                    <SelectTrigger className="rounded-xl h-10 text-sm">
                      <SelectValue placeholder="All Pakistan" />
                    </SelectTrigger>
                    <SelectContent className="rounded-xl">
                      <SelectItem value="Pakistan">🇵🇰 All Pakistan</SelectItem>
                      <SelectItem value="Islamabad">Islamabad</SelectItem>
                      <SelectItem value="Rawalpindi">Rawalpindi</SelectItem>
                    </SelectContent>
                  </Select>
                  {city && city !== "Pakistan" && (
                    <Select value={area} onValueChange={setArea}>
                      <SelectTrigger className="rounded-xl h-10 text-sm">
                        <SelectValue placeholder={`All ${city}`} />
                      </SelectTrigger>
                      <SelectContent className="rounded-xl">
                        <SelectItem value=" ">All {city}</SelectItem>
                        {(city === "Islamabad" ? ISB : RWP).map(a => <SelectItem key={a} value={a}>{a}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  )}
                </div>
              </FilterSection>

              {/* Condition */}
              <FilterSection title="Condition" id="cond">
                <div className="space-y-2">
                  {conditions.map(cond => (
                    <label key={cond} className="flex items-center gap-3 cursor-pointer group">
                      <Checkbox
                        id={`cond-${cond}`}
                        checked={selectedConditions.includes(cond)}
                        onCheckedChange={checked => setSelectedConditions(prev => checked ? [...prev, cond] : prev.filter(c => c !== cond))}
                        className="rounded-md data-[state=checked]:bg-primary data-[state=checked]:border-primary"
                      />
                      <span className="text-sm font-medium capitalize text-foreground/80 group-hover:text-foreground transition-colors">{cond}</span>
                    </label>
                  ))}
                </div>
              </FilterSection>

              {/* Price */}
              <FilterSection title="Price Range" id="price">
                <div className="space-y-3">
                  <Slider min={0} max={500000} step={5000} value={priceRange} onValueChange={v => setPriceRange(v as [number, number])} className="w-full" />
                  <div className="flex justify-between">
                    <span className="text-xs font-semibold bg-muted px-2 py-1 rounded-lg text-foreground/70">PKR {priceRange[0].toLocaleString()}</span>
                    <span className="text-xs font-semibold bg-muted px-2 py-1 rounded-lg text-foreground/70">PKR {priceRange[1].toLocaleString()}</span>
                  </div>
                </div>
              </FilterSection>

              {/* Brand */}
              <FilterSection title="Brand" id="brand">
                <div className="space-y-1.5 max-h-48 overflow-y-auto scrollbar-thin pr-1">
                  {brands.map(brand => (
                    <label key={brand} className="flex items-center gap-3 cursor-pointer group">
                      <Checkbox
                        id={`brand-${brand}`}
                        checked={selectedBrands.includes(brand)}
                        onCheckedChange={checked => setSelectedBrands(prev => checked ? [...prev, brand] : prev.filter(b => b !== brand))}
                        className="rounded-md data-[state=checked]:bg-primary data-[state=checked]:border-primary"
                      />
                      <span className="text-sm font-medium text-foreground/80 group-hover:text-foreground transition-colors">{brand}</span>
                    </label>
                  ))}
                </div>
              </FilterSection>

              {/* Summary */}
              {activeFilterCount > 0 && (
                <div className="px-4 py-3 bg-primary/5 border-t border-primary/10">
                  <p className="text-xs text-primary font-semibold">{listings.length} result{listings.length !== 1 ? "s" : ""} found</p>
                </div>
              )}
            </div>
          </aside>

          {/* ── Main Grid ── */}
          <div className="flex-1 min-w-0">
            {/* Results header */}
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-muted-foreground font-medium">
                {loading ? "Loading..." : `${listings.length} listing${listings.length !== 1 ? "s" : ""}${lastSearch ? ` for "${lastSearch}"` : ""}`}
              </p>
            </div>

            {loading && (
              <div className="grid grid-cols-2 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="rounded-2xl overflow-hidden bg-white border border-border/50 shadow-sm animate-pulse">
                    <div className="aspect-video bg-muted shimmer" />
                    <div className="p-4 space-y-2.5">
                      <div className="h-4 bg-muted rounded-full shimmer w-3/4" />
                      <div className="h-5 bg-muted rounded-full shimmer w-1/2" />
                      <div className="h-3 bg-muted rounded-full shimmer w-2/5" />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {!loading && listings.length === 0 && (
              <div className="bg-white rounded-2xl border border-border/60 shadow-sm text-center py-20 px-4">
                <div className="text-5xl mb-4">🔍</div>
                <h3 className="text-xl font-bold text-foreground mb-2">No listings found{lastSearch ? ` for "${lastSearch}"` : ""}</h3>
                <p className="text-muted-foreground text-sm mb-6">Try adjusting your filters or search terms</p>
                {(activeFilterCount > 0 || lastSearch) && (
                  <Button onClick={() => { resetFilters(); setLastSearch(""); }} variant="outline" className="rounded-xl">
                    Clear all filters
                  </Button>
                )}
              </div>
            )}

            {!loading && listings.length > 0 && (
              <div className="grid grid-cols-2 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {listings.map((listing, i) => {
                  const imgs = (() => { try { return JSON.parse(listing.images || "[]"); } catch { return []; } })();
                  const imgUrl = imgs[0] ? getImageUrl(imgs[0]) : null;
                  const isFav = favoriteIds.has(listing.id);
                  const condNum = parseInt(listing.condition);
                  const condOk = !isNaN(condNum);

                  return (
                    <Link key={listing.id} to={`/product/${listing.id}`} className="group">
                      <div className="relative bg-white rounded-2xl overflow-hidden border border-border/50 shadow-[var(--shadow-xs)] hover:shadow-[var(--shadow-lg)] hover:-translate-y-1 hover:border-primary/20 transition-all duration-300 h-full flex flex-col">
                        {/* Favorite */}
                        <Button
                          variant="ghost"
                          size="icon"
                          className={`absolute top-2.5 right-2.5 z-10 rounded-full h-8 w-8 shadow-md border border-white/60 transition-all duration-200 ${isFav ? "bg-red-50 opacity-100" : "bg-white/90 opacity-0 group-hover:opacity-100"}`}
                          onClick={e => toggleFavorite(listing.id, e)}
                          disabled={togglingFavorite === listing.id}
                        >
                          {togglingFavorite === listing.id ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Heart className={`h-3.5 w-3.5 ${isFav ? "text-red-500 fill-red-500" : "text-foreground/60 hover:text-red-500"}`} />
                          )}
                        </Button>

                        {/* Image */}
                        <div className="aspect-video bg-muted relative overflow-hidden">
                          {condOk && (
                            <span className={`absolute top-2 left-2 z-10 badge-pill border text-[10px] ${condClass(condNum)}`}>
                              {getConditionLabel(condNum)} {condNum}/10
                            </span>
                          )}
                          {imgUrl ? (
                            <img src={imgUrl} alt={listing.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" loading="lazy" />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-3xl bg-gradient-to-br from-muted to-muted/50">📦</div>
                          )}
                          {listing.location && (
                            <span className="absolute bottom-2 left-2 badge-pill bg-white/90 text-foreground text-[10px] shadow-sm backdrop-blur-sm">
                              📍 {listing.location.split(",")[0]}
                            </span>
                          )}
                          {imgs.length > 1 && (
                            <span className="absolute bottom-2 right-2 badge-pill bg-black/60 text-white text-[10px]">
                              📷 {imgs.length}
                            </span>
                          )}
                        </div>

                        {/* Info */}
                        <div className="p-4 flex flex-col gap-2 flex-1">
                          <div className="flex items-start justify-between gap-2">
                            <h3 className="font-bold text-sm text-foreground line-clamp-1 group-hover:text-primary transition-colors flex-1">{listing.title}</h3>
                            <Badge variant="secondary" className="text-[10px] flex-shrink-0 rounded-full">{listing.category}</Badge>
                          </div>
                          <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed">{listing.description}</p>
                          <div className="flex items-center justify-between mt-auto pt-2 border-t border-border/30">
                            <span className="text-lg font-black text-primary">{formatCurrency(listing.price)}</span>
                            {condOk && (
                              <Badge className={`${condClass(condNum)} border text-[10px] font-semibold rounded-full`}>
                                {getConditionLabel(condNum)} {condNum}/10
                              </Badge>
                            )}
                          </div>
                          {/* Extra tags */}
                          <div className="flex flex-wrap gap-1">
                            {listing.brand && <span className="badge-pill bg-muted text-muted-foreground">🏷️ {listing.brand}</span>}
                            {listing.category === 'furniture' && listing.furniture_type && <span className="badge-pill bg-muted text-muted-foreground">🪑 {listing.furniture_type}</span>}
                          </div>
                          {listing.views > 0 && (
                            <p className="text-[11px] text-muted-foreground/70">{listing.views} views</p>
                          )}
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
