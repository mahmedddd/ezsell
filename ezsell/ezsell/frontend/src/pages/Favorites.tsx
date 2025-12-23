import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { favoritesService, getImageUrl } from '@/lib/api';
import { Home, Heart, Trash2, ShoppingBag, ArrowLeft, Loader2 } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

interface Listing {
  id: number;
  title: string;
  description: string;
  price: number;
  category: string;
  condition: string;
  images: string;
  image_url?: string;
  views: number;
  created_at: string;
  owner_id: number;
}

export default function Favorites() {
  const [favorites, setFavorites] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(true);
  const [removingId, setRemovingId] = useState<number | null>(null);
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const currentUser = JSON.parse(localStorage.getItem('user') || '{}');

  useEffect(() => {
    // Check if user is logged in
    if (!currentUser?.id) {
      toast({
        title: "Login Required",
        description: "Please login to view your saved listings",
        variant: "destructive",
      });
      navigate('/login');
      return;
    }
    
    fetchFavorites();
  }, []);

  const fetchFavorites = async () => {
    try {
      setLoading(true);
      const data = await favoritesService.getFavorites();
      setFavorites(data);
    } catch (error) {
      console.error('Failed to fetch favorites:', error);
      toast({
        title: "Error",
        description: "Failed to load your saved listings",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveFavorite = async (listingId: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    setRemovingId(listingId);
    try {
      await favoritesService.removeFromFavorites(listingId);
      setFavorites(prev => prev.filter(f => f.id !== listingId));
      toast({
        title: "Removed",
        description: "Listing removed from your saved items",
      });
    } catch (error) {
      console.error('Failed to remove favorite:', error);
      toast({
        title: "Error",
        description: "Failed to remove listing",
        variant: "destructive",
      });
    } finally {
      setRemovingId(null);
    }
  };

  const getListingImage = (listing: Listing) => {
    // Try to get image from images field (JSON array)
    if (listing.images) {
      try {
        const parsedImages = typeof listing.images === 'string' ? JSON.parse(listing.images) : listing.images;
        if (Array.isArray(parsedImages) && parsedImages.length > 0) {
          return getImageUrl(parsedImages[0]);
        }
      } catch (e) {
        console.error('Failed to parse images:', e);
      }
    }
    // Fallback to image_url
    return listing.image_url ? getImageUrl(listing.image_url) : null;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f5f5f0] to-[#e8e8dc]">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <Button 
            variant="ghost" 
            onClick={() => navigate(-1)} 
            className="text-[#143109] hover:bg-[#143109]/10"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <Button 
            variant="ghost" 
            onClick={() => navigate('/')} 
            className="text-[#143109] hover:bg-[#143109]/10"
          >
            <Home className="mr-2 h-4 w-4" />
            Home
          </Button>
        </div>

        {/* Page Title */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-red-100 rounded-lg">
              <Heart className="h-6 w-6 text-red-500 fill-red-500" />
            </div>
            <h1 className="text-3xl font-bold text-slate-900">Saved Listings</h1>
          </div>
          <p className="text-slate-600">
            Your favorite items saved for later. These will be here until you remove them.
          </p>
        </div>

        {/* Loading State */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-16">
            <Loader2 className="h-12 w-12 animate-spin text-[#143109] mb-4" />
            <p className="text-slate-600">Loading your saved listings...</p>
          </div>
        ) : favorites.length === 0 ? (
          /* Empty State */
          <Card className="max-w-md mx-auto">
            <CardContent className="flex flex-col items-center justify-center py-16">
              <div className="p-4 bg-slate-100 rounded-full mb-4">
                <Heart className="h-12 w-12 text-slate-400" />
              </div>
              <h2 className="text-xl font-semibold mb-2">No saved listings yet</h2>
              <p className="text-slate-500 text-center mb-6">
                When you find something you like, tap the heart icon to save it here.
              </p>
              <Button 
                onClick={() => navigate('/listings')}
                className="bg-[#143109] hover:bg-[#1a4a0d]"
              >
                <ShoppingBag className="mr-2 h-4 w-4" />
                Browse Listings
              </Button>
            </CardContent>
          </Card>
        ) : (
          /* Favorites Grid */
          <>
            <div className="mb-4 flex justify-between items-center">
              <p className="text-sm text-slate-600">
                {favorites.length} saved listing{favorites.length !== 1 ? 's' : ''}
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {favorites.map((listing) => (
                <Link key={listing.id} to={`/product/${listing.id}`}>
                  <Card className="group hover:shadow-xl transition-all duration-300 cursor-pointer h-full relative overflow-hidden border-2 border-transparent hover:border-[#143109]/20">
                    {/* Remove Button */}
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="absolute top-3 right-3 z-10 bg-white/90 hover:bg-red-50 rounded-full shadow-md opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={(e) => e.preventDefault()}
                        >
                          {removingId === listing.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4 text-red-500" />
                          )}
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent onClick={(e) => e.stopPropagation()}>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Remove from Saved?</AlertDialogTitle>
                          <AlertDialogDescription>
                            Are you sure you want to remove "{listing.title}" from your saved listings?
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                          <AlertDialogAction
                            className="bg-red-500 hover:bg-red-600"
                            onClick={(e) => handleRemoveFavorite(listing.id, e)}
                          >
                            Remove
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>

                    {/* Saved Badge */}
                    <div className="absolute top-3 left-3 z-10">
                      <Badge className="bg-red-500 text-white">
                        <Heart className="h-3 w-3 mr-1 fill-white" />
                        Saved
                      </Badge>
                    </div>

                    <CardHeader className="pb-2">
                      {/* Image */}
                      <div className="aspect-video bg-slate-200 rounded-lg mb-4 flex items-center justify-center overflow-hidden">
                        {getListingImage(listing) ? (
                          <img 
                            src={getListingImage(listing)!} 
                            alt={listing.title} 
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" 
                          />
                        ) : (
                          <span className="text-slate-400">No image</span>
                        )}
                      </div>
                      
                      {/* Title & Category */}
                      <div className="flex justify-between items-start gap-2 mb-1">
                        <CardTitle className="text-lg line-clamp-1 group-hover:text-[#143109] transition-colors">
                          {listing.title}
                        </CardTitle>
                        <Badge variant="secondary" className="shrink-0 capitalize">
                          {listing.category}
                        </Badge>
                      </div>
                      
                      {/* Description */}
                      <CardDescription className="line-clamp-2 text-sm">
                        {listing.description}
                      </CardDescription>
                    </CardHeader>
                    
                    <CardContent className="pt-0">
                      {/* Price & Condition */}
                      <div className="flex justify-between items-center mb-3">
                        <span className="text-xl font-bold text-[#143109]">
                          PKR {listing.price.toLocaleString()}
                        </span>
                        <Badge variant="outline" className="capitalize">
                          {listing.condition}
                        </Badge>
                      </div>
                      
                      {/* Stats */}
                      <div className="flex justify-between items-center text-xs text-slate-500">
                        <span>{listing.views} views</span>
                        <span>Saved {formatDate(listing.created_at)}</span>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
