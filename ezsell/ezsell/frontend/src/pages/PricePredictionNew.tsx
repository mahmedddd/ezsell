/**
 * 🔮 AI-Powered Price Prediction Page with Title Validation
 * Features: Dropdown selections, strict title validation, NLP-based predictions
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Checkbox } from '@/components/ui/checkbox';
import { AlertCircle, TrendingUp, DollarSign, Sparkles, CheckCircle2, XCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

interface PredictionResult {
  predicted_price: number;
  confidence_lower: number;
  confidence_upper: number;
  model_confidence: number;
  category: string;
  message: string;
  recommendation: string;
}

interface DropdownOptions {
  condition?: string[];
  brands?: string[];
  ram_options?: number[];
  storage_options?: number[];
  camera_options?: number[];
  battery_options?: number[];
  screen_size_options?: number[];
  processors?: string[];
  generation_options?: number[];
  gpu_options?: string[];
  materials?: string[];
  furniture_types?: string[];
  seating_capacity_options?: number[];
  boolean_features?: Record<string, string>;
}

interface ValidationResult {
  is_valid: boolean;
  message: string;
  extracted_info?: any;
  hints?: {
    required: string[];
    recommended: string[];
    example: string;
  };
}

export default function PricePredictionNew() {
  const [activeTab, setActiveTab] = useState<'mobile' | 'laptop' | 'furniture'>('mobile');
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [options, setOptions] = useState<DropdownOptions>({});
  const [titleValidation, setTitleValidation] = useState<ValidationResult | null>(null);
  const [validatingTitle, setValidatingTitle] = useState(false);

  // Common form fields
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [condition, setCondition] = useState<string>('used');

  // Mobile form state
  const [mobileData, setMobileData] = useState({
    brand: '',
    ram: 8,
    storage: 128,
    camera: 0,
    battery: 0,
    screen_size: 0,
    has_5g: false,
    has_pta: false,
    has_amoled: false,
    has_warranty: false,
    has_box: false,
  });

  // Laptop form state
  const [laptopData, setLaptopData] = useState({
    brand: '',
    processor: '',
    generation: 10,
    ram: 8,
    storage: 512,
    gpu: '',
    screen_size: 15.6,
    has_ssd: true,
    is_gaming: false,
    is_touchscreen: false,
    has_backlit_keyboard: false,
  });

  // Furniture form state
  const [furnitureData, setFurnitureData] = useState({
    material: '',
    furniture_type: '',
    seating_capacity: 0,
    length: 0,
    width: 0,
    height: 0,
    is_imported: false,
    is_handmade: false,
    has_storage: false,
    is_modern: false,
    is_antique: false,
  });

  // Load dropdown options for a category
  const loadOptions = async (category: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/dropdown-options/${category}`);
      if (response.ok) {
        const data = await response.json();
        setOptions(data);
      }
    } catch (err) {
      console.error('Error loading options:', err);
    }
  };

  // Validate title in real-time
  const validateTitle = async (category: string, titleText: string, descText: string = '', material: string = '') => {
    if (!titleText || titleText.length < 5) {
      setTitleValidation(null);
      return;
    }

    setValidatingTitle(true);
    try {
      const params = new URLSearchParams({
        category,
        title: titleText,
        description: descText,
        material: material
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

  // Handle tab change
  const handleTabChange = (value: string) => {
    setActiveTab(value as 'mobile' | 'laptop' | 'furniture');
    setPrediction(null);
    setError(null);
    setTitleValidation(null);
    setTitle('');
    setDescription('');
    setCondition('used');
    loadOptions(value);
  };

  // Handle title change with debounced validation
  useEffect(() => {
    const timer = setTimeout(() => {
      if (title) {
        const material = activeTab === 'furniture' ? furnitureData.material : '';
        validateTitle(activeTab, title, description, material);
      }
    }, 800);

    return () => clearTimeout(timer);
  }, [title, description, furnitureData.material, activeTab]);

  // Make prediction
  const handlePredict = async () => {
    // Check title validation first
    if (!titleValidation || !titleValidation.is_valid) {
      setError('Please provide a valid title with relevant product information');
      return;
    }

    setLoading(true);
    setError(null);
    setPrediction(null);

    try {
      let requestData: any = {
        category: activeTab,
        title: title,
        description: description,
        condition: condition
      };

      if (activeTab === 'mobile') {
        requestData = { ...requestData, ...mobileData };
      } else if (activeTab === 'laptop') {
        requestData = { ...requestData, ...laptopData };
      } else if (activeTab === 'furniture') {
        requestData = { ...requestData, ...furnitureData };
      }

      const response = await fetch('http://localhost:8000/api/v1/predict-price', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.message || errorData.detail || 'Prediction failed');
      }

      const result = await response.json();
      setPrediction(result);
    } catch (err: any) {
      setError(err.message || 'Failed to predict price');
    } finally {
      setLoading(false);
    }
  };

  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-PK', {
      style: 'currency',
      currency: 'PKR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  // Load initial options
  useEffect(() => {
    loadOptions('mobile');
  }, []);

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2 flex items-center justify-center gap-2">
            <Sparkles className="h-8 w-8 text-blue-500" />
            AI-Powered Price Prediction
          </h1>
          <p className="text-muted-foreground">
            Get accurate price estimates using advanced machine learning with strict validation
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Input Form */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Item Details</CardTitle>
                <CardDescription>
                  Provide detailed product information. Title must include brand/model information.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs value={activeTab} onValueChange={handleTabChange}>
                  <TabsList className="grid w-full grid-cols-3 mb-6">
                    <TabsTrigger value="mobile">📱 Mobile</TabsTrigger>
                    <TabsTrigger value="laptop">💻 Laptop</TabsTrigger>
                    <TabsTrigger value="furniture">🛋️ Furniture</TabsTrigger>
                  </TabsList>

                  {/* Common Fields for All Categories */}
                  <div className="space-y-4 mb-6">
                    <div>
                      <Label>Title *</Label>
                      <Input
                        placeholder={
                          activeTab === 'mobile'
                            ? 'e.g., Samsung Galaxy S23 Ultra 12GB RAM 256GB'
                            : activeTab === 'laptop'
                            ? 'e.g., Dell XPS 15 Intel Core i7 12th Gen 16GB RAM'
                            : 'e.g., Modern 5 Seater L-Shape Sofa - Premium Fabric'
                        }
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        className={
                          titleValidation
                            ? titleValidation.is_valid
                              ? 'border-green-500'
                              : 'border-red-500'
                            : ''
                        }
                      />
                      {validatingTitle && (
                        <p className="text-sm text-muted-foreground mt-1">Validating...</p>
                      )}
                      {titleValidation && !validatingTitle && (
                        <div className={`flex items-start gap-2 mt-2 p-2 rounded ${
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

                    <div>
                      <Label>Description *</Label>
                      <Textarea
                        placeholder="Detailed product description with specifications, condition, and any additional features..."
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        rows={3}
                      />
                    </div>

                    <div>
                      <Label>Condition *</Label>
                      <Select value={condition} onValueChange={setCondition}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {options.condition?.map((cond) => (
                            <SelectItem key={cond} value={cond}>
                              {cond.charAt(0).toUpperCase() + cond.slice(1)}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {/* Mobile Form */}
                  <TabsContent value="mobile" className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Brand (Optional)</Label>
                        <Select value={mobileData.brand} onValueChange={(v) => setMobileData({ ...mobileData, brand: v })}>
                          <SelectTrigger>
                            <SelectValue placeholder="Auto-detected from title" />
                          </SelectTrigger>
                          <SelectContent>
                            {options.brands?.map((brand) => (
                              <SelectItem key={brand} value={brand}>{brand}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>RAM (GB)</Label>
                        <Select value={String(mobileData.ram)} onValueChange={(v) => setMobileData({ ...mobileData, ram: parseInt(v) })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {options.ram_options?.map((ram) => (
                              <SelectItem key={ram} value={String(ram)}>{ram} GB</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Storage (GB)</Label>
                        <Select value={String(mobileData.storage)} onValueChange={(v) => setMobileData({ ...mobileData, storage: parseInt(v) })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {options.storage_options?.map((storage) => (
                              <SelectItem key={storage} value={String(storage)}>{storage} GB</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Camera (MP)</Label>
                        <Select value={String(mobileData.camera)} onValueChange={(v) => setMobileData({ ...mobileData, camera: parseInt(v) })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {options.camera_options?.map((camera) => (
                              <SelectItem key={camera} value={String(camera)}>
                                {camera === 0 ? 'Unknown' : `${camera} MP`}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 mt-4">
                      {Object.entries(options.boolean_features || {}).map(([key, label]) => (
                        <div key={key} className="flex items-center space-x-2">
                          <Checkbox
                            checked={(mobileData as any)[key] || false}
                            onCheckedChange={(checked) => setMobileData({ ...mobileData, [key]: checked as boolean })}
                          />
                          <Label>{label}</Label>
                        </div>
                      ))}
                    </div>

                    <Button
                      onClick={handlePredict}
                      disabled={loading || !title || !description || !titleValidation?.is_valid}
                      className="w-full mt-4"
                    >
                      {loading ? 'Calculating...' : 'Predict Price'}
                    </Button>
                  </TabsContent>

                  {/* Laptop Form */}
                  <TabsContent value="laptop" className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Brand (Optional)</Label>
                        <Select value={laptopData.brand} onValueChange={(v) => setLaptopData({ ...laptopData, brand: v })}>
                          <SelectTrigger>
                            <SelectValue placeholder="Auto-detected from title" />
                          </SelectTrigger>
                          <SelectContent>
                            {options.brands?.map((brand) => (
                              <SelectItem key={brand} value={brand}>{brand}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Processor</Label>
                        <Select value={laptopData.processor} onValueChange={(v) => setLaptopData({ ...laptopData, processor: v })}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select processor" />
                          </SelectTrigger>
                          <SelectContent>
                            {options.processors?.map((proc) => (
                              <SelectItem key={proc} value={proc}>{proc}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Generation</Label>
                        <Select value={String(laptopData.generation)} onValueChange={(v) => setLaptopData({ ...laptopData, generation: parseInt(v) })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {options.generation_options?.map((gen) => (
                              <SelectItem key={gen} value={String(gen)}>{gen}th Gen</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>RAM (GB)</Label>
                        <Select value={String(laptopData.ram)} onValueChange={(v) => setLaptopData({ ...laptopData, ram: parseInt(v) })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {options.ram_options?.map((ram) => (
                              <SelectItem key={ram} value={String(ram)}>{ram} GB</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Storage (GB)</Label>
                        <Select value={String(laptopData.storage)} onValueChange={(v) => setLaptopData({ ...laptopData, storage: parseInt(v) })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {options.storage_options?.map((storage) => (
                              <SelectItem key={storage} value={String(storage)}>{storage} GB</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>GPU</Label>
                        <Select value={laptopData.gpu} onValueChange={(v) => setLaptopData({ ...laptopData, gpu: v })}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select GPU" />
                          </SelectTrigger>
                          <SelectContent>
                            {options.gpu_options?.map((gpu) => (
                              <SelectItem key={gpu} value={gpu}>{gpu}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 mt-4">
                      {Object.entries(options.boolean_features || {}).map(([key, label]) => (
                        <div key={key} className="flex items-center space-x-2">
                          <Checkbox
                            checked={(laptopData as any)[key] || false}
                            onCheckedChange={(checked) => setLaptopData({ ...laptopData, [key]: checked as boolean })}
                          />
                          <Label>{label}</Label>
                        </div>
                      ))}
                    </div>

                    <Button
                      onClick={handlePredict}
                      disabled={loading || !title || !description || !titleValidation?.is_valid}
                      className="w-full mt-4"
                    >
                      {loading ? 'Calculating...' : 'Predict Price'}
                    </Button>
                  </TabsContent>

                  {/* Furniture Form */}
                  <TabsContent value="furniture" className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Material *</Label>
                        <Select value={furnitureData.material} onValueChange={(v) => setFurnitureData({ ...furnitureData, material: v })}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select material" />
                          </SelectTrigger>
                          <SelectContent>
                            {options.materials?.map((mat) => (
                              <SelectItem key={mat} value={mat}>{mat}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Furniture Type (Optional)</Label>
                        <Select value={furnitureData.furniture_type} onValueChange={(v) => setFurnitureData({ ...furnitureData, furniture_type: v })}>
                          <SelectTrigger>
                            <SelectValue placeholder="Auto-detected from title" />
                          </SelectTrigger>
                          <SelectContent>
                            {options.furniture_types?.map((type) => (
                              <SelectItem key={type} value={type}>{type}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Seating Capacity</Label>
                        <Select value={String(furnitureData.seating_capacity)} onValueChange={(v) => setFurnitureData({ ...furnitureData, seating_capacity: parseInt(v) })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {options.seating_capacity_options?.map((capacity) => (
                              <SelectItem key={capacity} value={String(capacity)}>
                                {capacity === 0 ? 'N/A' : `${capacity} Seater`}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 mt-4">
                      {Object.entries(options.boolean_features || {}).map(([key, label]) => (
                        <div key={key} className="flex items-center space-x-2">
                          <Checkbox
                            checked={(furnitureData as any)[key] || false}
                            onCheckedChange={(checked) => setFurnitureData({ ...furnitureData, [key]: checked as boolean })}
                          />
                          <Label>{label}</Label>
                        </div>
                      ))}
                    </div>

                    <Button
                      onClick={handlePredict}
                      disabled={loading || !title || !description || !furnitureData.material || !titleValidation?.is_valid}
                      className="w-full mt-4"
                    >
                      {loading ? 'Calculating...' : 'Predict Price'}
                    </Button>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>

          {/* Results Panel */}
          <div>
            {error && (
              <Alert variant="destructive" className="mb-4">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {prediction && (
              <div className="space-y-4">
                <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <DollarSign className="h-5 w-5 text-blue-600" />
                      Predicted Price
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-4xl font-bold text-blue-600 mb-2">
                      {formatCurrency(prediction.predicted_price)}
                    </div>
                    <div className="text-sm text-muted-foreground mb-4">
                      Model Confidence: {prediction.model_confidence.toFixed(1)}%
                    </div>
                    <div className="bg-white/60 rounded-lg p-3">
                      <div className="text-sm font-medium mb-1">Price Range</div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-green-600">{formatCurrency(prediction.confidence_lower)}</span>
                        <TrendingUp className="h-4 w-4 text-gray-400" />
                        <span className="text-red-600">{formatCurrency(prediction.confidence_upper)}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Recommendation</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">{prediction.recommendation}</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Model Information</CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm space-y-1">
                    <p><span className="font-medium">Category:</span> {prediction.category}</p>
                    <p className="text-muted-foreground">{prediction.message}</p>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
