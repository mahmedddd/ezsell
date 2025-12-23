import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { listingService, getImageUrl, favoritesService } from '@/lib/api';
import { Home, MapPin, Eye, MessageCircle, Heart } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { ChatWindow } from '@/components/ChatWindow';
import { ARViewer } from '@/components/ARViewer';
import { AR3DViewer } from '@/components/AR3DViewer';
import { RealisticARViewer } from '@/components/RealisticARViewer';
import { Advanced3DARViewer } from '@/components/Advanced3DARViewer';

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [listing, setListing] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showChat, setShowChat] = useState(false);
  const [isFavorited, setIsFavorited] = useState(false);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const { toast } = useToast();
  
  const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
  const isOwner = currentUser?.id === listing?.owner_id;
  
  // Get all images (main + additional + new images field)
  const getAllImages = () => {
    const images: string[] = [];
    
    // Check for new 'images' field (JSON array)
    if (listing?.images) {
      try {
        const parsedImages = typeof listing.images === 'string' ? JSON.parse(listing.images) : listing.images;
        if (Array.isArray(parsedImages)) {
          images.push(...parsedImages);
        }
      } catch (e) {
        console.error('Failed to parse images field:', e);
      }
    }
    
    // Fallback to old fields for backwards compatibility
    if (images.length === 0) {
      if (listing?.image_url) {
        images.push(listing.image_url);
      }
      if (listing?.additional_images) {
        try {
          const additionalImages = JSON.parse(listing.additional_images);
          images.push(...additionalImages);
        } catch (e) {
          console.error('Failed to parse additional images');
        }
      }
    }
    
    return images;
  };

  useEffect(() => {
    if (id) {
      fetchListing(parseInt(id));
    }
  }, [id]);

  const fetchListing = async (listingId: number) => {
    try {
      const data = await listingService.getListingById(listingId);
      setListing(data);
      // Check if listing is favorited
      if (currentUser?.id) {
        const favoriteStatus = await favoritesService.checkFavorite(listingId);
        setIsFavorited(favoriteStatus.is_favorited);
      }
    } catch (error) {
      console.error('Failed to fetch listing:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleFavorite = async () => {
    if (!currentUser?.id) {
      toast({
        title: "Login Required",
        description: "Please login to save listings",
        variant: "destructive",
      });
      return;
    }

    try {
      if (isFavorited) {
        await favoritesService.removeFromFavorites(listing.id);
        setIsFavorited(false);
        toast({
          title: "Removed from favorites",
          description: "Listing removed from your saved items",
        });
      } else {
        await favoritesService.addToFavorites(listing.id);
        setIsFavorited(true);
        toast({
          title: "Added to favorites",
          description: "Listing saved successfully",
        });
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
      toast({
        title: "Error",
        description: "Failed to update favorites",
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#f5f5f0] to-[#e8e8dc] flex items-center justify-center">
        <div className="text-slate-900 text-xl font-semibold">Loading...</div>
      </div>
    );
  }

  if (!listing) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#f5f5f0] to-[#e8e8dc] flex items-center justify-center">
        <div className="text-slate-900 text-xl font-semibold">Listing not found</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f5f5f0] to-[#e8e8dc]">
      <div className="container mx-auto px-4 py-8">
        <Button variant="ghost" onClick={() => navigate('/')} className="mb-6 text-[#143109] hover:bg-[#143109]/10">
          <Home className="mr-2 h-4 w-4" />
          Back to Home
        </Button>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Image Section */}
          <div>
            <Card>
              <CardContent className="p-0">
                {/* Main Image Display */}
                <div className="aspect-square bg-slate-200 rounded-t-lg flex items-center justify-center overflow-hidden">
                  {getAllImages().length > 0 && getAllImages()[selectedImageIndex] ? (
                    <img 
                      src={getImageUrl(getAllImages()[selectedImageIndex])!} 
                      alt={`${listing.title} - Image ${selectedImageIndex + 1}`} 
                      className="w-full h-full object-cover" 
                    />
                  ) : (
                    <span className="text-slate-500 text-xl">No image available</span>
                  )}
                </div>
                
                {/* Thumbnail Gallery */}
                {getAllImages().length > 1 && (
                  <div className="p-4 bg-white rounded-b-lg">
                    <div className="flex gap-2 overflow-x-auto">
                      {getAllImages().map((img, index) => (
                        <button
                          key={index}
                          onClick={() => setSelectedImageIndex(index)}
                          className={`flex-shrink-0 w-20 h-20 rounded-md overflow-hidden border-2 transition-all ${
                            selectedImageIndex === index 
                              ? 'border-[#143109] ring-2 ring-[#143109]/20' 
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <img 
                            src={getImageUrl(img)!} 
                            alt={`Thumbnail ${index + 1}`}
                            className="w-full h-full object-cover"
                          />
                        </button>
                      ))}
                    </div>
                    <p className="text-xs text-gray-500 mt-2 text-center">
                      {selectedImageIndex + 1} / {getAllImages().length}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Details Section */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-3xl mb-2">{listing.title}</CardTitle>
                    <div className="flex gap-2 mb-4">
                      <Badge>{listing.category}</Badge>
                      <Badge variant="outline">{listing.condition}</Badge>
                      {listing.is_sold && <Badge variant="destructive">Sold</Badge>}
                    </div>
                  </div>
                  <div className="text-4xl font-bold text-primary">PKR {listing.price.toLocaleString()}</div>
                </div>
                
                <CardDescription className="text-base">{listing.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {listing.location && (
                  <div className="flex items-center text-muted-foreground">
                    <MapPin className="h-4 w-4 mr-2" />
                    {listing.location}
                  </div>
                )}
                
                <div className="flex items-center text-muted-foreground">
                  <Eye className="h-4 w-4 mr-2" />
                  {listing.views} views
                </div>

                <div className="pt-4 border-t">
                  <p className="text-sm font-semibold text-gray-700">Posted by</p>
                  <p className="text-base font-medium text-[#143109]">
                    {listing.owner?.username || 'User'}
                    {listing.owner?.full_name && ` (${listing.owner.full_name})`}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {new Date(listing.created_at).toLocaleDateString('en-US', { 
                      weekday: 'long',
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric' 
                    })}
                  </p>
                </div>

                <div className="text-sm text-muted-foreground">
                  Listed on {new Date(listing.created_at).toLocaleDateString()}
                </div>

                <div className="pt-4 space-y-2">
                  {isOwner && (
                    <Button 
                      className="w-full bg-[#143109] hover:bg-[#AAAE7F]" 
                      size="lg"
                      onClick={() => navigate(`/edit-listing/${listing.id}`)}
                    >
                      <MessageCircle className="mr-2 h-5 w-5" />
                      Edit Listing
                    </Button>
                  )}
                  
                  {!isOwner && (
                    <Button 
                      className="w-full bg-[#143109] hover:bg-[#AAAE7F]" 
                      size="lg" 
                      disabled={listing.is_sold}
                      onClick={() => setShowChat(true)}
                    >
                      <MessageCircle className="mr-2 h-5 w-5" />
                      {listing.is_sold ? 'Sold Out' : 'Chat with Seller'}
                    </Button>
                  )}
                  
                  {/* AR Viewers - Only for furniture */}
                  <div className="space-y-2">
                    <Advanced3DARViewer 
                      listingId={listing.id}
                      listingTitle={listing.title}
                      category={listing.category}
                      price={listing.price}
                      furnitureImageUrl={getAllImages()[0] ? getImageUrl(getAllImages()[0]) : undefined}
                    />
                    <RealisticARViewer 
                      listingId={listing.id}
                      listingTitle={listing.title}
                      category={listing.category}
                      price={listing.price}
                    />
                    <div className="grid grid-cols-2 gap-2">
                      <ARViewer 
                        listingId={listing.id}
                        listingTitle={listing.title}
                        category={listing.category}
                      />
                      <AR3DViewer 
                        listingId={listing.id}
                        listingTitle={listing.title}
                        category={listing.category}
                      />
                    </div>
                  </div>
                  
                  <Button 
                    variant="outline" 
                    className={`w-full ${isFavorited ? 'bg-red-50 border-red-300 text-red-600 hover:bg-red-100' : ''}`}
                    size="lg"
                    onClick={handleToggleFavorite}
                  >
                    <Heart className={`mr-2 h-5 w-5 ${isFavorited ? 'fill-current' : ''}`} />
                    {isFavorited ? 'Saved' : 'Save for Later'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
      
      {/* Chat Window */}
      {showChat && !isOwner && currentUser?.id && (
        <ChatWindow
          listingId={listing.id}
          listingTitle={listing.title}
          sellerId={listing.owner_id}
          sellerName={listing.owner?.username || 'Seller'}
          currentUserId={currentUser.id}
          onClose={() => setShowChat(false)}
        />
      )}
    </div>
  );
}
