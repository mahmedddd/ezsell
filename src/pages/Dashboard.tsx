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
                            wrapperClassName="w-full h-full"
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
                            wrapperClassName="w-full h-full"
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

          {/* Insights Tab */}
          <TabsContent value="insights">
            {analyticsLoading ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#2E6091] mb-4" />
                  <p className="text-muted-foreground">Loading your insights...</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-6">
                {/* Summary Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[
                    { label: 'Searches', value: analytics?.total_searches ?? 0, color: 'text-blue-600' },
                    { label: 'Listing Views', value: analytics?.total_views ?? 0, color: 'text-green-600' },
                    { label: 'Favorites', value: analytics?.total_favorites ?? 0, color: 'text-red-500' },
                    { label: 'Messages Sent', value: analytics?.total_messages ?? 0, color: 'text-purple-600' },
                  ].map(stat => (
                    <Card key={stat.label}>
                      <CardContent className="pt-6">
                        <div className={`text-3xl font-bold ${stat.color}`}>{stat.value}</div>
                        <div className="text-sm text-muted-foreground mt-1">{stat.label}</div>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {/* Engagement Score */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <Card className="border-t-4 border-t-primary">
                    <CardHeader>
                      <CardTitle>Engagement Score</CardTitle>
                      <CardDescription>How active you are on EZSell</CardDescription>
                    </CardHeader>
                    <CardContent className="flex items-center justify-center py-6">
                      <div className="text-5xl font-extrabold text-[#2E6091]">
                        {analytics?.engagement_score ?? 0}
                        <span className="text-xl text-muted-foreground font-normal">/100</span>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="col-span-2 border-t-4 border-t-purple-500">
                    <CardHeader>
                      <CardTitle>Top Keywords</CardTitle>
                      <CardDescription>Extracted from your search history</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap gap-2">
                        {(analytics?.top_keywords ?? []).length > 0
                          ? analytics.top_keywords.map((kw: any, idx: number) => (
                            <Badge key={idx} variant="secondary" className="px-3 py-1 text-sm bg-purple-50 text-purple-700 hover:bg-purple-100">
                              {kw.keyword}
                            </Badge>
                          ))
                          : <p className="text-sm text-muted-foreground">Use the search bar to start building your keyword profile.</p>
                        }
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Charts */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Activity Timeline */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Activity Timeline</CardTitle>
                      <CardDescription>Your search & view trends over the last 30 days</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {(analytics?.activity_timeline ?? []).length > 0 ? (
                        <div className="h-64 w-full">
                          <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={analytics.activity_timeline} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                              <defs>
                                <linearGradient id="colorSearch" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#82ca9d" stopOpacity={0.8} />
                                  <stop offset="95%" stopColor="#82ca9d" stopOpacity={0.1} />
                                </linearGradient>
                                <linearGradient id="colorView" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8} />
                                  <stop offset="95%" stopColor="#8884d8" stopOpacity={0.1} />
                                </linearGradient>
                              </defs>
                              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                              <Tooltip />
                              <Legend />
                              <Area type="monotone" dataKey="search_count" stroke="#82ca9d" fill="url(#colorSearch)" name="Searches" strokeWidth={2} />
                              <Area type="monotone" dataKey="view_count" stroke="#8884d8" fill="url(#colorView)" name="Views" strokeWidth={2} />
                            </AreaChart>
                          </ResponsiveContainer>
                        </div>
                      ) : (
                        <div className="h-64 flex flex-col items-center justify-center text-muted-foreground">
                          <BarChart3 className="h-10 w-10 mb-3 opacity-40" />
                          <p className="text-sm">Search or browse listings to build your activity timeline.</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* Top Categories Pie */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Top Categories</CardTitle>
                      <CardDescription>Categories you search & browse most</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {(analytics?.top_categories ?? []).length > 0 ? (
                        <div className="h-64 w-full">
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie
                                data={analytics.top_categories.slice(0, 5)}
                                dataKey="count"
                                nameKey="category"
                                cx="50%"
                                cy="50%"
                                outerRadius={90}
                                label={({ category, percent }: any) => `${category} ${(percent * 100).toFixed(0)}%`}
                                labelLine={false}
                              >
                                {analytics.top_categories.slice(0, 5).map((_: any, i: number) => (
                                  <Cell key={i} fill={['#2E6091', '#82ca9d', '#8884d8', '#ffc658', '#ff7f7f'][i % 5]} />
                                ))}
                              </Pie>
                              <Tooltip formatter={(val: any, name: any) => [val, name]} />
                            </PieChart>
                          </ResponsiveContainer>
                        </div>
                      ) : (
                        <div className="h-64 flex flex-col items-center justify-center text-muted-foreground">
                          <BarChart3 className="h-10 w-10 mb-3 opacity-40" />
                          <p className="text-sm">Browse listings by category to see your preferences here.</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
