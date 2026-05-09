import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { listingService, getImageUrl, favoritesService, arAssetsService, analyticsService, recommendationService, getSessionId } from '../lib/api.ts';
import { Home, MapPin, Eye, MessageCircle, Heart, ChevronLeft, ChevronRight, Share2, ShoppingBag, Star, Clock, AlertCircle } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { ChatWindow } from '@/components/ChatWindow';
import { formatCurrency } from '../lib/utils.ts';
import { SmartImage } from '@/components/ui/SmartImage';
// ── New unified AR entry-point ──────────────────────────────────────────────
import { WebARViewer } from '@/components/ar/WebARViewer';

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [listing, setListing] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showChat, setShowChat] = useState(false);
  const [isFavorited, setIsFavorited] = useState(false);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const [arAssets, setArAssets] = useState<any>(null);
  const [similarListings, setSimilarListings] = useState<any[]>([]);
  const [loadingSimilar, setLoadingSimilar] = useState(false);
  const [showPhone, setShowPhone] = useState(false);
  const [openedViaContact, setOpenedViaContact] = useState(false);
  const { toast } = useToast();

  const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
  const isOwner = currentUser?.id === listing?.owner_id;

  // Get all images (main + additional + new images field)
  const getAllImages = useCallback(() => {
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
  }, [listing]);

  useEffect(() => {
    if (id) {
      fetchListing(parseInt(id));
    }
  }, [id]);

  const fetchListing = async (listingId: number) => {
    try {
      const data = await listingService.getListing(listingId);
      setListing(data);
      // Check if listing is favorited
      if (currentUser?.id) {
        const favoriteStatus = await favoritesService.checkFavorite(listingId);
        setIsFavorited(favoriteStatus.is_favorited);
      }
      // Fetch AR assets for furniture
      if (data.category?.toLowerCase() === 'furniture') {
        const assets = await arAssetsService.getAssets(listingId);
        setArAssets(assets);
      }

      // Fetch similar items
      fetchSimilarListings(listingId);
    } catch (error) {
      console.error('Failed to fetch listing:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSimilarListings = async (listingId: number) => {
    try {
      setLoadingSimilar(true);
      const data = await recommendationService.getSimilar(listingId, 6);
      setSimilarListings(data.recommendations || []);
    } catch (error) {
      console.error('Failed to fetch similar listings:', error);
    } finally {
      setLoadingSimilar(false);
    }
  };

  // Track product view for analytics
  useEffect(() => {
    if (listing && id) {
      const trackView = async () => {
        try {
          await analyticsService.trackActivity({
            activity_type: 'view',
            listing_id: parseInt(id),
            category: listing.category,
            session_id: getSessionId()
          });
        } catch (err) {
          console.error('Failed to track view activity:', err);
        }
      };
      trackView();
    }
  }, [listing?.id, id]);

  const handleShare = async () => {
    if (navigator.share) {
      await navigator.share({ title: listing?.title, url: window.location.href });
    } else {
      navigator.clipboard.writeText(window.location.href);
      toast({ title: 'Link copied!', description: 'Product link copied to clipboard' });
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
        await favoritesService.removeFavorite(listing.id);
        setIsFavorited(false);
        toast({
          title: "Removed",
          description: "Removed from your saved listings",
        });
      } else {
        await favoritesService.addFavorite(listing.id);
        setIsFavorited(true);
        // Track favorite activity
        await analyticsService.trackActivity({
          activity_type: 'favorite',
          listing_id: listing.id,
          category: listing.category
        });
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
    }
  };

  const handleCallAction = async () => {
    if (!currentUser?.id) {
      toast({
        title: "Login Required",
        description: "Please login to view seller contact",
        variant: "destructive",
      });
      return;
    }

    if (!showPhone) {
      try {
        const data = await listingService.trackCall(listing.id);
        if (data.phone) {
          setShowPhone(true);
          setShowChat(true);
          setOpenedViaContact(true); // flag: always show guidelines

          // Track call/message activity
          await analyticsService.trackActivity({
            activity_type: 'message',
            listing_id: listing.id,
            category: listing.category
          });

          toast({
            title: "Seller Notified",
            description: "The seller has been notified that you are interested in calling.",
          });
        }
      } catch (error) {
        console.error('Failed to track call:', error);
        // Fallback to showing phone even if notification fails, to not block the user
        setShowPhone(true);
        setShowChat(true);
        setOpenedViaContact(true); // flag: always show guidelines
      }
    } else {
      window.location.href = `tel:${listing.owner.phone}`;
    }
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#f5f5f0] to-[#e8e8dc] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 rounded-full border-4 border-[#2E6091]/20 border-t-[#2E6091] animate-spin" />
          <p className="text-gray-500 text-sm">Loading…</p>
        </div>
      </div>
    );
  }

  if (!listing) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#f5f5f0] to-[#e8e8dc] flex items-center justify-center">
        <div className="text-center">
          <ShoppingBag className="mx-auto h-12 w-12 text-gray-400 mb-3" />
          <p className="text-gray-600 font-semibold">Listing not found</p>
          <Button onClick={() => navigate('/')} className="mt-4 bg-[#2E6091]">Back to Home</Button>
        </div>
      </div>
    );
  }

  const isFurniture = listing.category?.toLowerCase() === 'furniture';
  const allImages = getAllImages();
  const mainImgUrl = allImages[selectedImageIndex] ? getImageUrl(allImages[selectedImageIndex]) : null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f5f5f0] to-[#e8e8dc] pb-24 md:pb-8">

      {/* ── Mobile sticky top bar ────────────────────────────────────────── */}
      <div className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-gray-100 md:hidden">
        <div className="flex items-center justify-between px-4 py-3">
          <button onClick={() => navigate('/')} className="p-2 rounded-xl bg-gray-100 hover:bg-gray-200 transition-colors">
            <ChevronLeft className="h-5 w-5 text-gray-700" />
          </button>
          <p className="font-semibold text-sm text-gray-900 truncate max-w-[60%]">{listing.title}</p>
          <div className="flex gap-2">
            <button onClick={handleShare} className="p-2 rounded-xl bg-gray-100 hover:bg-gray-200 transition-colors"><Share2 className="h-4 w-4 text-gray-700" /></button>
            <button onClick={handleToggleFavorite} className="p-2 rounded-xl bg-gray-100 hover:bg-gray-200 transition-colors"><Heart className={`h-4 w-4 ${isFavorited ? 'fill-red-500 text-red-500' : 'text-gray-700'}`} /></button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-4 md:py-8 max-w-6xl">

        <div className="grid md:grid-cols-2 gap-6 lg:gap-10">

          {/* ── Left: Image Gallery ─────────────────────────────────────── */}
          <div className="space-y-3">
            <div className="relative aspect-square bg-gray-100 rounded-2xl overflow-hidden shadow-lg">
              {mainImgUrl ? (
                <SmartImage
                  src={mainImgUrl}
                  alt={`${listing.title} – image ${selectedImageIndex + 1}`}
                  className="w-full h-full object-cover"
                  wrapperClassName="w-full h-full"
                  priority="eager"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <ShoppingBag className="h-16 w-16 text-gray-300" />
                </div>
              )}
              {allImages.length > 1 && (
                <>
                  <button onClick={() => setSelectedImageIndex((i) => (i - 1 + allImages.length) % allImages.length)} className="absolute left-3 top-1/2 -translate-y-1/2 p-2 rounded-full bg-white/80 backdrop-blur shadow-md hover:bg-white transition-all"><ChevronLeft className="h-5 w-5 text-gray-800" /></button>
                  <button onClick={() => setSelectedImageIndex((i) => (i + 1) % allImages.length)} className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-full bg-white/80 backdrop-blur shadow-md hover:bg-white transition-all"><ChevronRight className="h-5 w-5 text-gray-800" /></button>
                  <div className="absolute bottom-3 right-3 bg-black/50 text-white text-xs font-medium px-2.5 py-1 rounded-full backdrop-blur">{selectedImageIndex + 1} / {allImages.length}</div>
                </>
              )}
              {listing.is_sold && <div className="absolute top-3 left-3 bg-red-500/90 text-white text-sm font-bold px-3 py-1.5 rounded-xl shadow backdrop-blur">SOLD</div>}
            </div>

            {allImages.length > 1 && (
              <div className="flex gap-2 overflow-x-auto pb-1">
                {allImages.map((img: string, i: number) => (
                  <button key={i} onClick={() => setSelectedImageIndex(i)}
                    className={`flex-shrink-0 w-16 h-16 md:w-20 md:h-20 rounded-xl overflow-hidden border-2 transition-all ${i === selectedImageIndex ? 'border-[#2E6091] ring-2 ring-[#2E6091]/20 scale-105' : 'border-transparent opacity-70 hover:opacity-100 hover:border-gray-300'}`}>
                    <SmartImage
                      src={getImageUrl(img)!}
                      alt={`Thumb ${i + 1}`}
                      className="w-full h-full object-cover"
                      wrapperClassName="w-full h-full"
                      priority="lazy"
                    />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* ── Right: Details Panel ────────────────────────────────────── */}
          <div className="space-y-4">

            <Card className="border-0 shadow-md rounded-2xl overflow-hidden">
              <CardHeader className="pb-3">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-2xl md:text-3xl leading-tight">{listing.title}</CardTitle>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      <Badge className="bg-[#2E6091]/10 text-[#2E6091] border-0">{listing.category}</Badge>
                      <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
                        {listing.condition}/10 - {getConditionLabel(listing.condition)}
                      </Badge>
                      {listing.is_sold && <Badge variant="destructive">Sold</Badge>}
                    </div>
                  </div>
                  <div className="text-3xl md:text-4xl font-black tracking-tighter text-slate-900 break-words overflow-hidden max-w-full">
                    {formatCurrency(listing.price)}
                  </div>
                </div>
                <CardDescription className="text-sm leading-relaxed mt-2 text-gray-600">{listing.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 pt-0">
                {listing.location && <div className="flex items-center text-sm text-gray-500 gap-2"><MapPin className="h-4 w-4 text-[#2E6091] shrink-0" />{listing.location}</div>}
                <div className="flex items-center text-sm text-gray-500 gap-2"><Eye className="h-4 w-4 text-[#2E6091] shrink-0" />{listing.views} views</div>
                <div className="p-3 bg-gray-50 rounded-xl flex items-center gap-3 mt-2">
                  <div className="w-9 h-9 rounded-full bg-[#2E6091]/10 flex items-center justify-center shrink-0">
                    <span className="text-[#2E6091] font-bold text-sm">{(listing.owner?.username || 'U')[0].toUpperCase()}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-900 truncate">{listing.owner?.username || 'User'}{listing.owner?.full_name && ` · ${listing.owner.full_name}`}</p>
                    <p className="text-xs text-gray-400">Listed {new Date(listing.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}</p>
                    {(() => {
                      const createdDate = new Date(listing.created_at);
                      const expiryDate = new Date(createdDate.getTime() + 30 * 24 * 60 * 60 * 1000);
                      const now = new Date();
                      const diffTime = expiryDate.getTime() - now.getTime();
                      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

                      if (diffDays <= 0) {
                        return (
                          <div className="flex items-center text-red-500 text-[10px] font-medium mt-1">
                            <AlertCircle className="w-3 h-3 mr-1" />
                            <span>Ad Expired</span>
                          </div>
                        );
                      }
                      return (
                        <div className="flex items-center text-amber-600 text-[10px] font-medium mt-1">
                          <Clock className="w-3 h-3 mr-1" />
                          <span>{diffDays} days remaining</span>
                        </div>
                      );
                    })()}
                  </div>
                  <Star className="h-4 w-4 text-amber-400 shrink-0" />
                </div>

                {listing.owner?.phone && (
                  <div className="mt-4 p-4 bg-green-50 rounded-2xl border border-green-100 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-white rounded-xl shadow-sm">
                        <svg className="w-5 h-5 text-[#2E6091]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h2.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-[10px] uppercase tracking-wider font-bold text-green-700">Seller Phone</p>
                        <p className="text-lg font-bold text-[#2E6091]">
                          {showPhone || isOwner ? listing.owner.phone : `${listing.owner.phone.substring(0, 4)}XXXXXXX`}
                        </p>
                      </div>
                    </div>
                    <Button
                      size="sm"
                      className="bg-[#2E6091] hover:bg-[#1E4166] text-white rounded-lg h-9 px-4"
                      onClick={handleCallAction}
                    >
                      {showPhone || isOwner ? 'Call Now' : 'Show Contact'}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* ── WebAR Section ─────────────────────────────────────────── */}
            {isFurniture && (
              <WebARViewer
                listingId={listing.id}
                listingTitle={listing.title}
                listingDescription={listing.description}
                category={listing.category}
                price={listing.price}
                furnitureType={listing.furniture_type}
                furnitureSubtype={listing.furniture_subtype}
                furnitureMaterial={listing.material}
                furnitureImageUrl={allImages[0] ? getImageUrl(allImages[0]) : null}
                allImageUrls={allImages.map((img: string) => getImageUrl(img)).filter((u: string | null): u is string => !!u)}
                arAssets={arAssets}
                dimensionsCm={arAssets?.dimensions_cm ?? null}
                onModelGenerated={() => fetchListing(listing.id)}
              />
            )}

            {/* ── Action buttons ────────────────────────────────────────── */}
            <Card className="border-0 shadow-md rounded-2xl overflow-hidden">
              <CardContent className="pt-4 pb-4 space-y-3">
                {isOwner ? (
                  <Button className="w-full bg-[#2E6091] hover:bg-[#1E4166] text-white rounded-xl py-5 text-base font-semibold" onClick={() => navigate(`/edit-listing/${listing.id}`)}>
                    <MessageCircle className="mr-2 h-5 w-5" />Edit Listing
                  </Button>
                ) : (
                  <Button className="w-full bg-[#2E6091] hover:bg-[#1E4166] text-white rounded-xl py-5 text-base font-semibold" disabled={listing.is_sold} onClick={() => setShowChat(true)}>
                    <MessageCircle className="mr-2 h-5 w-5" />{listing.is_sold ? 'Sold Out' : 'Chat with Seller'}
                  </Button>
                )}
                <div className="hidden md:flex gap-3">
                  <Button variant="outline" className={`flex-1 rounded-xl py-5 ${isFavorited ? 'bg-red-50 border-red-200 text-red-600' : ''}`} onClick={handleToggleFavorite}>
                    <Heart className={`mr-2 h-5 w-5 ${isFavorited ? 'fill-current' : ''}`} />{isFavorited ? 'Saved' : 'Save'}
                  </Button>
                  <Button variant="outline" className="flex-1 rounded-xl py-5" onClick={handleShare}>
                    <Share2 className="mr-2 h-5 w-5" />Share
                  </Button>
                </div>
              </CardContent>
            </Card>

            {(listing.brand || listing.material || listing.furniture_type || arAssets?.dimensions_cm) && (
              <Card className="border-0 shadow-md rounded-2xl overflow-hidden">
                <CardHeader className="pb-2"><CardTitle className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Details</CardTitle></CardHeader>
                <CardContent className="pt-0 grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                  <span className="text-gray-500">Condition</span><span className="font-medium">{listing.condition}/10 - {getConditionLabel(listing.condition)}</span>
                  {(listing.furniture_brand || listing.brand) && <><span className="text-gray-500">Brand</span><span className="font-medium">{listing.furniture_brand || listing.brand}</span></>}
                  {listing.furniture_type && <><span className="text-gray-500">Type</span><span className="font-medium capitalize">{listing.furniture_type.replace('_', ' ')}</span></>}
                  {listing.material && <><span className="text-gray-500">Material</span><span className="font-medium capitalize">{listing.material.replace('_', ' ')}</span></>}
                  {listing.is_sliding_door && <><span className="text-gray-500">Doors</span><span className="font-medium">Sliding Mechanism</span></>}
                  {listing.has_mattress && (
                    <>
                      <span className="text-gray-500">Mattress</span>
                      <span className="font-medium">Included ({listing.mattress_type?.replace('_', ' ') || 'Standard'})</span>
                    </>
                  )}
                  {arAssets?.dimensions_cm && <><span className="text-gray-500">Dimensions</span><span className="font-medium">{arAssets.dimensions_cm.w} × {arAssets.dimensions_cm.l} × {arAssets.dimensions_cm.h} cm</span></>}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>

      {/* Mobile fixed bottom CTA */}
      <div className="fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-t border-gray-100 px-4 py-3 md:hidden">
        <div className="flex gap-3 max-w-lg mx-auto">
          <button onClick={handleToggleFavorite} className={`flex-shrink-0 p-3 rounded-2xl border-2 transition-all ${isFavorited ? 'bg-red-50 border-red-200 text-red-500' : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'}`}>
            <Heart className={`h-5 w-5 ${isFavorited ? 'fill-current' : ''}`} />
          </button>
          {isOwner ? (
            <button onClick={() => navigate(`/edit-listing/${listing.id}`)} className="flex-1 flex items-center justify-center gap-2 bg-[#2E6091] hover:bg-[#1E4166] active:scale-[0.98] text-white font-bold text-sm py-3 rounded-2xl transition-all shadow-lg shadow-[#2E6091]/20">
              <MessageCircle className="h-5 w-5" />Edit Listing
            </button>
          ) : (
            <button disabled={listing.is_sold} onClick={() => setShowChat(true)} className="flex-1 flex items-center justify-center gap-2 bg-[#2E6091] hover:bg-[#1E4166] active:scale-[0.98] disabled:opacity-60 text-white font-bold text-sm py-3 rounded-2xl transition-all shadow-lg shadow-[#2E6091]/20">
              <MessageCircle className="h-5 w-5" />{listing.is_sold ? 'Sold Out' : 'Chat with Seller'}
            </button>
          )}
        </div>
      </div>

      {/* ── Similar Items Section ────────────────────────────────────────── */}
      {similarListings.length > 0 && (
        <div className="container mx-auto px-4 py-12 max-w-6xl">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-[#2E6091]">Similar Items You Might Like</h2>
            <Link to="/" className="text-sm font-semibold text-[#2E6091] hover:underline">Explore More</Link>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {similarListings.map((rec: any, idx: number) => {
              const item = rec.listing_details;
              if (!item) return null;
              const img = item.images ? (typeof item.images === 'string' ? JSON.parse(item.images)[0] : item.images[0]) : null;

              return (
                <Link key={`${rec.listing_id}-${idx}`} to={`/product/${rec.listing_id}`} className="group">
                  <Card className="border-0 shadow-sm rounded-xl overflow-hidden hover:shadow-md transition-all h-full">
                    <div className="aspect-square relative overflow-hidden bg-gray-100">
                      {img ? (
                        <img src={getImageUrl(img)!} alt={item.title} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-2xl">📦</div>
                      )}
                      <div className="absolute top-2 left-2 flex flex-col gap-1">
                        <Badge className="bg-white/90 text-black text-[10px] font-bold px-1.5 py-0 border-0 shadow-sm w-fit">{rec.score > 0.8 ? 'Best Match' : rec.recommendation_type}</Badge>
                        {item.location && (
                          <Badge className="bg-[#2E6091]/90 text-white text-[9px] font-bold px-1.5 py-0 border-0 shadow-sm w-fit">
                            📍 {item.location.split(',')[0]}
                          </Badge>
                        )}
                      </div>
                    </div>
                    <CardContent className="p-2.5">
                      <p className="text-xs font-bold text-[#2E6091] mb-1">PKR {item.price?.toLocaleString()}</p>
                      <h3 className="text-[11px] font-medium text-gray-700 line-clamp-2 leading-tight group-hover:text-[#2E6091]">{item.title}</h3>
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>
        </div>
      )}

      {/* Chat Window */}
      {showChat && !isOwner && currentUser?.id && (
        <ChatWindow
          listingId={listing.id}
          listingTitle={listing.title}
          sellerId={listing.owner_id}
          sellerName={listing.owner?.username || 'Seller'}
          currentUserId={currentUser.id}
          onClose={() => { setShowChat(false); setOpenedViaContact(false); }}
          listingImage={allImages && allImages.length > 0 ? allImages[0] : undefined}
          listingPrice={listing.price}
          forceShowGuidelines={openedViaContact}
          sellerAvatar={listing.owner?.avatar_url}
        />
      )}
    </div>
  );
}
