import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { listingService, predictionService } from '@/lib/api';
import { Upload, Loader2, Sparkles, TrendingUp, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function CreateListingForm() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [prediction, setPrediction] = useState<{
    predicted_price: number;
    confidence_score: number;
    price_range_min: number;
    price_range_max: number;
    extracted_features?: any;
  } | null>(null);
  const [predictionError, setPredictionError] = useState<string | null>(null);
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

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      if (!['image/jpeg', 'image/jpg', 'image/png'].includes(file.type)) {
        alert('Please upload only JPG or PNG images');
        return;
      }
      
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        alert('Image size must be less than 5MB');
        return;
      }

      setImageFile(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  // Auto-predict price when relevant fields are filled
  useEffect(() => {
    const canPredict = () => {
      if (!formData.category || !formData.title || !formData.condition) return false;
      
      if (formData.category === 'mobile' && !formData.brand) return false;
      if (formData.category === 'laptop' && !formData.brand) return false;
      
      return true;
    };

    if (canPredict()) {
      handlePredictPrice();
    } else {
      setPrediction(null);
      setPredictionError(null);
    }
  }, [formData.title, formData.category, formData.condition, formData.brand, formData.description, formData.furniture_type, formData.material]);

  const handlePredictPrice = async () => {
    setPredicting(true);
    setPredictionError(null);
    
    try {
      const features: Record<string, any> = {
        title: formData.title,
        condition: formData.condition,
        description: formData.description,
      };

      if (formData.category === 'mobile') {
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
        features,
      });

      setPrediction(result);
      // Auto-fill the price with predicted value
      setFormData({ ...formData, price: Math.round(result.predicted_price).toString() });
    } catch (error: any) {
      console.error('Prediction error:', error);
      setPredictionError(error.response?.data?.detail || 'Unable to predict price. Please ensure all required fields are filled.');
      setPrediction(null);
    } finally {
      setPredicting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!imageFile) {
      alert('Please upload a product image');
      return;
    }

    if (!formData.category) {
      alert('Please select a category');
      return;
    }

    if (!formData.condition) {
      alert('Please select the product condition');
      return;
    }

    // Category-specific validation
    if ((formData.category === 'mobile' || formData.category === 'laptop') && !formData.brand) {
      alert(`Please enter the brand for ${formData.category}`);
      return;
    }

    setLoading(true);

    try {
      const listingData: any = {
        title: formData.title,
        description: formData.description,
        price: parseFloat(formData.price),
        category: formData.category,
        condition: formData.condition,
        location: formData.location || undefined,
        images: imageFile ? [imageFile] : undefined,
        predicted_price: prediction?.predicted_price || undefined,
      };

      // Add category-specific fields
      if (formData.category === 'mobile') {
        listingData.brand = formData.brand;
      } else if (formData.category === 'laptop') {
        listingData.brand = formData.brand;
        listingData.model = formData.model;
      } else if (formData.category === 'furniture') {
        listingData.furniture_type = formData.furniture_type;
        listingData.material = formData.material;
      }

      await listingService.createListing(listingData);
      alert('Listing created successfully!');
      navigate('/dashboard');
    } catch (error: any) {
      console.error('Failed to create listing:', error);
      alert(error.response?.data?.detail || 'Failed to create listing');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader className="bg-gradient-to-r from-[#143109] to-[#AAAE7F] text-white">
        <CardTitle className="text-2xl">Create New Listing</CardTitle>
      </CardHeader>
      <CardContent className="mt-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Image Upload */}
          <div className="space-y-2">
            <Label>Product Image (Required) *</Label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-[#143109] transition-colors">
              {imagePreview ? (
                <div className="space-y-4">
                  <img
                    src={imagePreview}
                    alt="Preview"
                    className="max-h-64 mx-auto rounded-lg object-contain"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setImageFile(null);
                      setImagePreview(null);
                    }}
                  >
                    Remove Image
                  </Button>
                </div>
              ) : (
                <label className="cursor-pointer block">
                  <input
                    type="file"
                    accept=".jpg,.jpeg,.png"
                    onChange={handleImageChange}
                    className="hidden"
                    required
                  />
                  <Upload className="h-12 w-12 mx-auto text-gray-400 mb-2" />
                  <p className="text-sm text-gray-600">
                    Click to upload image (JPG, PNG - Max 5MB)
                  </p>
                  <p className="text-xs text-red-600 mt-2">* Required for listing</p>
                </label>
              )}
            </div>
          </div>

          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title">Title *</Label>
            <Input
              id="title"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              required
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description *</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={4}
              required
            />
          </div>

          {/* Price */}
          <div className="space-y-2">
            <Label htmlFor="price">Price (PKR) *</Label>
            <Input
              id="price"
              type="number"
              value={formData.price}
              onChange={(e) => setFormData({ ...formData, price: e.target.value })}
              required
            />
          </div>

          {/* AI Price Prediction */}
          {predicting && (
            <Alert className="bg-blue-50 border-blue-200">
              <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
              <AlertDescription className="text-blue-800 ml-2">
                Analyzing your product and predicting optimal price...
              </AlertDescription>
            </Alert>
          )}

          {prediction && !predicting && (
            <Alert className="bg-gradient-to-r from-green-50 to-emerald-50 border-green-300">
              <Sparkles className="h-5 w-5 text-green-600" />
              <AlertDescription className="ml-2">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-green-900">AI Predicted Price:</span>
                    <span className="text-2xl font-bold text-green-700">
                      Rs. {Math.round(prediction.predicted_price).toLocaleString()}
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-green-800">Confidence Score:</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 h-2 bg-green-200 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-green-600 rounded-full transition-all"
                          style={{ width: `${prediction.confidence_score * 100}%` }}
                        />
                      </div>
                      <span className="font-semibold text-green-700">
                        {Math.round(prediction.confidence_score * 100)}%
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-sm text-green-800">
                    <TrendingUp className="h-4 w-4" />
                    <span>
                      Recommended range: Rs. {Math.round(prediction.price_range_min).toLocaleString()} - 
                      Rs. {Math.round(prediction.price_range_max).toLocaleString()}
                    </span>
                  </div>

                  {prediction.extracted_features && (
                    <details className="text-xs text-green-700 mt-2">
                      <summary className="cursor-pointer hover:text-green-900">View detected features</summary>
                      <div className="mt-2 p-2 bg-white rounded border border-green-200">
                        <pre className="text-xs">{JSON.stringify(prediction.extracted_features, null, 2)}</pre>
                      </div>
                    </details>
                  )}
                </div>
              </AlertDescription>
            </Alert>
          )}

          {predictionError && !predicting && (
            <Alert className="bg-amber-50 border-amber-300">
              <AlertCircle className="h-4 w-4 text-amber-600" />
              <AlertDescription className="text-amber-800 ml-2">
                {predictionError}
              </AlertDescription>
            </Alert>
          )}

          {/* Category */}
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
                <SelectItem value="mobile">Mobile Phone</SelectItem>
                <SelectItem value="laptop">Laptop</SelectItem>
                <SelectItem value="furniture">Furniture</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Condition */}
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

          {/* Category-specific fields */}
          {(formData.category === 'mobile' || formData.category === 'laptop') && (
            <div className="space-y-2">
              <Label htmlFor="brand">Brand *</Label>
              <Input
                id="brand"
                value={formData.brand}
                onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
                placeholder="e.g., Samsung, Apple, Dell"
                required
              />
            </div>
          )}

          {formData.category === 'laptop' && (
            <div className="space-y-2">
              <Label htmlFor="model">Model</Label>
              <Input
                id="model"
                value={formData.model}
                onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                placeholder="e.g., MacBook Pro, ThinkPad"
              />
            </div>
          )}

          {formData.category === 'furniture' && (
            <>
              <div className="space-y-2">
                <Label htmlFor="furniture_type">Type</Label>
                <Input
                  id="furniture_type"
                  value={formData.furniture_type}
                  onChange={(e) => setFormData({ ...formData, furniture_type: e.target.value })}
                  placeholder="e.g., Sofa, Bed, Table"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="material">Material</Label>
                <Input
                  id="material"
                  value={formData.material}
                  onChange={(e) => setFormData({ ...formData, material: e.target.value })}
                  placeholder="e.g., Wood, Leather, Metal"
                />
              </div>
            </>
          )}

          {/* Location */}
          <div className="space-y-2">
            <Label htmlFor="location">Location</Label>
            <Input
              id="location"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            />
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-[#143109] hover:bg-[#AAAE7F]"
            size="lg"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Creating...
              </>
            ) : (
              'Create Listing'
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
