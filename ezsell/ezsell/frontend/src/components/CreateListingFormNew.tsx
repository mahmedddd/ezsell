import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { listingService, getImageUrl } from '@/lib/api';
import { Upload, Loader2, Sparkles, TrendingUp, AlertCircle, CheckCircle2, XCircle, Info, PartyPopper, Eye } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface CreateListingFormNewProps {
  editMode?: boolean;
  listingId?: number;
  existingData?: any;
}

export function CreateListingFormNew({ editMode = false, listingId, existingData }: CreateListingFormNewProps = {}) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [validatingTitle, setValidatingTitle] = useState(false);
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);
  const [dropdownOptions, setDropdownOptions] = useState<any>({});
  const [titleValidation, setTitleValidation] = useState<{
    is_valid: boolean;
    message: string;
    hints?: any;
  } | null>(null);
  const [prediction, setPrediction] = useState<any | null>(null);
  const [predictionError, setPredictionError] = useState<string | null>(null);
  const [showPreviewDialog, setShowPreviewDialog] = useState(false);
  const [createdListing, setCreatedListing] = useState<any | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    price: '',
    category: 'mobile',
    condition: '5',
    city: '',
    area: '',
    location: '',
    // Mobile specs
    brand: '',
    ram: 0,
    storage: 0,
    camera: 0,
    battery: 0,
    screen_size: 0,
    has_5g: false,
    has_pta: false,
    has_amoled: false,
    has_warranty: false,
    has_box: false,
    // Laptop specs
    processor: '',
    generation: 10,
    gpu: '',
    has_ssd: true,
    is_gaming: false,
    is_touchscreen: false,
    has_backlit_keyboard: false,
    // Furniture specs
    material: '',
    furniture_type: '',
    furniture_subtype: '',
    seating_capacity: 0,
    is_imported: false,
    is_handmade: false,
    has_storage: false,
    is_modern: false,
    is_antique: false,
    is_foldable: false,
    is_custom_made: false,
  });

  // Load dropdown options for selected category
  const loadDropdownOptions = async (category: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/dropdown-options/${category}`);
      if (response.ok) {
        const data = await response.json();
        setDropdownOptions(data);
      }
    } catch (err) {
      console.error('Error loading dropdown options:', err);
    }
  };

  // Validate title in real-time
  const validateTitle = async (category: string, title: string, description: string = '', material: string = '') => {
    if (!title || title.length < 5) {
      setTitleValidation(null);
      return;
    }

    setValidatingTitle(true);
    try {
      const params = new URLSearchParams({
        category,
        title,
        description,
        material
      });

      const response = await fetch(`http://localhost:8000/api/v1/validate-title?${params}`);
      if (response.ok) {
        const result = await response.json();
        setTitleValidation(result);
      }
    } catch (err) {
      console.error('Error validating title:', err);
    } finally {
      setValidatingTitle(false);
    }
  };

  // Load dropdown options when category changes
  useEffect(() => {
    if (formData.category) {
      loadDropdownOptions(formData.category);
    }
  }, [formData.category]);

  // Populate form data in edit mode
  useEffect(() => {
    if (editMode && existingData) {
      // Parse location if it exists
      let city = '';
      let area = '';
      if (existingData.location) {
        const locationParts = existingData.location.split(',').map((s: string) => s.trim());
        if (locationParts.length >= 2) {
          city = locationParts[0];
          area = locationParts[1];
        } else {
          city = locationParts[0] || '';
        }
      }

      setFormData({
        title: existingData.title || '',
        description: existingData.description || '',
        price: existingData.price?.toString() || '',
        category: existingData.category || 'mobile',
        condition: existingData.condition || '5',
        city: city,
        area: area,
        location: existingData.location || '',
        brand: existingData.brand || '',
        ram: existingData.ram || 0,
        storage: existingData.storage || 0,
        camera: existingData.camera || 0,
        battery: existingData.battery || 0,
        screen_size: existingData.screen_size || 0,
        has_5g: existingData.has_5g || false,
        has_pta: existingData.has_pta || false,
        has_amoled: existingData.has_amoled || false,
        has_warranty: existingData.has_warranty || false,
        has_box: existingData.has_box || false,
        processor: existingData.processor || '',
        generation: existingData.generation || 10,
        gpu: existingData.gpu || '',
        has_ssd: existingData.has_ssd !== undefined ? existingData.has_ssd : true,
        is_gaming: existingData.is_gaming || false,
        is_touchscreen: existingData.is_touchscreen || false,
        has_backlit_keyboard: existingData.has_backlit_keyboard || false,
        material: existingData.material || '',
        furniture_type: existingData.furniture_type || '',
        furniture_subtype: existingData.furniture_subtype || '',
        seating_capacity: existingData.seating_capacity || 0,
        is_imported: existingData.is_imported || false,
        is_handmade: existingData.is_handmade || false,
        has_storage: existingData.has_storage || false,
        is_modern: existingData.is_modern || false,
        is_antique: existingData.is_antique || false,
        is_foldable: existingData.is_foldable || false,
        is_custom_made: existingData.is_custom_made || false,
      });

      // Load existing images as previews
      if (existingData.images) {
        try {
          const parsedImages = typeof existingData.images === 'string' ? JSON.parse(existingData.images) : existingData.images;
          if (Array.isArray(parsedImages)) {
            const imageUrls = parsedImages.map((img: string) => getImageUrl(img));
            setImagePreviews(imageUrls.filter((url: string | null): url is string => url !== null));
          }
        } catch (e) {
          console.error('Failed to parse existing images:', e);
        }
      } else if (existingData.image_url) {
        const url = getImageUrl(existingData.image_url);
        if (url) setImagePreviews([url]);
      }
    }
  }, [editMode, existingData]);

  // Validate title with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      if (formData.title && formData.category) {
        const material = formData.category === 'furniture' ? formData.material : '';
        validateTitle(formData.category, formData.title, formData.description, material);
      }
    }, 800);

    return () => clearTimeout(timer);
  }, [formData.title, formData.description, formData.material, formData.category]);

  // Auto-predict price when title is valid and any relevant field changes
  useEffect(() => {
    const canPredict = () => {
      if (!formData.category || !formData.title || !formData.condition) return false;
      if (!titleValidation || !titleValidation.is_valid) return false;
      if (formData.category === 'furniture' && !formData.material) return false;
      
      return true;
    };

    if (canPredict()) {
      const timer = setTimeout(() => {
        handlePredictPrice();
      }, 1200);
      return () => clearTimeout(timer);
    } else {
      setPrediction(null);
    }
  }, [
    formData.title, 
    formData.category, 
    formData.condition, 
    formData.description, 
    formData.material, 
    titleValidation,
    // Mobile specific fields that affect price
    formData.has_pta,
    formData.has_warranty,
    formData.has_box,
    formData.has_5g,
    formData.has_amoled,
    formData.ram,
    formData.storage,
    // Laptop specific fields that affect price
    formData.has_ssd,
    formData.is_gaming,
    formData.is_touchscreen,
    formData.gpu,
    formData.processor,
    formData.generation,
    // Furniture specific fields that affect price
    formData.furniture_type,
    formData.furniture_subtype,
    formData.seating_capacity,
    formData.is_antique,
    formData.is_handmade,
    formData.is_imported,
    formData.has_storage,
  ]);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    
    if (files.length > 7) {
      alert('Maximum 7 images allowed');
      return;
    }
    
    // Validate each file
    for (const file of files) {
      if (!['image/jpeg', 'image/jpg', 'image/png'].includes(file.type)) {
        alert('Please upload only JPG, JPEG or PNG images');
        return;
      }
      
      if (file.size > 10 * 1024 * 1024) {
        alert('Each image must be less than 10MB');
        return;
      }
    }

    setImageFiles(files);
    
    // Create previews for all images
    const previews: string[] = [];
    let loadedCount = 0;
    
    files.forEach((file) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        previews.push(reader.result as string);
        loadedCount++;
        if (loadedCount === files.length) {
          setImagePreviews(previews);
        }
      };
      reader.readAsDataURL(file);
    });
  };

  const handlePredictPrice = async () => {
    if (!titleValidation || !titleValidation.is_valid) {
      setPredictionError('Please provide a valid title with relevant product information');
      return;
    }

    setPredicting(true);
    setPredictionError(null);
    
    try {
      const requestData: any = {
        category: formData.category,
        title: formData.title,
        description: formData.description,
        condition: formData.condition,
      };

      // Add category-specific fields
      if (formData.category === 'mobile') {
        Object.assign(requestData, {
          brand: formData.brand,
          ram: formData.ram,
          storage: formData.storage,
          camera: formData.camera,
          battery: formData.battery,
          screen_size: formData.screen_size,
          has_5g: formData.has_5g,
          has_pta: formData.has_pta,
          has_amoled: formData.has_amoled,
          has_warranty: formData.has_warranty,
          has_box: formData.has_box,
        });
      } else if (formData.category === 'laptop') {
        Object.assign(requestData, {
          brand: formData.brand,
          processor: formData.processor,
          generation: formData.generation,
          ram: formData.ram,
          storage: formData.storage,
          gpu: formData.gpu,
          screen_size: formData.screen_size,
          has_ssd: formData.has_ssd,
          is_gaming: formData.is_gaming,
          is_touchscreen: formData.is_touchscreen,
        });
      } else if (formData.category === 'furniture') {
        Object.assign(requestData, {
          material: formData.material,
          furniture_type: formData.furniture_type,
          furniture_subtype: formData.furniture_subtype,
          seating_capacity: formData.seating_capacity,
          is_imported: formData.is_imported,
          is_handmade: formData.is_handmade,
          has_storage: formData.has_storage,
          is_modern: formData.is_modern,
          is_antique: formData.is_antique,
        });
      }

      const response = await fetch('http://localhost:8000/api/v1/predict-price', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.log('Error response:', errorData);
        
        // Extract error message from nested detail object
        let errorMsg = 'Prediction failed';
        if (errorData.detail) {
          if (typeof errorData.detail === 'string') {
            errorMsg = errorData.detail;
          } else if (typeof errorData.detail === 'object') {
            errorMsg = errorData.detail.message || errorData.detail.error || JSON.stringify(errorData.detail);
          }
        }
        throw new Error(errorMsg);
      }

      const result = await response.json();
      console.log('Prediction result:', result);
      
      // Validate result structure
      if (!result || typeof result.predicted_price === 'undefined') {
        console.log('Invalid result structure:', result);
        throw new Error('Invalid prediction response from server');
      }
      
      setPrediction(result);
      setPredictionError(null);
      
      // Auto-fill the price with predicted value
      setFormData({ ...formData, price: Math.round(result.predicted_price).toString() });
    } catch (error: any) {
      console.error('Prediction error:', error);
      
      // Extract error message properly
      let errorMessage = 'Unable to predict price';
      if (error.message && typeof error.message === 'string') {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      }
      
      setPredictionError(errorMessage);
      setPrediction(null);
    } finally {
      setPredicting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Form submitted, starting validation...');
    
    // Basic field validation
    if (!formData.title || formData.title.trim().length < 5) {
      alert('❌ Please enter a title (at least 5 characters)');
      return;
    }

    if (!formData.description || formData.description.trim().length < 10) {
      alert('❌ Please enter a description (at least 10 characters)');
      return;
    }

    if (!formData.location || formData.location.trim() === '') {
      alert('❌ Please enter the location');
      return;
    }

    // Title validation check
    if (!titleValidation || !titleValidation.is_valid) {
      alert('❌ Invalid Title: Please provide a valid title with relevant product information (brand, model, specs)');
      return;
    }

    // Only require images for new listings, not when editing
    if (!editMode) {
      if (imageFiles.length < 5) {
        alert('❌ Please upload at least 5 product images');
        return;
      }
      
      if (imageFiles.length > 10) {
        alert('❌ Maximum 10 images allowed');
        return;
      }
    }

    // Category-specific validation
    if ((formData.category === 'mobile' || formData.category === 'laptop') && !formData.brand) {
      alert('❌ Please select a brand from the dropdown');
      return;
    }

    if (formData.category === 'furniture' && !formData.furniture_type) {
      alert('❌ Please select the furniture type');
      return;
    }

    if (formData.category === 'furniture' && !formData.material) {
      alert('❌ Please select the material for furniture');
      return;
    }

    if (!formData.price || parseFloat(formData.price) <= 0) {
      alert('❌ Please enter a valid price');
      return;
    }

    // Check if user is logged in
    const token = localStorage.getItem('authToken');
    if (!token) {
      alert('❌ Please login first to create a listing');
      navigate('/login');
      return;
    }

    setLoading(true);
    console.log(editMode ? '=== STARTING LISTING UPDATE ===' : '=== STARTING LISTING CREATION ===');
    console.log('Form data:', formData);
    console.log('Image files:', imageFiles.map(f => f.name));
    console.log('Token present:', !!localStorage.getItem('authToken'));

    try {
      const listingData: any = {
        title: formData.title.trim(),
        description: formData.description.trim(),
        price: parseFloat(formData.price),
        category: formData.category,
        condition: formData.condition,
        location: formData.location.trim(),
        images: imageFiles.length > 0 ? imageFiles : undefined,
        predicted_price: prediction?.predicted_price || undefined,
        brand: formData.brand || undefined,
        material: formData.material || undefined,
        furniture_type: formData.furniture_type || undefined,
      };

      console.log('Prepared listing data for API:', listingData);
      
      let result;
      if (editMode && listingId) {
        console.log('Calling listingService.updateListing...');
        result = await listingService.updateListing(listingId, listingData);
        console.log('✅ Listing updated successfully:', result);
        alert('✅ Listing updated successfully!');
        navigate(`/product/${listingId}`);
      } else {
        console.log('Calling listingService.createListing...');
        result = await listingService.createListing(listingData);
        console.log('✅ Listing created successfully:', result);
        // Show preview dialog instead of alert
        setCreatedListing(result);
        setShowPreviewDialog(true);
      }
    } catch (error: any) {
      console.error('=== ERROR CREATING LISTING ===');
      console.error('Error object:', error);
      console.error('Error message:', error.message);
      console.error('Error response:', error.response);
      console.error('Error request:', error.request);
      console.error('Error config:', error.config);
      
      // Check for network error (no response)
      if (!error.response && !error.request) {
        alert('❌ Network Error: Unable to connect to server. Please check if the backend is running on http://localhost:8000');
        return;
      }
      
      // Check if request was made but no response received
      if (error.request && !error.response) {
        alert('❌ Network Error: No response from server. Please check your internet connection and backend server.');
        return;
      }
      
      // Check for authentication error
      if (error.response?.status === 401) {
        alert('❌ Session expired. Please login again.');
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        navigate('/login');
        return;
      }
      
      // Check for validation errors
      if (error.response?.status === 422) {
        const details = error.response?.data?.detail;
        if (Array.isArray(details)) {
          const fieldErrors = details.map((d: any) => `${d.loc?.join('.')||'field'}: ${d.msg}`).join('\n');
          alert('❌ Validation Error:\n' + fieldErrors);
        } else {
          alert('❌ Validation Error: ' + (details || 'Invalid data'));
        }
        return;
      }
      
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to create listing. Please try again.';
      alert('❌ Error: ' + errorMsg);
    } finally {
      setLoading(false);
      console.log('=== LISTING CREATION ENDED ===');
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-PK', {
      style: 'currency',
      currency: 'PKR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <Card className="max-w-4xl mx-auto">
        <CardHeader className="bg-gradient-to-r from-[#143109] to-[#AAAE7F] text-white">
          <CardTitle className="text-2xl flex items-center gap-2">
            <Sparkles className="h-6 w-6" />
            {editMode ? 'Edit Listing' : 'Create New Listing'}
          </CardTitle>
          <CardDescription className="text-white/90">
            {editMode ? 'Update your product information' : 'Add a new product with AI-powered price prediction'}
          </CardDescription>
        </CardHeader>
        <CardContent className="mt-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            
            {/* Step 1: Basic Details */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                📝 Step 1: Product Details
              </h3>
              
              {/* Category */}
              <div className="space-y-2">
                <Label>Category *</Label>
                <Select
                  value={formData.category}
                  onValueChange={(value) => {
                    setFormData({ ...formData, category: value });
                    setPrediction(null);
                    setTitleValidation(null);
                  }}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="mobile">📱 Mobile</SelectItem>
                    <SelectItem value="laptop">💻 Laptop</SelectItem>
                    <SelectItem value="furniture">🛋️ Furniture</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Condition - 10 Level Scale */}
              <div className="space-y-2">
                <Label>Condition * (Affects Price Prediction)</Label>
                <Select
                  value={formData.condition}
                  onValueChange={(value) => setFormData({ ...formData, condition: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="10">10 - Brand New/Sealed (~100% value)</SelectItem>
                    <SelectItem value="9">9 - Excellent/Mint (~95% value)</SelectItem>
                    <SelectItem value="8">8 - Like New (~88% value)</SelectItem>
                    <SelectItem value="7">7 - Very Good (~80% value)</SelectItem>
                    <SelectItem value="6">6 - Good (~70% value)</SelectItem>
                    <SelectItem value="5">5 - Average/Used (~60% value)</SelectItem>
                    <SelectItem value="4">4 - Fair (~48% value)</SelectItem>
                    <SelectItem value="3">3 - Acceptable (~35% value)</SelectItem>
                    <SelectItem value="2">2 - Poor/Damaged (~25% value)</SelectItem>
                    <SelectItem value="1">1 - For Parts/Broken (~15% value)</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500 mt-1">
                  Select the condition level that best matches your product. Higher numbers = better condition = higher predicted price.
                </p>
              </div>

              {/* Title with Validation */}
              <div className="space-y-2">
                <Label>Title * (Include brand, model, specs)</Label>
                <Input
                  placeholder={
                    formData.category === 'mobile'
                      ? 'e.g., Samsung Galaxy S23 Ultra 12GB RAM 256GB'
                      : formData.category === 'laptop'
                      ? 'e.g., Dell XPS 15 Intel Core i7 12th Gen 16GB RAM'
                      : 'e.g., Modern 5 Seater L-Shape Sofa Premium Fabric'
                  }
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className={
                    titleValidation
                      ? titleValidation.is_valid
                        ? 'border-green-500'
                        : 'border-red-500'
                      : ''
                  }
                  required
                />
                {validatingTitle && (
                  <p className="text-sm text-muted-foreground flex items-center gap-2">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    Validating title...
                  </p>
                )}
                {titleValidation && !validatingTitle && (
                  <div className={`flex items-start gap-2 p-3 rounded-lg ${
                    titleValidation.is_valid ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                  }`}>
                    {titleValidation.is_valid ? (
                      <CheckCircle2 className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    ) : (
                      <XCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    )}
                    <div className="text-sm">
                      <p className="font-medium">{titleValidation.message}</p>
                      {!titleValidation.is_valid && titleValidation.hints && (
                        <p className="mt-1 text-xs">
                          Example: {titleValidation.hints.example}
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Description */}
              <div className="space-y-2">
                <Label>Description *</Label>
                <Textarea
                  placeholder="Add detailed description including features, condition, age..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={4}
                  required
                />
              </div>

              {/* Location - City and Area */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>City *</Label>
                  <Select
                    value={formData.city}
                    onValueChange={(value) => {
                      setFormData({ ...formData, city: value, area: '', location: value });
                    }}
                    required
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select city" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Islamabad">Islamabad</SelectItem>
                      <SelectItem value="Rawalpindi">Rawalpindi</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Area/Sector *</Label>
                  <Select
                    value={formData.area}
                    onValueChange={(value) => {
                      setFormData({ ...formData, area: value, location: `${formData.city}, ${value}` });
                    }}
                    disabled={!formData.city}
                    required
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={formData.city ? "Select area" : "Select city first"} />
                    </SelectTrigger>
                    <SelectContent>
                      {formData.city === 'Islamabad' && [
                        'Bahria Town', 'Blue Area', 'DHA Phase 1', 'DHA Phase 2', 'F-6', 'F-7', 'F-8', 'F-10', 'F-11',
                        'G-6', 'G-7', 'G-8', 'G-9', 'G-10', 'G-11', 'G-13', 'G-14', 'G-15',
                        'I-8', 'I-9', 'I-10', 'I-11', 'I-14',
                        'PWD Housing Scheme', 'Sector B-17', 'Sector C-18', 'Sector D-12', 'Sector D-17', 'Sector E-7', 'Sector E-11'
                      ].sort().map(area => (
                        <SelectItem key={area} value={area}>{area}</SelectItem>
                      ))}
                      {formData.city === 'Rawalpindi' && [
                        'Adyala Road', 'Airport Housing Society', 'Allama Iqbal Town', 'Bahria Town Phase 1', 'Bahria Town Phase 2',
                        'Bahria Town Phase 3', 'Bahria Town Phase 4', 'Bahria Town Phase 5', 'Bahria Town Phase 6',
                        'Bahria Town Phase 7', 'Bahria Town Phase 8', 'Chaklala Scheme 3', 'Commercial Market',
                        'Committee Chowk', 'DHA Phase 1', 'DHA Phase 2', 'Gulistan Colony', 'Gulzar-e-Quaid',
                        'Jinnah Garden', 'Korang Town', 'Main Murree Road', 'Misrial Road', 'Model Town',
                        'Peoples Colony', 'PWD Housing Scheme', 'Saddar', 'Satellite Town', 'Shamshabad', 'Shamsabad',
                        'Tench Bhatta', 'Westridge', 'Wah Cantt'
                      ].sort().map(area => (
                        <SelectItem key={area} value={area}>{area}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Image Upload */}
              <div className="space-y-2">
                <Label>Product Images (Up to 7 images)</Label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-[#143109] transition-colors">
                  {imagePreviews.length > 0 ? (
                    <div className="space-y-4">
                      <div className="grid grid-cols-3 gap-4">
                        {imagePreviews.map((preview, index) => (
                          <div key={index} className="relative">
                            <img
                              src={preview}
                              alt={`Preview ${index + 1}`}
                              className="h-32 w-full rounded-lg object-cover"
                            />
                            <span className="absolute top-1 right-1 bg-black bg-opacity-60 text-white text-xs px-2 py-1 rounded">
                              {index + 1}
                            </span>
                          </div>
                        ))}
                      </div>
                      <p className="text-sm text-green-600 font-medium">
                        ✅ {imagePreviews.length} images uploaded
                      </p>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => {
                          setImageFiles([]);
                          setImagePreviews([]);
                        }}
                      >
                        Remove All Images
                      </Button>
                    </div>
                  ) : (
                    <label className="cursor-pointer block">
                      <input
                        type="file"
                        accept=".jpg,.jpeg,.png"
                        onChange={handleImageChange}
                        className="hidden"
                        multiple
                      />
                      <Upload className="h-12 w-12 mx-auto text-gray-400 mb-2" />
                      <p className="text-sm text-gray-600 font-medium">
                        Click to upload images (optional)
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        JPG, JPEG, PNG - Max 10MB each - Up to 7 images
                      </p>
                      <p className="text-xs text-gray-500 mt-2">
                        📸 Maximum 7 images allowed
                      </p>
                    </label>
                  )}
                </div>
              </div>
            </div>

            {/* Step 2: Category-Specific Fields */}
            {formData.category && (
              <div className="space-y-4 border-t pt-6">
                <h3 className="text-lg font-semibold">
                  🔧 Step 2: {formData.category.charAt(0).toUpperCase() + formData.category.slice(1)} Specifications
                </h3>

                {/* Mobile Fields */}
                {formData.category === 'mobile' && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Brand *</Label>
                      <Select value={formData.brand} onValueChange={(v) => setFormData({ ...formData, brand: v })} required>
                        <SelectTrigger>
                          <SelectValue placeholder="Select brand" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Apple">Apple</SelectItem>
                          <SelectItem value="Samsung">Samsung</SelectItem>
                          <SelectItem value="Xiaomi">Xiaomi</SelectItem>
                          <SelectItem value="Redmi">Redmi</SelectItem>
                          <SelectItem value="Oppo">Oppo</SelectItem>
                          <SelectItem value="Vivo">Vivo</SelectItem>
                          <SelectItem value="Realme">Realme</SelectItem>
                          <SelectItem value="OnePlus">OnePlus</SelectItem>
                          <SelectItem value="Huawei">Huawei</SelectItem>
                          <SelectItem value="Google">Google</SelectItem>
                          <SelectItem value="Nokia">Nokia</SelectItem>
                          <SelectItem value="Infinix">Infinix</SelectItem>
                          <SelectItem value="Tecno">Tecno</SelectItem>
                          <SelectItem value="Other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>RAM (GB)</Label>
                      <Select value={String(formData.ram)} onValueChange={(v) => setFormData({ ...formData, ram: parseInt(v) })}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0">Unknown</SelectItem>
                          <SelectItem value="2">2 GB</SelectItem>
                          <SelectItem value="3">3 GB</SelectItem>
                          <SelectItem value="4">4 GB</SelectItem>
                          <SelectItem value="6">6 GB</SelectItem>
                          <SelectItem value="8">8 GB</SelectItem>
                          <SelectItem value="12">12 GB</SelectItem>
                          <SelectItem value="16">16 GB</SelectItem>
                          <SelectItem value="18">18 GB</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Storage (GB)</Label>
                      <Select value={String(formData.storage)} onValueChange={(v) => setFormData({ ...formData, storage: parseInt(v) })}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0">Unknown</SelectItem>
                          <SelectItem value="16">16 GB</SelectItem>
                          <SelectItem value="32">32 GB</SelectItem>
                          <SelectItem value="64">64 GB</SelectItem>
                          <SelectItem value="128">128 GB</SelectItem>
                          <SelectItem value="256">256 GB</SelectItem>
                          <SelectItem value="512">512 GB</SelectItem>
                          <SelectItem value="1024">1 TB</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Camera (MP)</Label>
                      <Select value={String(formData.camera)} onValueChange={(v) => setFormData({ ...formData, camera: parseInt(v) })}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0">Unknown</SelectItem>
                          <SelectItem value="8">8 MP</SelectItem>
                          <SelectItem value="12">12 MP</SelectItem>
                          <SelectItem value="13">13 MP</SelectItem>
                          <SelectItem value="16">16 MP</SelectItem>
                          <SelectItem value="20">20 MP</SelectItem>
                          <SelectItem value="48">48 MP</SelectItem>
                          <SelectItem value="50">50 MP</SelectItem>
                          <SelectItem value="64">64 MP</SelectItem>
                          <SelectItem value="108">108 MP</SelectItem>
                          <SelectItem value="200">200 MP</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Mobile Boolean Features */}
                    <div className="col-span-2 grid grid-cols-2 gap-3 mt-2">
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.has_5g}
                          onCheckedChange={(checked) => setFormData({ ...formData, has_5g: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">5G Support</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.has_pta}
                          onCheckedChange={(checked) => setFormData({ ...formData, has_pta: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">PTA Approved</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.has_amoled}
                          onCheckedChange={(checked) => setFormData({ ...formData, has_amoled: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">AMOLED Display</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.has_warranty}
                          onCheckedChange={(checked) => setFormData({ ...formData, has_warranty: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">Warranty</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.has_box}
                          onCheckedChange={(checked) => setFormData({ ...formData, has_box: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">Original Box</Label>
                      </div>
                    </div>
                  </div>
                )}

                {/* Laptop Fields */}
                {formData.category === 'laptop' && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Brand *</Label>
                      <Select value={formData.brand} onValueChange={(v) => setFormData({ ...formData, brand: v })} required>
                        <SelectTrigger>
                          <SelectValue placeholder="Select brand" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="HP">HP</SelectItem>
                          <SelectItem value="Dell">Dell</SelectItem>
                          <SelectItem value="Lenovo">Lenovo</SelectItem>
                          <SelectItem value="Apple">Apple</SelectItem>
                          <SelectItem value="Asus">Asus</SelectItem>
                          <SelectItem value="Acer">Acer</SelectItem>
                          <SelectItem value="MSI">MSI</SelectItem>
                          <SelectItem value="Microsoft">Microsoft</SelectItem>
                          <SelectItem value="Razer">Razer</SelectItem>
                          <SelectItem value="Other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Processor</Label>
                      <Select value={formData.processor} onValueChange={(v) => setFormData({ ...formData, processor: v })}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select processor" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Intel Core i3">Intel Core i3</SelectItem>
                          <SelectItem value="Intel Core i5">Intel Core i5</SelectItem>
                          <SelectItem value="Intel Core i7">Intel Core i7</SelectItem>
                          <SelectItem value="Intel Core i9">Intel Core i9</SelectItem>
                          <SelectItem value="AMD Ryzen 3">AMD Ryzen 3</SelectItem>
                          <SelectItem value="AMD Ryzen 5">AMD Ryzen 5</SelectItem>
                          <SelectItem value="AMD Ryzen 7">AMD Ryzen 7</SelectItem>
                          <SelectItem value="AMD Ryzen 9">AMD Ryzen 9</SelectItem>
                          <SelectItem value="Apple M1">Apple M1</SelectItem>
                          <SelectItem value="Apple M2">Apple M2</SelectItem>
                          <SelectItem value="Apple M3">Apple M3</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>RAM (GB)</Label>
                      <Select value={String(formData.ram)} onValueChange={(v) => setFormData({ ...formData, ram: parseInt(v) })}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0">Unknown</SelectItem>
                          <SelectItem value="4">4 GB</SelectItem>
                          <SelectItem value="8">8 GB</SelectItem>
                          <SelectItem value="12">12 GB</SelectItem>
                          <SelectItem value="16">16 GB</SelectItem>
                          <SelectItem value="24">24 GB</SelectItem>
                          <SelectItem value="32">32 GB</SelectItem>
                          <SelectItem value="64">64 GB</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Storage (GB)</Label>
                      <Select value={String(formData.storage)} onValueChange={(v) => setFormData({ ...formData, storage: parseInt(v) })}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0">Unknown</SelectItem>
                          <SelectItem value="128">128 GB</SelectItem>
                          <SelectItem value="256">256 GB</SelectItem>
                          <SelectItem value="512">512 GB</SelectItem>
                          <SelectItem value="1024">1 TB</SelectItem>
                          <SelectItem value="2048">2 TB</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>GPU</Label>
                      <Select value={formData.gpu} onValueChange={(v) => setFormData({ ...formData, gpu: v })}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select GPU" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Integrated">Integrated</SelectItem>
                          <SelectItem value="NVIDIA GTX 1650">NVIDIA GTX 1650</SelectItem>
                          <SelectItem value="NVIDIA RTX 3050">NVIDIA RTX 3050</SelectItem>
                          <SelectItem value="NVIDIA RTX 3060">NVIDIA RTX 3060</SelectItem>
                          <SelectItem value="NVIDIA RTX 4050">NVIDIA RTX 4050</SelectItem>
                          <SelectItem value="NVIDIA RTX 4060">NVIDIA RTX 4060</SelectItem>
                          <SelectItem value="AMD Radeon">AMD Radeon</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Laptop Boolean Features */}
                    <div className="col-span-2 grid grid-cols-2 gap-3 mt-2">
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.has_ssd}
                          onCheckedChange={(checked) => setFormData({ ...formData, has_ssd: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">SSD Storage</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.is_gaming}
                          onCheckedChange={(checked) => setFormData({ ...formData, is_gaming: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">Gaming Laptop</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.is_touchscreen}
                          onCheckedChange={(checked) => setFormData({ ...formData, is_touchscreen: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">Touchscreen</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.has_backlit_keyboard}
                          onCheckedChange={(checked) => setFormData({ ...formData, has_backlit_keyboard: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">Backlit Keyboard</Label>
                      </div>
                    </div>
                  </div>
                )}

                {/* Furniture Fields */}
                {formData.category === 'furniture' && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Material *</Label>
                      <Select value={formData.material} onValueChange={(v) => setFormData({ ...formData, material: v })} required>
                        <SelectTrigger>
                          <SelectValue placeholder="Select material" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="wood">Wood</SelectItem>
                          <SelectItem value="metal">Metal</SelectItem>
                          <SelectItem value="plastic">Plastic</SelectItem>
                          <SelectItem value="glass">Glass</SelectItem>
                          <SelectItem value="fabric">Fabric</SelectItem>
                          <SelectItem value="leather">Leather</SelectItem>
                          <SelectItem value="rattan">Rattan</SelectItem>
                          <SelectItem value="marble">Marble</SelectItem>
                          <SelectItem value="other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Furniture Type</Label>
                      <Select value={formData.furniture_type} onValueChange={(v) => setFormData({ ...formData, furniture_type: v, furniture_subtype: '' })}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select furniture type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="sofa">Sofa</SelectItem>
                          <SelectItem value="chair">Chair</SelectItem>
                          <SelectItem value="table">Table</SelectItem>
                          <SelectItem value="bed">Bed</SelectItem>
                          <SelectItem value="wardrobe">Wardrobe</SelectItem>
                          <SelectItem value="desk">Desk</SelectItem>
                          <SelectItem value="cabinet">Cabinet</SelectItem>
                          <SelectItem value="shelf">Shelf</SelectItem>
                          <SelectItem value="dressing_table">Dressing Table</SelectItem>
                          <SelectItem value="tv_unit">TV Unit</SelectItem>
                          <SelectItem value="other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Dynamic Sub-type based on Furniture Type */}
                    {formData.furniture_type && (
                      <div>
                        <Label>
                          {formData.furniture_type === 'bed' ? 'Bed Size' :
                           formData.furniture_type === 'table' ? 'Table Type' :
                           formData.furniture_type === 'sofa' ? 'Sofa Type' :
                           formData.furniture_type === 'chair' ? 'Chair Type' :
                           formData.furniture_type === 'wardrobe' ? 'Wardrobe Size' :
                           formData.furniture_type === 'desk' ? 'Desk Type' :
                           formData.furniture_type === 'cabinet' ? 'Cabinet Type' :
                           formData.furniture_type === 'shelf' ? 'Shelf Type' :
                           formData.furniture_type === 'dressing_table' ? 'Dressing Table Type' :
                           formData.furniture_type === 'tv_unit' ? 'TV Unit Type' :
                           'Sub-type'}
                        </Label>
                        <Select value={formData.furniture_subtype} onValueChange={(v) => setFormData({ ...formData, furniture_subtype: v })}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select size/type" />
                          </SelectTrigger>
                          <SelectContent>
                            {/* Bed sizes */}
                            {formData.furniture_type === 'bed' && (
                              <>
                                <SelectItem value="single">Single Bed</SelectItem>
                                <SelectItem value="double">Double Bed</SelectItem>
                                <SelectItem value="queen">Queen Size</SelectItem>
                                <SelectItem value="king">King Size</SelectItem>
                                <SelectItem value="bunk">Bunk Bed</SelectItem>
                              </>
                            )}
                            {/* Table types */}
                            {formData.furniture_type === 'table' && (
                              <>
                                <SelectItem value="dining_4">Dining Table (4 Person)</SelectItem>
                                <SelectItem value="dining_6">Dining Table (6 Person)</SelectItem>
                                <SelectItem value="dining_8">Dining Table (8 Person)</SelectItem>
                                <SelectItem value="coffee">Coffee Table</SelectItem>
                                <SelectItem value="side">Side Table</SelectItem>
                                <SelectItem value="console">Console Table</SelectItem>
                                <SelectItem value="study">Study Table</SelectItem>
                              </>
                            )}
                            {/* Sofa types */}
                            {formData.furniture_type === 'sofa' && (
                              <>
                                <SelectItem value="2_seater">2 Seater</SelectItem>
                                <SelectItem value="3_seater">3 Seater</SelectItem>
                                <SelectItem value="5_seater">5 Seater</SelectItem>
                                <SelectItem value="7_seater">7 Seater</SelectItem>
                                <SelectItem value="l_shaped">L-Shaped</SelectItem>
                                <SelectItem value="sectional">Sectional</SelectItem>
                                <SelectItem value="sofa_cum_bed">Sofa Cum Bed</SelectItem>
                                <SelectItem value="recliner">Recliner Sofa</SelectItem>
                              </>
                            )}
                            {/* Chair types */}
                            {formData.furniture_type === 'chair' && (
                              <>
                                <SelectItem value="dining">Dining Chair</SelectItem>
                                <SelectItem value="office">Office Chair</SelectItem>
                                <SelectItem value="gaming">Gaming Chair</SelectItem>
                                <SelectItem value="rocking">Rocking Chair</SelectItem>
                                <SelectItem value="accent">Accent Chair</SelectItem>
                                <SelectItem value="bean_bag">Bean Bag</SelectItem>
                              </>
                            )}
                            {/* Wardrobe sizes */}
                            {formData.furniture_type === 'wardrobe' && (
                              <>
                                <SelectItem value="2_door">2 Door</SelectItem>
                                <SelectItem value="3_door">3 Door</SelectItem>
                                <SelectItem value="4_door">4 Door</SelectItem>
                                <SelectItem value="sliding">Sliding Door</SelectItem>
                                <SelectItem value="walk_in">Walk-in Closet</SelectItem>
                              </>
                            )}
                            {/* Desk types */}
                            {formData.furniture_type === 'desk' && (
                              <>
                                <SelectItem value="computer">Computer Desk</SelectItem>
                                <SelectItem value="executive">Executive Desk</SelectItem>
                                <SelectItem value="standing">Standing Desk</SelectItem>
                                <SelectItem value="writing">Writing Desk</SelectItem>
                                <SelectItem value="l_shaped">L-Shaped Desk</SelectItem>
                              </>
                            )}
                            {/* Cabinet types */}
                            {formData.furniture_type === 'cabinet' && (
                              <>
                                <SelectItem value="kitchen">Kitchen Cabinet</SelectItem>
                                <SelectItem value="bathroom">Bathroom Cabinet</SelectItem>
                                <SelectItem value="storage">Storage Cabinet</SelectItem>
                                <SelectItem value="display">Display Cabinet</SelectItem>
                                <SelectItem value="filing">Filing Cabinet</SelectItem>
                              </>
                            )}
                            {/* Shelf types */}
                            {formData.furniture_type === 'shelf' && (
                              <>
                                <SelectItem value="bookshelf">Bookshelf</SelectItem>
                                <SelectItem value="wall_shelf">Wall Shelf</SelectItem>
                                <SelectItem value="corner">Corner Shelf</SelectItem>
                                <SelectItem value="floating">Floating Shelf</SelectItem>
                                <SelectItem value="shoe_rack">Shoe Rack</SelectItem>
                              </>
                            )}
                            {/* Dressing Table types */}
                            {formData.furniture_type === 'dressing_table' && (
                              <>
                                <SelectItem value="with_mirror">With Mirror</SelectItem>
                                <SelectItem value="with_storage">With Storage</SelectItem>
                                <SelectItem value="vanity">Vanity Set</SelectItem>
                                <SelectItem value="simple">Simple</SelectItem>
                              </>
                            )}
                            {/* TV Unit types */}
                            {formData.furniture_type === 'tv_unit' && (
                              <>
                                <SelectItem value="wall_mount">Wall Mount</SelectItem>
                                <SelectItem value="floor_standing">Floor Standing</SelectItem>
                                <SelectItem value="entertainment_center">Entertainment Center</SelectItem>
                                <SelectItem value="simple">Simple</SelectItem>
                              </>
                            )}
                            {/* Other or unselected */}
                            {formData.furniture_type === 'other' && (
                              <>
                                <SelectItem value="other">Other</SelectItem>
                              </>
                            )}
                          </SelectContent>
                        </Select>
                      </div>
                    )}

                    <div>
                      <Label>Seating Capacity (if applicable)</Label>
                      <Select value={String(formData.seating_capacity)} onValueChange={(v) => setFormData({ ...formData, seating_capacity: parseInt(v) })}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0">N/A</SelectItem>
                          <SelectItem value="1">1 Seater</SelectItem>
                          <SelectItem value="2">2 Seater</SelectItem>
                          <SelectItem value="3">3 Seater</SelectItem>
                          <SelectItem value="4">4 Seater</SelectItem>
                          <SelectItem value="5">5 Seater</SelectItem>
                          <SelectItem value="6">6 Seater</SelectItem>
                          <SelectItem value="7">7 Seater</SelectItem>
                          <SelectItem value="8">8+ Seater</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Furniture Boolean Features */}
                    <div className="col-span-2 grid grid-cols-2 gap-3 mt-2">
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.is_antique}
                          onCheckedChange={(checked) => setFormData({ ...formData, is_antique: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">Antique</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.is_foldable}
                          onCheckedChange={(checked) => setFormData({ ...formData, is_foldable: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">Foldable</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.is_custom_made}
                          onCheckedChange={(checked) => setFormData({ ...formData, is_custom_made: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">Custom Made</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.has_storage}
                          onCheckedChange={(checked) => setFormData({ ...formData, has_storage: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">Has Storage</Label>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Step 3: AI Price Prediction */}
            <div className="space-y-4 border-t pt-6">
              <h3 className="text-lg font-semibold">🤖 Step 3: AI Price Prediction</h3>
              
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
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-green-900">AI Predicted Price:</span>
                        <span className="text-2xl font-bold text-green-700">
                          {formatCurrency(prediction.predicted_price)}
                        </span>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-sm text-green-800">
                          <TrendingUp className="h-4 w-4" />
                          <span>
                            Range: {formatCurrency(prediction.confidence_lower)} - 
                            {formatCurrency(prediction.confidence_upper)}
                          </span>
                        </div>
                        {prediction.confidence_score && (
                          <span className="text-sm font-medium text-green-700 bg-green-100 px-2 py-1 rounded">
                            {Math.round(prediction.confidence_score * 100)}% Confidence
                          </span>
                        )}
                      </div>

                      <div className="text-xs text-green-700">
                        <strong>Recommendation:</strong> {prediction.recommendation}
                      </div>
                      
                      {(!formData.ram || !formData.storage || !formData.camera) && formData.category === 'mobile' && (
                        <div className="text-xs text-green-600 italic mt-2">
                          💡 Tip: Adding RAM, Storage, and Camera specs can improve prediction accuracy
                        </div>
                      )}
                      {(!formData.processor || !formData.ram || !formData.storage) && formData.category === 'laptop' && (
                        <div className="text-xs text-green-600 italic mt-2">
                          💡 Tip: Adding Processor, RAM, and Storage specs can improve prediction accuracy
                        </div>
                      )}
                    </div>
                  </AlertDescription>
                </Alert>
              )}

              {predictionError && !predicting && (
                <Alert className="bg-amber-50 border-amber-300">
                  <AlertCircle className="h-4 w-4 text-amber-600" />
                  <AlertDescription className="text-amber-800 ml-2">
                    {typeof predictionError === 'string' ? predictionError : 'Unable to predict price. Please try again.'}
                  </AlertDescription>
                </Alert>
              )}

              {!titleValidation?.is_valid && formData.title && !predicting && (
                <Alert className="bg-red-50 border-red-300">
                  <XCircle className="h-4 w-4 text-red-600" />
                  <AlertTitle className="text-red-800">Invalid Title</AlertTitle>
                  <AlertDescription className="text-red-700 text-sm">
                    {titleValidation?.message || 'Please provide a valid title with brand and model information.'}
                  </AlertDescription>
                </Alert>
              )}

              {!prediction && !predicting && (() => {
                const missingFields = [];
                
                if (!formData.title) missingFields.push('Title with brand and model');
                else if (!titleValidation?.is_valid && formData.title) return null; // Error shown above
                
                if (!formData.brand && (formData.category === 'mobile' || formData.category === 'laptop')) {
                  missingFields.push('Brand from dropdown');
                }
                
                if (!formData.condition) missingFields.push('Condition');
                
                if (formData.category === 'furniture' && !formData.material) {
                  missingFields.push('Material');
                }
                
                if (missingFields.length > 0) {
                  return (
                    <Alert className="bg-blue-50 border-blue-300">
                      <Info className="h-4 w-4 text-blue-600" />
                      <AlertDescription className="text-blue-700">
                        <strong>Fill required fields to get AI price prediction:</strong>
                        <ul className="list-disc ml-5 mt-2 space-y-1">
                          {missingFields.map((field, idx) => (
                            <li key={idx} className="text-sm">{field}</li>
                          ))}
                        </ul>
                        {formData.category === 'mobile' && (
                          <p className="text-xs mt-3 italic text-blue-600">
                            💡 Optional: Add RAM, Storage, Camera for better accuracy
                          </p>
                        )}
                        {formData.category === 'laptop' && (
                          <p className="text-xs mt-3 italic text-blue-600">
                            💡 Optional: Add Processor, RAM, Storage, GPU for better accuracy
                          </p>
                        )}
                      </AlertDescription>
                    </Alert>
                  );
                }
                
                return null;
              })()}
            </div>

            {/* Step 4: Set Your Price */}
            <div className="space-y-4 border-t pt-6">
              <h3 className="text-lg font-semibold">💰 Step 4: Set Your Price</h3>
              
              <div className="space-y-2">
                <Label>Your Price (PKR) *</Label>
                <Input
                  type="number"
                  placeholder="Enter your asking price"
                  value={formData.price}
                  onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                  required
                />
                {prediction && (
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">
                      💡 Recommended: {formatCurrency(prediction.predicted_price)} 
                      (±{formatCurrency(prediction.predicted_price - prediction.confidence_lower)})
                    </p>
                    {prediction.allowed_price_min && prediction.allowed_price_max && (
                      <>
                        <p className="text-sm font-medium text-green-700">
                          ✅ Auto-Approval Range: {formatCurrency(prediction.allowed_price_min)} - {formatCurrency(prediction.allowed_price_max)}
                        </p>
                        {formData.price && (
                          Number(formData.price) < prediction.allowed_price_min || Number(formData.price) > prediction.allowed_price_max
                        ) && (
                          <p className="text-sm font-medium text-orange-600 bg-orange-50 p-2 rounded">
                            ⚠️ Price outside auto-approval range. Your listing will be sent for admin review.
                          </p>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
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
                  {editMode ? 'Updating Listing...' : 'Creating Listing...'}
                </>
              ) : (
                editMode ? 'Update Listing' : 'Create Listing'
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Success Preview Dialog */}
      <Dialog open={showPreviewDialog} onOpenChange={setShowPreviewDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-2xl">
              <PartyPopper className="h-6 w-6 text-green-600" />
              Ad Posted Successfully!
            </DialogTitle>
            <DialogDescription>
              Your listing has been created and is now live. Here's a preview:
            </DialogDescription>
          </DialogHeader>

          {createdListing && (
            <div className="space-y-4 mt-4">
              {/* Preview Card */}
              <Card className="border-2 border-green-200">
                <CardContent className="p-6">
                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Image */}
                    <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center">
                      {imagePreview ? (
                        <img
                          src={imagePreview}
                          alt={createdListing.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <span className="text-gray-400">No image</span>
                      )}
                    </div>

                    {/* Details */}
                    <div className="space-y-3">
                      <div>
                        <Badge className="mb-2">{createdListing.category}</Badge>
                        <h3 className="text-xl font-bold">{createdListing.title}</h3>
                        <p className="text-2xl font-bold text-green-600 mt-2">
                          Rs. {createdListing.price?.toLocaleString()}
                        </p>
                      </div>

                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Condition:</span>
                          <span className="font-medium capitalize">{createdListing.condition}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Location:</span>
                          <span className="font-medium">{createdListing.location}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Status:</span>
                          <Badge variant="outline" className="text-yellow-600 border-yellow-600">
                            {createdListing.status === 'approved' ? 'Live' : 'Pending Approval'}
                          </Badge>
                        </div>
                      </div>

                      <div className="pt-3 border-t">
                        <p className="text-sm text-gray-700 line-clamp-3">
                          {createdListing.description}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Success Message */}
                  <Alert className="mt-4 bg-green-50 border-green-200">
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                    <AlertTitle className="text-green-900">Listing Created!</AlertTitle>
                    <AlertDescription className="text-green-700">
                      Your ad is now {createdListing.status === 'approved' ? 'live and visible to buyers' : 'pending approval by admin'}. 
                      You can view it in your dashboard.
                    </AlertDescription>
                  </Alert>
                </CardContent>
              </Card>

              {/* Action Buttons */}
              <div className="flex gap-3">
                <Button
                  onClick={() => navigate(`/product/${createdListing.id}`)}
                  className="flex-1 bg-[#143109] hover:bg-[#AAAE7F]"
                >
                  <Eye className="mr-2 h-4 w-4" />
                  View Listing
                </Button>
                <Button
                  onClick={() => {
                    setShowPreviewDialog(false);
                    navigate('/dashboard');
                  }}
                  variant="outline"
                  className="flex-1"
                >
                  Go to Dashboard
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
