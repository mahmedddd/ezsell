import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { listingService, authService, getImageUrl, predictionService, favoritesService } from '@/lib/api';
import { useToast } from '@/components/ui/use-toast';
import { Plus, Edit, Trash2, Package, Upload, X, Sparkles, Loader2, Home, Heart } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function Dashboard() {
  const [user, setUser] = useState<any>(null);
  const [listings, setListings] = useState<any[]>([]);
  const [favorites, setFavorites] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('listings');
  const navigate = useNavigate();
  const { toast } = useToast();

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    price: '',
    category: '',
    condition: '',
    location: '',
    brand: '',
    model: '',
    furniture_type: '',
    material: '',
  });
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);
  const [predictedPrice, setPredictedPrice] = useState<any>(null);
  const [predicting, setPredicting] = useState(false);

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

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    
    if (files.length + imageFiles.length > 5) {
      toast({ title: 'Error', description: 'Maximum 5 images allowed', variant: 'destructive' });
      return;
    }
    
    const validFiles: File[] = [];
    const newPreviews: string[] = [];
    
    for (const file of files) {
      if (!['image/jpeg', 'image/jpg', 'image/png'].includes(file.type)) {
        toast({ title: 'Error', description: 'Please upload only JPG or PNG images', variant: 'destructive' });
        continue;
      }
      if (file.size > 5 * 1024 * 1024) {
        toast({ title: 'Error', description: 'Each image must be less than 5MB', variant: 'destructive' });
        continue;
      }
      validFiles.push(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        newPreviews.push(reader.result as string);
        if (newPreviews.length === validFiles.length) {
          setImagePreviews([...imagePreviews, ...newPreviews]);
        }
      };
      reader.readAsDataURL(file);
    }
    
    setImageFiles([...imageFiles, ...validFiles]);
  };

  const removeImage = (index: number) => {
    setImageFiles(imageFiles.filter((_, i) => i !== index));
    setImagePreviews(imagePreviews.filter((_, i) => i !== index));
  };

  const handlePredictPrice = async () => {
    if (!formData.category || !formData.title || !formData.condition) {
      toast({
        title: 'Missing Information',
        description: 'Please fill in category, title, and condition first',
        variant: 'destructive'
      });
      return;
    }

    setPredicting(true);
    try {
      const features: any = {
        title: formData.title,
        condition: formData.condition,
        description: formData.description
      };

      if (formData.category === 'mobile' && formData.brand) {
        features.brand = formData.brand;
      } else if (formData.category === 'laptop') {
        features.brand = formData.brand;
        features.model = formData.model;
      } else if (formData.category === 'furniture') {
        features.type = formData.furniture_type;
        features.material = formData.material;
      }

      const result = await predictionService.predictPrice({
        category: formData.category,
        features
      });

      setPredictedPrice(result);
      setFormData({ ...formData, price: result.predicted_price.toString() });
      
      toast({
        title: 'Price Predicted!',
        description: `Suggested price: PKR ${result.predicted_price.toLocaleString()} (${Math.round(result.confidence_score * 100)}% confidence)`,
      });
    } catch (error: any) {
      toast({
        title: 'Prediction Failed',
        description: error.response?.data?.detail || 'Could not predict price. Please enter manually.',
        variant: 'destructive'
      });
    } finally {
      setPredicting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate required fields
    if (!formData.title.trim()) {
      toast({ title: 'Error', description: 'Title is required', variant: 'destructive' });
      return;
    }
    if (!formData.condition) {
      toast({ title: 'Error', description: 'Condition is required', variant: 'destructive' });
      return;
    }
    if (!formData.model.trim()) {
      toast({ title: 'Error', description: 'Model is required. Please specify the product model/brand.', variant: 'destructive' });
      return;
    }
    
    try {
      const listingData: any = {
        ...formData,
        price: parseFloat(formData.price),
        images: imageFiles,
        predicted_price: predictedPrice?.predicted_price || undefined,
      };

      const response = await listingService.createListing(listingData);
      
      // Check the response approval status
      if (response.approval_status === 'pending') {
        toast({
          title: 'Listing Submitted for Review',
          description: 'Your listing price differs significantly from the AI prediction and has been sent to admin for approval. You will receive a message once it is reviewed.',
          duration: 7000,
        });
      } else {
        toast({
          title: 'Success!',
          description: 'Listing created successfully and is now live!',
        });
      }
      
      setIsCreateOpen(false);
      setFormData({
        title: '',
        description: '',
        price: '',
        category: '',
        condition: '',
        location: '',
        brand: '',
        model: '',
        furniture_type: '',
        material: '',
      });
      setImageFiles([]);
      setImagePreviews([]);
      fetchMyListings();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to create listing',
        variant: 'destructive',
      });
    }
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
            <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create Listing
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create New Listing</DialogTitle>
                <DialogDescription>
                  Add a new product to your listings
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Step 1: Basic Details */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                  <h3 className="font-semibold text-blue-900 mb-2">📝 Step 1: Enter Product Details</h3>
                  <p className="text-sm text-blue-700">Fill in the details below to get an AI price prediction</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="category">Category *</Label>
                    <Select
                      value={formData.category}
                      onValueChange={(value) => setFormData({ ...formData, category: value })}
                      required
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="mobile">Mobile</SelectItem>
                        <SelectItem value="laptop">Laptop</SelectItem>
                        <SelectItem value="furniture">Furniture</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="condition">Condition *</Label>
                    <Select
                      value={formData.condition}
                      onValueChange={(value) => setFormData({ ...formData, condition: value })}
                      required
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select condition" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="new">New</SelectItem>
                        <SelectItem value="like-new">Like New</SelectItem>
                        <SelectItem value="good">Good</SelectItem>
                        <SelectItem value="fair">Fair</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="title">Title * (Include brand, model, specs)</Label>
                  <Input
                    id="title"
                    name="title"
                    value={formData.title}
                    onChange={handleChange}
                    placeholder="e.g., iPhone 14 Pro Max 256GB, Dell XPS 15, Wooden Dining Table"
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="description">Description *</Label>
                  <Textarea
                    id="description"
                    name="description"
                    value={formData.description}
                    onChange={handleChange}
                    placeholder="Add detailed description including features, condition, age..."
                    required
                    rows={4}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="location">Location</Label>
                  <Input
                    id="location"
                    name="location"
                    value={formData.location}
                    onChange={handleChange}
                    placeholder="City, Area"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label>Product Images (Max 5 - JPG or PNG)</Label>
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 hover:border-[#143109] transition-colors">
                    {imagePreviews.length > 0 ? (
                      <div className="space-y-3">
                        <div className="grid grid-cols-3 gap-3">
                          {imagePreviews.map((preview, index) => (
                            <div key={index} className="relative">
                              <img
                                src={preview}
                                alt={`Preview ${index + 1}`}
                                className="w-full h-32 rounded-lg object-cover"
                              />
                              <Button
                                type="button"
                                variant="destructive"
                                size="sm"
                                className="absolute top-1 right-1 h-6 w-6 p-0"
                                onClick={() => removeImage(index)}
                              >
                                <X className="h-4 w-4" />
                              </Button>
                            </div>
                          ))}
                        </div>
                        {imagePreviews.length < 5 && (
                          <label className="cursor-pointer block text-center py-2 border-2 border-dashed border-gray-300 rounded-lg hover:border-[#143109]">
                            <input
                              type="file"
                              accept=".jpg,.jpeg,.png"
                              onChange={handleImageChange}
                              className="hidden"
                              multiple
                            />
                            <Upload className="h-6 w-6 mx-auto text-gray-400 mb-1" />
                            <p className="text-xs text-gray-600">Add more ({5 - imagePreviews.length} remaining)</p>
                          </label>
                        )}
                      </div>
                    ) : (
                      <label className="cursor-pointer block text-center">
                        <input
                          type="file"
                          accept=".jpg,.jpeg,.png"
                          onChange={handleImageChange}
                          className="hidden"
                          multiple
                        />
                        <Upload className="h-8 w-8 mx-auto text-gray-400 mb-2" />
                        <p className="text-sm text-gray-600">
                          Click to upload up to 5 images
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          JPG, PNG - Max 5MB each
                        </p>
                      </label>
                    )}
                  </div>
                </div>

                {/* Category-specific fields */}
                {formData.category === 'mobile' && (
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="brand">Brand</Label>
                      <Input
                        id="brand"
                        name="brand"
                        value={formData.brand}
                        onChange={handleChange}
                        placeholder="e.g., Apple, Samsung"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="model">Model <span className="text-red-500">*</span></Label>
                      <Input
                        id="model"
                        name="model"
                        value={formData.model}
                        onChange={handleChange}
                        placeholder="e.g., iPhone 14 Pro, Galaxy S23"
                        required
                      />
                    </div>
                  </>
                )}

                {formData.category === 'laptop' && (
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="brand">Brand</Label>
                      <Input
                        id="brand"
                        name="brand"
                        value={formData.brand}
                        onChange={handleChange}
                        placeholder="e.g., HP, Dell, Lenovo"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="model">Model <span className="text-red-500">*</span></Label>
                      <Input
                        id="model"
                        name="model"
                        value={formData.model}
                        onChange={handleChange}
                        placeholder="e.g., MacBook Pro M1, ThinkPad X1"
                        required
                      />
                    </div>
                  </>
                )}

                {formData.category === 'furniture' && (
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="furniture_type">Type</Label>
                      <Input
                        id="furniture_type"
                        name="furniture_type"
                        value={formData.furniture_type}
                        onChange={handleChange}
                        placeholder="e.g., Sofa, Table"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="model">Model/Style <span className="text-red-500">*</span></Label>
                      <Input
                        id="model"
                        name="model"
                        value={formData.model}
                        onChange={handleChange}
                        placeholder="e.g., Modern L-Shape, Classic Oak"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="material">Material</Label>
                      <Input
                        id="material"
                        name="material"
                        value={formData.material}
                        onChange={handleChange}
                        placeholder="e.g., Wood, Metal"
                      />
                    </div>
                  </>
                )}

                {/* Step 2: Get AI Price Prediction */}
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mt-4">
                  <h3 className="font-semibold text-purple-900 mb-2">🤖 Step 2: Get AI Price Prediction</h3>
                  <p className="text-sm text-purple-700 mb-3">Click below to get an intelligent price suggestion based on your product details</p>
                  <Button
                    type="button"
                    onClick={handlePredictPrice}
                    disabled={predicting || !formData.category || !formData.title || !formData.condition}
                    className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                  >
                    {predicting ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Sparkles className="mr-2 h-4 w-4" />
                        Get AI Price Prediction
                      </>
                    )}
                  </Button>
                  
                  {predictedPrice && (
                    <Alert className="mt-3 bg-gradient-to-r from-purple-50 to-blue-50 border-purple-300">
                      <Sparkles className="h-4 w-4 text-purple-600" />
                      <AlertDescription className="text-sm">
                        <strong>AI Suggested Price: PKR {predictedPrice.predicted_price.toLocaleString()}</strong>
                        <br />
                        <span className="text-xs text-gray-600">
                          Confidence: {Math.round(predictedPrice.confidence_score * 100)}% • 
                          Range: {predictedPrice.price_range_min.toLocaleString()} - {predictedPrice.price_range_max.toLocaleString()}
                        </span>
                        {predictedPrice.extracted_features && (
                          <div className="mt-2 pt-2 border-t border-purple-200">
                            <div className="text-xs font-semibold text-purple-700 mb-1">📱 Detected Specs:</div>
                            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-700">
                              <div>💾 RAM: {predictedPrice.extracted_features.ram_gb}GB</div>
                              <div>📦 Storage: {predictedPrice.extracted_features.storage_gb}GB</div>
                              {predictedPrice.extracted_features.camera_mp !== "Not detected" && (
                                <div>📷 Camera: {predictedPrice.extracted_features.camera_mp}MP</div>
                              )}
                              {predictedPrice.extracted_features.battery_mah !== "Not detected" && (
                                <div>🔋 Battery: {predictedPrice.extracted_features.battery_mah}mAh</div>
                              )}
                              {predictedPrice.extracted_features.screen_inch !== "Not detected" && (
                                <div>📱 Screen: {predictedPrice.extracted_features.screen_inch}"</div>
                              )}
                              <div>📶 5G: {predictedPrice.extracted_features.has_5g ? 'Yes' : 'No'}</div>
                              <div>📅 Year: {predictedPrice.extracted_features.year}</div>
                              <div>🏆 Tier: {predictedPrice.extracted_features.brand_tier}</div>
                            </div>
                          </div>
                        )}
                      </AlertDescription>
                    </Alert>
                  )}
                </div>

                {/* Step 3: Set Your Price */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h3 className="font-semibold text-green-900 mb-2">💰 Step 3: Set Your Price</h3>
                  <p className="text-sm text-green-700 mb-3">
                    {predictedPrice 
                      ? "You can use the AI suggestion or set your own price" 
                      : "Get AI prediction first for best results"}
                  </p>
                  <div className="space-y-2">
                    <Label htmlFor="price">Your Price (PKR) *</Label>
                    <Input
                      id="price"
                      name="price"
                      type="number"
                      step="0.01"
                      value={formData.price}
                      onChange={handleChange}
                      required
                      placeholder={predictedPrice ? `Suggested: ${predictedPrice.predicted_price.toLocaleString()}` : "Enter your asking price"}
                    />
                    {predictedPrice && formData.price && (
                      <div className="text-sm mt-2">
                        {Math.abs(parseFloat(formData.price) - predictedPrice.predicted_price) >= 20000 ? (
                          <p className="text-orange-600 font-medium">
                            ⚠️ Your price differs by PKR {Math.abs(parseFloat(formData.price) - predictedPrice.predicted_price).toLocaleString()} from AI prediction. This listing will be sent for admin approval.
                          </p>
                        ) : (
                          <p className="text-green-600 font-medium">
                            ✓ Your price is within acceptable range. Listing will be published immediately.
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                
                <Button type="submit" className="w-full bg-[#143109] hover:bg-[#143109]/90" size="lg">
                  Create Listing
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* My Listings Tab */}
        <TabsContent value="listings">
        {listings.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Package className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-lg text-muted-foreground mb-4">No listings yet</p>
              <Button onClick={() => setIsCreateOpen(true)}>
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
                    {getImageUrl(listing.image_url) ? (
                      <img src={getImageUrl(listing.image_url)!} alt={listing.title} className="w-full h-full object-cover rounded-md" />
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
                    {getImageUrl(listing.image_url) ? (
                      <img src={getImageUrl(listing.image_url)!} alt={listing.title} className="w-full h-full object-cover rounded-md" />
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
