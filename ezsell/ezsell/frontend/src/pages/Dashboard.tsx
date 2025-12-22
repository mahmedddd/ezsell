import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { listingService, authService, getImageUrl, favoritesService } from '@/lib/api';
import { useToast } from '@/components/ui/use-toast';
import { Plus, Edit, Trash2, Package, Home, Heart } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function Dashboard() {
  const [user, setUser] = useState<any>(null);
  const [listings, setListings] = useState<any[]>([]);
  const [favorites, setFavorites] = useState<any[]>([]);
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

  const handleRemoveFavorite = async (listingId: number) => {
    try {
      await favoritesService.removeFromFavorites(listingId);
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
        <Button variant="ghost" onClick={() => navigate('/')} className="mb-4 text-[#143109] hover:bg-[#143109]/10">
          <Home className="mr-2 h-4 w-4" />
          Back to Home
        </Button>
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 mb-2">Dashboard</h1>
            <p className="text-slate-600">Welcome back, {user?.username}!</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate('/listings')}>
              Browse Listings
            </Button>
            <Button variant="outline" onClick={handleLogout}>
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
            </TabsList>
            <Button onClick={() => navigate('/create-listing')}>
              <Plus className="mr-2 h-4 w-4" />
              Create Listing
            </Button>
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
                  <div className="aspect-video bg-slate-200 rounded-md mb-4 flex items-center justify-center">
                    {getListingImage(listing) && getImageUrl(getListingImage(listing)!) ? (
                      <img src={getImageUrl(getListingImage(listing)!)!} alt={listing.title} className="w-full h-full object-cover rounded-md" />
                    ) : (
                      <span className="text-slate-500">No image</span>
                    )}
                  </div>
                  <div className="flex justify-between items-start mb-2">
                    <CardTitle className="text-lg">{listing.title}</CardTitle>
                    <div className="flex gap-2">
                      {listing.is_sold && <Badge variant="destructive">Sold</Badge>}
                      {listing.approval_status === 'pending' && <Badge className="bg-yellow-500">Pending Review</Badge>}
                      {listing.approval_status === 'rejected' && <Badge variant="destructive">Rejected</Badge>}
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
                    <Alert className="mb-4 bg-yellow-50 border-yellow-200">
                      <AlertDescription>
                        <strong>Under Review:</strong> Your listing is being reviewed by admin.
                      </AlertDescription>
                    </Alert>
                  )}
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-2xl font-bold text-primary">PKR {listing.price.toLocaleString()}</span>
                    <div className="text-sm text-muted-foreground">{listing.views} views</div>
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
                      <img src={getImageUrl(getListingImage(listing)!)!} alt={listing.title} className="w-full h-full object-cover rounded-md" />
                    ) : (
                      <span className="text-slate-500">No image</span>
                    )}
                    {listing.additional_images && JSON.parse(listing.additional_images).length > 0 && (
                      <Badge className="absolute bottom-2 left-2 bg-black/70 text-white text-xs">
                        📷 {JSON.parse(listing.additional_images).length + 1}
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
                    <span className="text-2xl font-bold text-primary">PKR {listing.price.toLocaleString()}</span>
                    <div className="text-sm text-muted-foreground">{listing.views} views</div>
                  </div>
                  {listing.owner && (
                    <div className="mb-4 pb-4 border-b">
                      <p className="text-xs text-gray-600 font-medium">
                        Posted by {listing.owner.username}
                      </p>
                    </div>
                  )}
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
        </Tabs>
      </div>
    </div>
  );
}
