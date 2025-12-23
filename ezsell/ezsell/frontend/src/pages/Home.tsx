import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Navigation from "@/components/Navigation";
import { Search, MapPin, Plus, Heart, ChevronRight, Loader2 } from "lucide-react";
import { listingService, getImageUrl, favoritesService } from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";

const Home = () => {
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
  
  const currentUser = JSON.parse(localStorage.getItem('user') || '{}');

  const categories = [
    { id: "all", name: "All Categories", icon: "📦" },
    { id: "mobiles", name: "Mobile Phones", icon: "📱" },
    { id: "laptops", name: "Laptops", icon: "💻" },
    { id: "furniture", name: "Furniture", icon: "🛋️" },
  ];

  useEffect(() => {
    loadListings();
    if (currentUser?.id) {
      loadFavorites();
    }
  }, [selectedCategory, city, area]);

  // Reload listings when component is focused (user navigates back to home)
  useEffect(() => {
    const handleFocus = () => {
      loadListings();
      if (currentUser?.id) {
        loadFavorites();
      }
    };
    
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [selectedCategory, city, area]);

  const loadListings = async () => {
    try {
      setLoading(true);
      const params = selectedCategory !== "all" ? { category: selectedCategory } : {};
      const data = await listingService.getAllListings(params);
      console.log('Loaded listings:', data);
      setListings(Array.isArray(data) ? data : []);
    } catch (error: any) {
      console.error('Error loading listings:', error);
      setListings([]);
      toast({
        title: "Error loading listings",
        description: error.response?.data?.detail || "Failed to load listings",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const loadFavorites = async () => {
    try {
      const favorites = await favoritesService.getFavorites();
      setFavoriteIds(new Set(favorites.map((f: any) => f.id)));
    } catch (error) {
      console.error('Failed to load favorites:', error);
    }
  };

  // Helper to get first image from listing (supports both old and new format)
  const getListingImage = (listing: any): string | null => {
    // Check new 'images' JSON field first
    if (listing?.images) {
      try {
        const parsedImages = typeof listing.images === 'string' 
          ? JSON.parse(listing.images) 
          : listing.images;
        if (Array.isArray(parsedImages) && parsedImages.length > 0) {
          return parsedImages[0];
        }
      } catch (e) {
        console.error('Failed to parse images field:', e);
      }
    }
    
    // Fallback to old image_url field
    if (listing?.image_url) {
      return listing.image_url;
    }
    
    return null;
  };

  const toggleFavorite = async (listingId: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!currentUser?.id) {
      toast({
        title: "Login Required",
        description: "Please login to save listings",
        variant: "destructive",
      });
      navigate('/login');
      return;
    }
    
    setTogglingFavorite(listingId);
    try {
      if (favoriteIds.has(listingId)) {
        await favoritesService.removeFromFavorites(listingId);
        setFavoriteIds(prev => {
          const newSet = new Set(prev);
          newSet.delete(listingId);
          return newSet;
        });
        toast({
          title: "Removed",
          description: "Removed from your saved listings",
        });
      } else {
        await favoritesService.addToFavorites(listingId);
        setFavoriteIds(prev => new Set([...prev, listingId]));
        toast({
          title: "Saved",
          description: "Added to your saved listings",
        });
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
      toast({
        title: "Error",
        description: "Failed to update favorites",
        variant: "destructive",
      });
    } finally {
      setTogglingFavorite(null);
    }
  };

  const handleSearch = () => {
    if (searchQuery.trim()) {
      navigate(`/listings?search=${encodeURIComponent(searchQuery)}`);
    }
  };

  const filteredListings = listings.filter((listing) => {
    // Search filter
    if (searchQuery && !listing.title.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    
    // Location filter
    if (city && city !== 'Pakistan') {
      const location = listing.location || '';
      if (!location.includes(city)) {
        return false;
      }
      if (area && area.trim() !== '') {
        if (!location.includes(area)) {
          return false;
        }
      }
    }
    
    return true;
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f5f5f0] via-[#e8e8dc] to-[#f5f5f0]">
      <Navigation />
      
      {/* Hero Section */}
      <section className="relative pt-16 pb-20 px-4 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-[#143109]/5 via-transparent to-[#AAAE7F]/5" />
        <div className="container mx-auto max-w-6xl relative">
          <div className="text-center mb-10">
            <div className="flex flex-col items-center justify-center mb-6">
              <img src="/images/ezsell-logo.png" alt="EZSELL Logo" className="h-32 w-auto" onError={(e) => { e.currentTarget.style.display = 'none'; e.currentTarget.nextElementSibling?.classList.remove('hidden'); }} />
              <div className="hidden flex-col items-center">
                <h1 className="text-6xl font-bold text-[#143109]">EZ SELL</h1>
                <p className="text-2xl text-[#5B9BD5] font-semibold mt-2">BAICH DIAAA !!!</p>
              </div>
            </div>
            <h1 className="text-5xl md:text-6xl font-bold text-[#143109] mb-4 animate-fade-in">
              Buy & Sell With <span className="text-[#AAAE7F]">Confidence</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Discover amazing deals on mobile phones, laptops, furniture and more
            </p>
            
            {/* Enhanced Search Bar */}
            <div className="max-w-3xl mx-auto">
              <div className="flex gap-3 bg-white rounded-2xl shadow-2xl p-3 border-2 border-[#143109]/20">
                <div className="flex-1 flex gap-3">
                  <Input
                    type="text"
                    placeholder="What are you looking for today?"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                    className="h-14 text-lg border-0 focus-visible:ring-0 focus-visible:ring-offset-0"
                  />
                  <Button onClick={handleSearch} size="lg" className="px-8 h-14 text-lg bg-[#143109] hover:bg-[#143109]/90">
                    <Search className="h-6 w-6 mr-2" />
                    Search
                  </Button>
                </div>
              </div>
            </div>
          </div>
          
          {/* Quick Stats */}
          <div className="grid grid-cols-3 gap-4 max-w-3xl mx-auto mt-8">
            <div className="text-center p-4 bg-white/60 backdrop-blur rounded-xl shadow-md hover:shadow-lg transition-shadow">
              <div className="text-3xl font-bold text-[#143109]">{listings.length}</div>
              <div className="text-sm text-gray-600 font-medium">Products Available</div>
            </div>
            <div className="text-center p-4 bg-white/60 backdrop-blur rounded-xl shadow-md hover:shadow-lg transition-shadow">
              <div className="text-3xl font-bold text-[#143109]">100%</div>
              <div className="text-sm text-gray-600 font-medium">Verified Sellers</div>
            </div>
            <div className="text-center p-4 bg-white/60 backdrop-blur rounded-xl shadow-md hover:shadow-lg transition-shadow">
              <div className="text-3xl font-bold text-[#143109]">24/7</div>
              <div className="text-sm text-gray-600 font-medium">Support Available</div>
            </div>
          </div>
        </div>
      </section>

      {/* Categories Bar */}
      <section className="py-6 px-4 bg-white/80 backdrop-blur-sm shadow-sm">
        <div className="container mx-auto">
          <h3 className="text-xl font-bold text-[#143109] mb-4 text-center">Browse by Category</h3>
          <div className="flex gap-3 justify-center overflow-x-auto pb-2 scrollbar-hide">
            {categories.map((category) => (
              <Button
                key={category.id}
                variant={selectedCategory === category.id ? "default" : "outline"}
                onClick={() => setSelectedCategory(category.id)}
                className={`flex-shrink-0 whitespace-nowrap h-12 px-6 text-base font-semibold transition-all ${
                  selectedCategory === category.id
                    ? "bg-[#143109] hover:bg-[#143109]/90 shadow-lg scale-105"
                    : "hover:border-[#143109] hover:text-[#143109]"
                }`}
              >
                <span className="mr-2 text-xl">{category.icon}</span>
                {category.name}
              </Button>
            ))}
          </div>
        </div>
      </section>

      {/* Location Filter Bar */}
      <section className="py-4 px-4 bg-white/60 backdrop-blur-sm border-t">
        <div className="container mx-auto">
          <div className="flex flex-wrap gap-3 justify-center items-center">
            <div className="flex items-center gap-2">
              <MapPin className="h-5 w-5 text-[#143109]" />
              <span className="font-semibold text-[#143109]">Filter by Location:</span>
            </div>
            <div className="flex gap-3">
              <Button
                variant={!city || city === 'Pakistan' ? "default" : "outline"}
                onClick={() => { setCity('Pakistan'); setArea(''); }}
                className={`h-10 px-6 ${
                  !city || city === 'Pakistan'
                    ? "bg-[#143109] hover:bg-[#143109]/90"
                    : "hover:border-[#143109] hover:text-[#143109]"
                }`}
              >
                🇵🇰 All Pakistan
              </Button>
              <Button
                variant={city === 'Islamabad' ? "default" : "outline"}
                onClick={() => { setCity('Islamabad'); setArea(''); }}
                className={`h-10 px-6 ${
                  city === 'Islamabad'
                    ? "bg-[#143109] hover:bg-[#143109]/90"
                    : "hover:border-[#143109] hover:text-[#143109]"
                }`}
              >
                Islamabad
              </Button>
              <Button
                variant={city === 'Rawalpindi' ? "default" : "outline"}
                onClick={() => { setCity('Rawalpindi'); setArea(''); }}
                className={`h-10 px-6 ${
                  city === 'Rawalpindi'
                    ? "bg-[#143109] hover:bg-[#143109]/90"
                    : "hover:border-[#143109] hover:text-[#143109]"
                }`}
              >
                Rawalpindi
              </Button>
            </div>
            {city && city !== 'Pakistan' && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Area:</span>
                <select
                  value={area}
                  onChange={(e) => setArea(e.target.value)}
                  className="h-10 px-4 rounded-md border border-gray-300 bg-white text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#143109]"
                >
                  <option value="">All {city}</option>
                  {city === 'Islamabad' && [
                    'Bahria Town', 'Blue Area', 'DHA Phase 1', 'DHA Phase 2',
                    'F-6', 'F-7', 'F-8', 'F-10', 'F-11',
                    'G-6', 'G-7', 'G-8', 'G-9', 'G-10', 'G-11', 'G-13', 'G-14', 'G-15',
                    'I-8', 'I-9', 'I-10', 'I-11', 'I-14',
                    'PWD Housing Scheme', 'Sector B-17', 'Sector C-18', 'Sector D-12', 'Sector E-11',
                    'Zaraj Housing Society'
                  ].sort().map(a => <option key={a} value={a}>{a}</option>)}
                  {city === 'Rawalpindi' && [
                    'Adyala Road', 'Airport Housing Society',
                    'Bahria Town Phase 1', 'Bahria Town Phase 2', 'Bahria Town Phase 3',
                    'Bahria Town Phase 4', 'Bahria Town Phase 5', 'Bahria Town Phase 6',
                    'Bahria Town Phase 7', 'Bahria Town Phase 8',
                    'Chaklala Scheme 3', 'DHA Phase 1', 'DHA Phase 2',
                    'Gulraiz Housing Scheme', 'Gulshan-e-Abad',
                    'National Police Foundation', 'Rehmanabad',
                    'Saddar', 'Satellite Town', 'Soan Garden', 'Tench Bhatta',
                    'Westridge'
                  ].sort().map(a => <option key={a} value={a}>{a}</option>)}
                </select>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Main Content - Listings Grid */}
      <section className="py-8 px-4">
        <div className="container mx-auto">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h2 className="text-3xl font-bold text-[#143109] mb-1">Fresh Recommendations</h2>
              <p className="text-gray-600">Handpicked deals just for you</p>
            </div>
            <Link to="/listings">
              <Button variant="outline" className="flex items-center gap-2 hover:bg-[#143109] hover:text-white">
                View all <ChevronRight className="h-5 w-5" />
              </Button>
            </Link>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {[...Array(8)].map((_, i) => (
                <Card key={i} className="overflow-hidden">
                  <div className="aspect-square bg-muted animate-pulse" />
                  <CardContent className="p-4">
                    <div className="h-4 bg-muted rounded animate-pulse mb-2" />
                    <div className="h-6 bg-muted rounded animate-pulse w-1/2" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : filteredListings.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground text-lg">No listings found</p>
              <Link to="/dashboard">
                <Button className="mt-4">
                  <Plus className="h-4 w-4 mr-2" />
                  Post Your Ad
                </Button>
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {filteredListings.slice(0, 20).map((listing) => (
                <Link key={listing.id} to={`/product/${listing.id}`}>
                  <Card className="overflow-hidden hover:shadow-2xl transition-all duration-300 cursor-pointer group border-2 border-transparent hover:border-[#143109]/30 bg-white">
                    <div className="relative aspect-square overflow-hidden bg-muted">
                      {getListingImage(listing) && getImageUrl(getListingImage(listing)!) ? (
                        <img
                          src={getImageUrl(getListingImage(listing)!)!}
                          alt={listing.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-4xl">
                          📦
                        </div>
                      )}
                      {listing.additional_images && JSON.parse(listing.additional_images).length > 0 && (
                        <Badge className="absolute bottom-2 left-2 bg-black/70 text-white text-xs">
                          📷 {JSON.parse(listing.additional_images).length + 1}
                        </Badge>
                      )}
                      <button 
                        className={`absolute top-2 right-2 p-2 rounded-full transition-all shadow-md hover:shadow-lg z-10 ${
                          favoriteIds.has(listing.id)
                            ? 'bg-red-50 hover:bg-red-100'
                            : 'bg-white/90 hover:bg-white'
                        }`}
                        onClick={(e) => toggleFavorite(listing.id, e)}
                        disabled={togglingFavorite === listing.id}
                      >
                        {togglingFavorite === listing.id ? (
                          <Loader2 className="h-4 w-4 animate-spin text-gray-500" />
                        ) : (
                          <Heart 
                            className={`h-4 w-4 transition-colors ${
                              favoriteIds.has(listing.id)
                                ? 'text-red-500 fill-red-500'
                                : 'text-gray-600 hover:text-red-500'
                            }`} 
                          />
                        )}
                      </button>
                      {listing.is_featured && (
                        <Badge className="absolute top-2 left-2 bg-yellow-500">
                          Featured
                        </Badge>
                      )}
                    </div>
                    <CardContent className="p-4">
                      <h3 className="font-semibold text-base line-clamp-2 mb-2 group-hover:text-primary transition-colors">
                        {listing.title}
                      </h3>
                      <p className="text-2xl font-bold text-primary mb-2">
                        PKR {listing.price.toLocaleString()}
                      </p>
                      <div className="flex items-center text-sm text-muted-foreground">
                        <MapPin className="h-3 w-3 mr-1" />
                        <span className="line-clamp-1">
                          {listing.location || "Pakistan"}
                        </span>
                      </div>
                      <div className="mt-3 pt-3 border-t">
                        <p className="text-xs text-gray-600 font-medium">
                          Posted by {listing.owner?.username || 'User'}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(listing.created_at).toLocaleDateString('en-US', { 
                            month: 'short', 
                            day: 'numeric', 
                            year: 'numeric' 
                          })}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Floating Sell Button - OLX Style */}
      <Link to="/dashboard">
        <Button
          size="lg"
          className="fixed bottom-8 right-8 rounded-full h-14 px-6 shadow-xl hover:shadow-2xl transition-shadow z-50"
        >
          <Plus className="h-5 w-5 mr-2" />
          SELL
        </Button>
      </Link>
    </div>
  );
};

export default Home;
