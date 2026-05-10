import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { listingService, authService, getImageUrl, favoritesService, analyticsService } from '../lib/api.ts';
import { useToast } from '@/components/ui/use-toast';
import { Plus, Edit, Trash2, Package, Home, Heart, BarChart3, RefreshCw, Eye, EyeOff, Check } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend, PieChart, Pie, Cell } from 'recharts';
import { formatCurrency } from '../lib/utils.ts';
import { SmartImage } from '@/components/ui/SmartImage';

export default function Dashboard() {
  const [user, setUser] = useState<any>(null);
  const [listings, setListings] = useState<any[]>([]);
  const [favorites, setFavorites] = useState<any[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(true);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('listings');
  const navigate = useNavigate();
  const { toast } = useToast();

  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (!token) {
      navigate('/login');
      return;
    }
    fetchUserData();
    fetchMyListings();
    fetchFavorites();
    fetchAnalytics();
  }, []);

  const fetchUserData = async () => {
    try {
      const userData = await authService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      navigate('/login');
    }
  };

  const fetchMyListings = async () => {
    try {
      const data = await listingService.getMyListings();
      console.log('DEBUG: My Listings Data:', data);
      if (data && data.length > 0) {
        console.log('DEBUG: First Listing Keys:', Object.keys(data[0]));
        console.log('DEBUG: First Listing is_active:', data[0].is_active);
      }
      setListings(data);
    } catch (error) {
      console.error('Failed to fetch listings:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFavorites = async () => {
    try {
      const data = await favoritesService.getFavorites();
      setFavorites(data);
    } catch (error) {
      console.error('Failed to fetch favorites:', error);
    }
  };

  const fetchAnalytics = async () => {
    setAnalyticsLoading(true);
    try {
      const data = await analyticsService.getDashboard(30);
      setAnalytics(data);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
      toast({
        title: 'Analytics Error',
        description: 'Failed to load your insights. Please try refreshing.',
        variant: 'destructive',
      });
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const handleRemoveFavorite = async (listingId: number) => {
    try {
      await favoritesService.removeFavorite(listingId);
      toast({
        title: 'Removed',
        description: 'Listing removed from favorites',
      });
      fetchFavorites();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to remove from favorites',
        variant: 'destructive',
      });
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

  const getConditionLabel = (condition: string | number) => {
    const c = typeof condition === 'string' ? parseInt(condition) : condition;
    if (c >= 10) return "Brand New";
    if (c >= 9) return "Like New";
    if (c >= 7) return "Excellent";
    if (c >= 5) return "Good";
    if (c >= 3) return "Fair";
    return "Poor";
  };



  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this listing?')) return;

    try {
      await listingService.deleteListing(id);
      toast({
        title: 'Deleted',
        description: 'Listing deleted successfully',
      });
      fetchMyListings();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete listing',
        variant: 'destructive',
      });
    }
  };

  const handleStatusToggle = async (id: number, updates: { is_sold?: boolean, is_active?: boolean }) => {
    try {
      await listingService.toggleListingStatus(id, updates);
      toast({
        title: updates.is_sold ? 'Marked as Sold' : updates.is_active === false ? 'Ad Hidden' : 'Ad Unhidden',
        description: updates.is_sold
          ? 'Your listing has been marked as sold and is no longer publicly visible.'
          : updates.is_active === false
            ? 'Your listing is now hidden from public view.'
            : 'Your listing is now live and visible to everyone.',
      });
      fetchMyListings();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update listing status. Please try again.',
        variant: 'destructive',
      });
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#f5f5f0] to-[#e8e8dc] flex items-center justify-center">
        <div className="text-slate-900 text-xl font-semibold">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f5f5f0] to-[#e8e8dc]">
      <div className="container mx-auto px-4 py-8">
        {/* Email Verification Nudge */}
        {user && !user.is_verified && (
          <Alert variant="destructive" className="mb-8 border-2 bg-red-50 border-red-200">
            <div className="flex items-center gap-3">
              <Package className="h-5 w-5 text-red-600" />
              <div className="flex-1">
                <p className="font-bold text-red-900">Account Not Verified</p>
                <p className="text-red-700 text-sm">Please verify your email to post new advertisements and build trust with buyers.</p>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="bg-red-100 hover:bg-red-200 text-red-900 border-red-300"
                onClick={() => navigate('/settings')}
              >
                Verify Now
              </Button>
            </div>
          </Alert>
        )}

        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 mb-2">Dashboard</h1>
            <p className="text-slate-600">Welcome back, {user?.username}!</p>
          </div>
          <div className="flex items-center gap-4">
            <Button variant="outline" onClick={() => navigate('/listings')} className="hidden sm:flex transition-all active:scale-95">
              Browse Listings
            </Button>
            <Button variant="outline" onClick={handleLogout} className="transition-all active:scale-95">
              Logout
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Listings</CardTitle>
              <Package className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{listings.length}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Listings</CardTitle>
              <Package className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {listings.filter(l => !l.is_sold).length}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Views</CardTitle>
              <Package className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {listings.reduce((sum, l) => sum + l.views, 0)}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Saved Favorites</CardTitle>
              <Heart className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{favorites.length}</div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs for My Listings and Favorites */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <div className="flex justify-between items-center mb-6">
            <TabsList>
              <TabsTrigger value="listings" className="gap-2">
                <Package className="h-4 w-4" />
                My Listings
              </TabsTrigger>
              <TabsTrigger value="favorites" className="gap-2">
                <Heart className="h-4 w-4" />
                Favorites ({favorites.length})
              </TabsTrigger>
              <TabsTrigger value="insights" className="gap-2">
                <BarChart3 className="h-4 w-4" />
                My Insights
              </TabsTrigger>
            </TabsList>
            <div className="flex gap-2">
              {activeTab === 'insights' && (
                <Button variant="outline" size="sm" onClick={fetchAnalytics} disabled={analyticsLoading}>
                  <RefreshCw className={`h-4 w-4 mr-2 ${analyticsLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              )}
              <Button onClick={() => navigate('/create-listing')}>
                <Plus className="mr-2 h-4 w-4" />
                Create Listing
              </Button>
            </div>
          </div>

          {/* My Listings Tab */}
          <TabsContent value="listings">
            {listings.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Package className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-lg text-muted-foreground mb-4">No listings yet</p>
                  <Button onClick={() => navigate('/create-listing')}>
                    <Plus className="mr-2 h-4 w-4" />
                    Create Your First Listing
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {listings.map((listing) => (
                  <Card key={listing.id}>
                    <CardHeader>
                      <div className="aspect-video bg-slate-200 rounded-md mb-4 flex items-center justify-center relative overflow-hidden">
                        {getListingImage(listing) && getImageUrl(getListingImage(listing)!) ? (
                          <SmartImage
                            src={getImageUrl(getListingImage(listing)!)!}
                            alt={listing.title}
                            className="w-full h-full object-cover rounded-md"
                            wrapperClassName="absolute inset-0"
                            priority="lazy"
                          />
                        ) : (
                          <span className="text-slate-500">No image</span>
                        )}
                        {listing.location && (
                          <Badge className="absolute top-2 left-2 bg-white/90 text-[#2E6091] text-[10px] font-bold px-2 py-0.5 border-0 shadow-sm backdrop-blur-sm z-10">
                            📍 {listing.location.split(',')[0]}
                          </Badge>
                        )}
                        {listing.condition && (
                          <Badge className="absolute top-8 left-2 bg-amber-500/90 text-white text-[10px] font-bold px-2 py-0.5 border-0 shadow-sm backdrop-blur-sm z-10">
                            {listing.condition}/10 {getConditionLabel(listing.condition)}
                          </Badge>
                        )}
                      </div>
                      <div className="flex justify-between items-start mb-2">
                        <CardTitle className="text-lg">{listing.title}</CardTitle>
                        <div className="flex flex-wrap gap-2">
                          {listing.is_sold ? (
                            <Badge variant="destructive" className="bg-red-500">Sold</Badge>
                          ) : listing.approval_status === 'pending' ? (
                            <Badge className="bg-yellow-500 text-white">Pending Review</Badge>
                          ) : listing.approval_status === 'rejected' ? (
                            <Badge variant="destructive">Rejected</Badge>
                          ) : (listing.approval_status === 'approved' || !listing.approval_status) && (listing.is_active || listing.is_active === undefined || listing.is_active === null) ? (
                            <Badge className="bg-green-500 text-white border-0 shadow-sm">Live & Active</Badge>
                          ) : (
                            <Badge variant="secondary" className="bg-gray-500 text-white border-0">Hidden</Badge>
                          )}
                        </div>
                      </div>
                      <CardDescription className="line-clamp-2">{listing.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {listing.approval_status === 'rejected' && listing.rejection_reason && (
                        <Alert variant="destructive" className="mb-4">
                          <AlertDescription>
                            <strong>Rejection Reason:</strong> {listing.rejection_reason}
                          </AlertDescription>
                        </Alert>
                      )}
                      {listing.approval_status === 'pending' && (
                        <Alert className="mb-4 bg-amber-50 border-amber-200">
                          <AlertDescription className="text-amber-800">
                            <strong>Under Review:</strong> Your listing is being reviewed by admin.
                          </AlertDescription>
                        </Alert>
                      )}
                      <div className="flex justify-between items-center mb-4">
                        <span className="text-2xl font-bold text-primary break-words overflow-hidden">
                          {formatCurrency(listing.price)}
                        </span>
                        <div className="flex gap-2">
                          {(() => {
                            const createdDate = new Date(listing.created_at);
                            const expiryDate = new Date(createdDate.getTime() + 30 * 24 * 60 * 60 * 1000);
                            const now = new Date();
                            const diffTime = expiryDate.getTime() - now.getTime();
                            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

                            if (diffDays <= 0) {
                              return <Badge variant="destructive">Expired</Badge>;
                            }
                            return (
                              <Badge variant="outline" className={diffDays <= 5 ? "text-amber-600 border-amber-200" : "text-blue-600 border-blue-200"}>
                                {diffDays} days left
                              </Badge>
                            );
                          })()}
                          <div className="text-sm text-muted-foreground">{listing.views} views</div>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-2 mb-4">
                        {listing.is_sold ? (
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-green-600 border-green-200 hover:bg-green-50"
                            onClick={() => handleStatusToggle(listing.id, { is_sold: false, is_active: true })}
                            disabled={listing.approval_status === 'pending'}
                          >
                            <Check className="mr-1 h-3 w-3" />
                            Mark Available
                          </Button>
                        ) : (
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-slate-600"
                            onClick={() => handleStatusToggle(listing.id, { is_sold: true })}
                            disabled={listing.approval_status === 'pending'}
                          >
                            Mark Sold
                          </Button>
                        )}

                        {(listing.is_active || (listing.is_active === undefined && (listing.approval_status === 'approved' || !listing.approval_status))) ? (
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-slate-600"
                            onClick={() => handleStatusToggle(listing.id, { is_active: false })}
                            disabled={listing.approval_status === 'pending'}
                          >
                            <EyeOff className="mr-1 h-3 w-3" />
                            Hide Ad
                          </Button>
                        ) : (
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-blue-600 border-blue-200 hover:bg-blue-50"
                            onClick={() => handleStatusToggle(listing.id, { is_active: true })}
                            disabled={listing.approval_status === 'pending'}
                          >
                            <Eye className="mr-1 h-3 w-3" />
                            Unhide
                          </Button>
                        )}
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" className="flex-1" onClick={() => navigate(`/product/${listing.id}`)}>
                          <Edit className="mr-2 h-4 w-4" />
                          View
                        </Button>
                        <Button variant="destructive" size="sm" onClick={() => handleDelete(listing.id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Favorites Tab */}
          <TabsContent value="favorites">
            {favorites.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Heart className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-lg text-muted-foreground mb-4">No saved favorites yet</p>
                  <p className="text-sm text-muted-foreground">Browse listings and click the heart icon to save items</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {favorites.map((listing) => (
                  <Card key={listing.id}>
                    <CardHeader>
                      <div className="aspect-video bg-slate-200 rounded-md mb-4 flex items-center justify-center relative">
                        {getListingImage(listing) && getImageUrl(getListingImage(listing)!) ? (
                          <SmartImage
                            src={getImageUrl(getListingImage(listing)!)!}
                            alt={listing.title}
                            className="w-full h-full object-cover rounded-md"
                            wrapperClassName="absolute inset-0"
                            priority="lazy"
                          />
                        ) : (
                          <span className="text-slate-500">No image</span>
                        )}
                        {listing.additional_images && JSON.parse(listing.additional_images).length > 0 && (
                          <Badge className="absolute bottom-2 left-2 bg-black/70 text-white text-xs">
                            📷 {JSON.parse(listing.additional_images).length + 1}
                          </Badge>
                        )}
                        {listing.location && (
                          <Badge className="absolute top-2 left-2 bg-white/90 text-[#2E6091] text-[10px] font-bold px-2 py-0.5 border-0 shadow-sm backdrop-blur-sm">
                            📍 {listing.location.split(',')[0]}
                          </Badge>
                        )}
                        {listing.condition && (
                          <Badge className="absolute top-8 left-2 bg-amber-500/90 text-white text-[10px] font-bold px-2 py-0.5 border-0 shadow-sm backdrop-blur-sm z-10">
                            {listing.condition}/10 {getConditionLabel(listing.condition)}
                          </Badge>
                        )}
                      </div>
                      <div className="flex justify-between items-start mb-2">
                        <CardTitle className="text-lg">{listing.title}</CardTitle>
                        <div className="flex gap-2">
                          {listing.is_sold && <Badge variant="destructive">Sold</Badge>}
                        </div>
                      </div>
                      <CardDescription className="line-clamp-2">{listing.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex justify-between items-center mb-4">
                        <span className="text-2xl font-bold text-primary break-words overflow-hidden">
                          {formatCurrency(listing.price)}
                        </span>
                        <div className="text-sm text-muted-foreground">{listing.views} views</div>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" className="flex-1" onClick={() => navigate(`/product/${listing.id}`)}>
                          <Package className="mr-2 h-4 w-4" />
                          View Details
                        </Button>
                        <Button variant="destructive" size="sm" onClick={() => handleRemoveFavorite(listing.id)}>
                          <Heart className="h-4 w-4 fill-current" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Insights Tab — Premium Light Redesign */}
          <TabsContent value="insights">
            {analyticsLoading ? (
              <div style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center',
                justifyContent: 'center', minHeight: 340, gap: 16,
              }}>
                <div style={{
                  width: 52, height: 52, borderRadius: '50%',
                  border: '3px solid hsl(210 20% 90%)',
                  borderTopColor: '#2E6091',
                  animation: 'spin 0.9s linear infinite',
                }} />
                <p style={{ color: 'hsl(210 15% 45%)', fontSize: 14 }}>Crunching your numbers…</p>
                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
                <style>{`
                  .ins-card {
                    background: #ffffff;
                    border: 1px solid hsl(210 20% 90%);
                    border-radius: 16px;
                    box-shadow: 0 4px 20px hsl(210 20% 40%/0.05), 0 1px 3px hsl(210 20% 40%/0.02);
                    padding: 24px;
                    color: hsl(210 25% 20%);
                    position: relative;
                    overflow: hidden;
                    transition: transform 0.2s, box-shadow 0.2s;
                  }
                  .ins-card:hover {
                    box-shadow: 0 8px 30px hsl(210 20% 40%/0.08), 0 2px 8px hsl(210 20% 40%/0.04);
                  }
                  .ins-card::before {
                    content: '';
                    position: absolute;
                    inset: 0;
                    background: radial-gradient(ellipse at top right, hsl(210 56% 96%/0.8), transparent 70%);
                    pointer-events: none;
                  }
                  .ins-label { color: hsl(210 15% 45%); font-size: 13px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; margin-bottom: 6px; }
                  .ins-value { font-size: 38px; font-weight: 800; line-height: 1; font-family: 'Plus Jakarta Sans','Inter',sans-serif; color: hsl(210 25% 15%); }
                  .ins-sub { font-size: 13px; color: hsl(210 15% 45%); margin-top: 6px; }
                  .ins-chip {
                    display: inline-flex; align-items: center; padding: 6px 14px;
                    border-radius: 999px; font-size: 13px; font-weight: 600;
                    border: 1px solid hsl(210 40% 90%);
                    background: hsl(210 40% 96%);
                    color: #2E6091;
                    cursor: default;
                    transition: all 0.2s;
                  }
                  .ins-chip:hover {
                    background: #2E6091;
                    border-color: #2E6091;
                    color: #fff;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px hsl(210 56% 40%/0.2);
                  }
                  .ins-section-title {
                    font-size: 14px; font-weight: 700; letter-spacing: 0.02em;
                    color: hsl(210 25% 20%);
                    display: flex; align-items: center; gap: 8px; margin-bottom: 16px;
                  }
                  .ins-section-title::after {
                    content: ''; flex: 1; height: 1px;
                    background: linear-gradient(90deg, hsl(210 20% 90%), transparent);
                  }
                `}</style>

                {/* ── KPI Strip ─────────────────────────────────────────── */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16 }}>
                  {[
                    { label: 'Searches', value: analytics?.total_searches ?? 0, icon: '🔍', accent: '#2E6091', bg: 'hsl(210 56% 96%)' },
                    { label: 'Listing Views', value: analytics?.total_views ?? 0, icon: '👁', accent: '#10b981', bg: 'hsl(160 84% 96%)' },
                    { label: 'Favorites', value: analytics?.total_favorites ?? 0, icon: '❤️', accent: '#ef4444', bg: 'hsl(350 84% 96%)' },
                    { label: 'Messages Sent', value: analytics?.total_messages ?? 0, icon: '💬', accent: '#8b5cf6', bg: 'hsl(258 84% 96%)' },
                  ].map(s => (
                    <div key={s.label} className="ins-card" style={{ paddingTop: 24, paddingBottom: 24 }}>
                      <div style={{
                        width: 44, height: 44, borderRadius: 12,
                        background: s.bg, border: `1px solid ${s.accent}20`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 20, marginBottom: 16, color: s.accent
                      }}>{s.icon}</div>
                      <div className="ins-value">{s.value.toLocaleString()}</div>
                      <div className="ins-label" style={{ marginTop: 8, marginBottom: 0 }}>{s.label}</div>
                    </div>
                  ))}
                </div>

                {/* ── Engagement Score + Keywords ───────────────────────── */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 16 }}>

                  {/* Engagement Gauge */}
                  <div className="ins-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
                    <div className="ins-section-title" style={{ width: '100%', marginBottom: 4 }}>Engagement Score</div>
                    {(() => {
                      const score = analytics?.engagement_score ?? 0;
                      const r = 54, circ = 2 * Math.PI * r;
                      const pct = Math.min(score / 100, 1);
                      const dash = pct * circ;
                      const color = score >= 70 ? '#10b981' : score >= 40 ? '#f59e0b' : '#ef4444';
                      const label = score >= 70 ? 'Excellent' : score >= 40 ? 'Good' : 'Growing';
                      return (
                        <div style={{ position: 'relative', width: 140, height: 140 }}>
                          <svg width="140" height="140" style={{ transform: 'rotate(-90deg)' }}>
                            <circle cx="70" cy="70" r={r} fill="none" stroke="hsl(210 20% 94%)" strokeWidth="10" />
                            <circle cx="70" cy="70" r={r} fill="none" stroke={color} strokeWidth="10"
                              strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
                              style={{ transition: 'stroke-dasharray 1.2s cubic-bezier(0.16,1,0.3,1)' }} />
                          </svg>
                          <div style={{
                            position: 'absolute', inset: 0, display: 'flex',
                            flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                          }}>
                            <div style={{ fontSize: 32, fontWeight: 900, color: hsl(210 25% 15%), lineHeight: 1 }}>{score}</div>
                            <div style={{ fontSize: 12, color: 'hsl(210 15% 50%)', marginTop: 2, fontWeight: 600 }}>/100</div>
                          </div>
                        </div>
                      );
                    })()}
                    <div style={{
                      fontSize: 14, fontWeight: 700, letterSpacing: '0.02em',
                      color: (analytics?.engagement_score ?? 0) >= 70 ? '#10b981' : (analytics?.engagement_score ?? 0) >= 40 ? '#f59e0b' : '#ef4444',
                      background: (analytics?.engagement_score ?? 0) >= 70 ? 'hsl(160 84% 96%)' : (analytics?.engagement_score ?? 0) >= 40 ? 'hsl(38 92% 95%)' : 'hsl(350 84% 96%)',
                      padding: '4px 12px', borderRadius: '999px'
                    }}>
                      {(analytics?.engagement_score ?? 0) >= 70 ? '🏆 Excellent' : (analytics?.engagement_score ?? 0) >= 40 ? '📈 Good' : '🌱 Growing'}
                    </div>
                    <div className="ins-sub" style={{ textAlign: 'center', lineHeight: 1.5, marginTop: 4 }}>
                      How active you are on EzSell
                    </div>
                  </div>

                  {/* Top Keywords */}
                  <div className="ins-card">
                    <div className="ins-section-title">Top Keywords</div>
                    <p className="ins-sub" style={{ marginBottom: 20 }}>Extracted from your search & browse history</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                      {(analytics?.top_keywords ?? []).length > 0
                        ? analytics.top_keywords.map((kw: any, idx: number) => {
                            const sizes = [15, 14, 13, 13, 12];
                            const opacities = [1, 0.9, 0.8, 0.7, 0.6];
                            return (
                              <span key={idx} className="ins-chip" style={{
                                fontSize: sizes[Math.min(idx, sizes.length - 1)] ?? 12,
                                opacity: opacities[Math.min(idx, opacities.length - 1)] ?? 0.6,
                              }}>
                                {kw.keyword}
                                {idx < 3 && <span style={{ marginLeft: 6, fontSize: 10, opacity: 0.7, fontWeight: 700 }}>#{idx + 1}</span>}
                              </span>
                            );
                          })
                        : <p style={{ color: 'hsl(210 15% 60%)', fontSize: 14 }}>Use the search bar to build your keyword profile.</p>
                      }
                    </div>
                  </div>
                </div>

                {/* ── Charts Row ────────────────────────────────────────── */}
                <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: 16 }}>

                  {/* Activity Timeline */}
                  <div className="ins-card">
                    <div className="ins-section-title">Activity Timeline</div>
                    <p className="ins-sub" style={{ marginBottom: 20 }}>Search & view trends — last 30 days</p>
                    {(analytics?.activity_timeline ?? []).length > 0 ? (
                      <div style={{ height: 240 }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={analytics.activity_timeline} margin={{ top: 4, right: 4, left: -28, bottom: 0 }}>
                            <defs>
                              <linearGradient id="gSearch" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#10b981" stopOpacity={0.2} />
                                <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                              </linearGradient>
                              <linearGradient id="gView" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#2E6091" stopOpacity={0.2} />
                                <stop offset="100%" stopColor="#2E6091" stopOpacity={0} />
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="hsl(210 20% 90%)" vertical={false} />
                            <XAxis dataKey="date" tick={{ fill: 'hsl(210 15% 50%)', fontSize: 11 }} axisLine={false} tickLine={false} dy={10} />
                            <YAxis tick={{ fill: 'hsl(210 15% 50%)', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} dx={-10} />
                            <Tooltip
                              contentStyle={{ background: '#ffffff', border: '1px solid hsl(210 20% 90%)', borderRadius: 12, boxShadow: '0 4px 12px hsl(210 20% 40%/0.1)' }}
                              labelStyle={{ color: 'hsl(210 25% 15%)', fontWeight: 700, marginBottom: 4 }}
                              itemStyle={{ color: 'hsl(210 20% 40%)', fontWeight: 600 }}
                            />
                            <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 13, color: 'hsl(210 15% 45%)', paddingTop: 10 }} />
                            <Area type="monotone" dataKey="search_count" stroke="#10b981" fill="url(#gSearch)" name="Searches" strokeWidth={3} dot={false} activeDot={{ r: 6, fill: '#10b981', stroke: '#fff', strokeWidth: 2 }} />
                            <Area type="monotone" dataKey="view_count" stroke="#2E6091" fill="url(#gView)" name="Views" strokeWidth={3} dot={false} activeDot={{ r: 6, fill: '#2E6091', stroke: '#fff', strokeWidth: 2 }} />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    ) : (
                      <div style={{ height: 220, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
                        <span style={{ fontSize: 36 }}>📊</span>
                        <p style={{ color: 'hsl(210 15% 45%)', fontSize: 13 }}>Search or browse listings to build your timeline.</p>
                      </div>
                    )}
                  </div>

                  {/* Category Donut */}
                  <div className="ins-card">
                    <div className="ins-section-title">Top Categories</div>
                    <p className="ins-sub" style={{ marginBottom: 16 }}>What you browse most</p>
                    {(analytics?.top_categories ?? []).length > 0 ? (
                      <>
                        <div style={{ height: 180 }}>
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <defs>
                                {['#2E6091', '#10b981', '#8b5cf6', '#f59e0b', '#ef4444'].map((c, i) => (
                                  <radialGradient key={i} id={`pieG${i}`} cx="50%" cy="50%" r="50%">
                                    <stop offset="0%" stopColor={c} stopOpacity={1} />
                                    <stop offset="100%" stopColor={c} stopOpacity={0.8} />
                                  </radialGradient>
                                ))}
                              </defs>
                              <Pie
                                data={analytics.top_categories.slice(0, 5)}
                                dataKey="count" nameKey="category"
                                cx="50%" cy="50%"
                                innerRadius={48} outerRadius={80}
                                paddingAngle={3}
                                stroke="none"
                              >
                                {analytics.top_categories.slice(0, 5).map((_: any, i: number) => (
                                  <Cell key={i} fill={`url(#pieG${i})`} />
                                ))}
                              </Pie>
                              <Tooltip
                                contentStyle={{ background: '#ffffff', border: '1px solid hsl(210 20% 90%)', borderRadius: 12, boxShadow: '0 4px 12px hsl(210 20% 40%/0.1)' }}
                                itemStyle={{ fontWeight: 600 }}
                                formatter={(val: any, name: any) => [val, name]}
                              />
                            </PieChart>
                          </ResponsiveContainer>
                        </div>
                        {/* Legend */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 12 }}>
                          {analytics.top_categories.slice(0, 4).map((cat: any, i: number) => {
                            const colors = ['#2E6091', '#10b981', '#8b5cf6', '#f59e0b'];
                            const total = analytics.top_categories.reduce((a: number, c: any) => a + c.count, 0);
                            const pct = total > 0 ? Math.round((cat.count / total) * 100) : 0;
                            return (
                              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                <div style={{ width: 10, height: 10, borderRadius: '50%', background: colors[i], flexShrink: 0 }} />
                                <span style={{ fontSize: 13, color: 'hsl(210 25% 30%)', flex: 1, textTransform: 'capitalize', fontWeight: 500 }}>{cat.category}</span>
                                <div style={{ width: 70, height: 6, borderRadius: 6, background: 'hsl(210 20% 92%)' }}>
                                  <div style={{ width: `${pct}%`, height: '100%', borderRadius: 6, background: colors[i] }} />
                                </div>
                                <span style={{ fontSize: 12, color: 'hsl(210 15% 45%)', width: 32, textAlign: 'right', fontWeight: 600 }}>{pct}%</span>
                              </div>
                            );
                          })}
                        </div>
                      </>
                    ) : (
                      <div style={{ height: 220, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
                        <span style={{ fontSize: 40 }}>🍩</span>
                        <p style={{ color: 'hsl(210 15% 50%)', fontSize: 14 }}>Browse by category to see your preferences.</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* ── Listing Performance Bar Chart ──────────────────────── */}
                {listings.length > 0 && (
                  <div className="ins-card">
                    <div className="ins-section-title">Your Listing Performance</div>
                    <p className="ins-sub" style={{ marginBottom: 20 }}>Views per listing</p>
                    <div style={{ height: 200 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={listings.slice(0, 8).map(l => ({ name: l.title.slice(0, 14) + (l.title.length > 14 ? '…' : ''), views: l.views || 0 }))}
                          margin={{ top: 4, right: 4, left: -28, bottom: 0 }}
                        >
                          <defs>
                            <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%" stopColor="#4f8bd1" />
                              <stop offset="100%" stopColor="#2E6091" />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="hsl(210 20% 90%)" vertical={false} />
                          <XAxis dataKey="name" tick={{ fill: 'hsl(210 15% 50%)', fontSize: 11 }} axisLine={false} tickLine={false} dy={10} />
                          <YAxis tick={{ fill: 'hsl(210 15% 50%)', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} dx={-10} />
                          <Tooltip
                            contentStyle={{ background: '#ffffff', border: '1px solid hsl(210 20% 90%)', borderRadius: 12, boxShadow: '0 4px 12px hsl(210 20% 40%/0.1)' }}
                            cursor={{ fill: 'hsl(210 20% 96%)' }}
                          />
                          <Bar dataKey="views" fill="url(#barGrad)" radius={[8, 8, 0, 0]} name="Views" maxBarSize={60} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
