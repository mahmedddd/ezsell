/**
 * 🔮 AI-Powered Price Prediction Page
 * Features: Dropdown selections, NLP-based predictions, real-time estimates
 */

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Checkbox } from '@/components/ui/checkbox';
import { AlertCircle, TrendingUp, DollarSign, Sparkles } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface PredictionResult {
  predicted_price: number;
  confidence_score: number;
  price_range_min: number;
  price_range_max: number;
  currency: string;
  category: string;
  extracted_features: Record<string, any>;
}

interface PredictionOptions {
  brands?: string[];
  ram?: number[];
  storage?: number[];
  camera?: number[];
  battery?: number[];
  screen_size?: number[];
  processors?: string[];
  generation?: number[];
  gpu?: string[];
  materials?: string[];
  seating_capacity?: number[];
  length_cm?: number[];
  width_cm?: number[];
  height_cm?: number[];
  condition?: string[];
  age_months?: number[];
  boolean_features?: string[];
}

export default function PricePrediction() {
  const [activeTab, setActiveTab] = useState<'mobile' | 'laptop' | 'furniture'>('mobile');
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [options, setOptions] = useState<PredictionOptions>({});

  // Mobile form state
  const [mobileData, setMobileData] = useState({
    brand: '',
    ram: 8,
    storage: 128,
    camera: 0,
    battery: 0,
    screen_size: 0,
    condition: 'good',
    age_months: 12,
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
    gpu: 'None',
    screen_size: 15.6,
    condition: 'good',
    age_months: 12,
    has_ssd: true,
    is_gaming: false,
    is_touchscreen: false,
  });

  // Furniture form state
  const [furnitureData, setFurnitureData] = useState({
    material: '',
    seating_capacity: 0,
    length: 0,
    width: 0,
    height: 0,
    condition: 'good',
    is_imported: false,
    is_handmade: false,
    has_storage: false,
    is_modern: false,
    is_antique: false,
  });

  // Load dropdown options for a category
  const loadOptions = async (category: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/prediction-options/${category}`);
      if (response.ok) {
        const data = await response.json();
        setOptions(data);
      }
    } catch (err) {
      console.error('Error loading options:', err);
    }
  };

  // Handle tab change
  const handleTabChange = (value: string) => {
    setActiveTab(value as 'mobile' | 'laptop' | 'furniture');
    setPrediction(null);
    setError(null);
    loadOptions(value);
  };

  // Make prediction
  const handlePredict = async () => {
    setLoading(true);
    setError(null);
    setPrediction(null);

    try {
      let requestData: any = { category: activeTab };

      if (activeTab === 'mobile') {
        requestData = { ...requestData, ...mobileData };
      } else if (activeTab === 'laptop') {
        requestData = { ...requestData, ...laptopData };
      } else if (activeTab === 'furniture') {
        requestData = { ...requestData, ...furnitureData };
      }

      const response = await fetch('http://localhost:8000/api/v1/predict-price-with-dropdowns', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Prediction failed');
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
  useState(() => {
    loadOptions('mobile');
  });

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
            Get accurate price estimates using advanced machine learning
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Input Form */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Item Details</CardTitle>
                <CardDescription>
                  Select your item specifications to get an AI-powered price estimate
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs value={activeTab} onValueChange={handleTabChange}>
                  <TabsList className="grid w-full grid-cols-3 mb-6">
                    <TabsTrigger value="mobile">📱 Mobile</TabsTrigger>
                    <TabsTrigger value="laptop">💻 Laptop</TabsTrigger>
                    <TabsTrigger value="furniture">🛋️ Furniture</TabsTrigger>
                  </TabsList>

                  {/* Mobile Form */}
                  <TabsContent value="mobile" className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Brand</Label>
                        <Select value={mobileData.brand} onValueChange={(v) => setMobileData({ ...mobileData, brand: v })}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select brand" />
                          </SelectTrigger>
                          <SelectContent>
                            {options.brands?.map((brand) => (
                              <SelectItem key={brand} value={brand}>{brand}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Condition</Label>
                        <Select value={mobileData.condition} onValueChange={(v) => setMobileData({ ...mobileData, condition: v })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {options.condition?.map((cond) => (
                              <SelectItem key={cond} value={cond}>{cond.charAt(0).toUpperCase() + cond.slice(1)}</SelectItem>
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
                            {options.ram?.map((ram) => (
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
                            {options.storage?.map((storage) => (
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
                            {options.camera?.map((camera) => (
                              <SelectItem key={camera} value={String(camera)}>
                                {camera === 0 ? 'Unknown' : `${camera} MP`}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Battery (mAh)</Label>
                        <Select value={String(mobileData.battery)} onValueChange={(v) => setMobileData({ ...mobileData, battery: parseInt(v) })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {options.battery?.map((battery) => (
                              <SelectItem key={battery} value={String(battery)}>
                                {battery === 0 ? 'Unknown' : `${battery} mAh`}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Screen Size (inch)</Label>
                        <Select value={String(mobileData.screen_size)} onValueChange={(v) => setMobileData({ ...mobileData, screen_size: parseFloat(v) })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {options.screen_size?.map((size) => (
                              <SelectItem key={size} value={String(size)}>
                                {size === 0 ? 'Unknown' : `${size}"`}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Age (months)</Label>
                        <Select value={String(mobileData.age_months)} onValueChange={(v) => setMobileData({ ...mobileData, age_months: parseInt(v) })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {options.age_months?.map((age) => (
                              <SelectItem key={age} value={String(age)}>
                                {age === 0 ? 'Brand New' : `${age} months`}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 pt-4">
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={mobileData.has_5g}
                          onCheckedChange={(checked) => setMobileData({ ...mobileData, has_5g: checked as boolean })}
                        />
                        <Label>5G Support</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={mobileData.has_pta}
                          onCheckedChange={(checked) => setMobileData({ ...mobileData, has_pta: checked as boolean })}
                        />
                        <Label>PTA Approved</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={mobileData.has_amoled}
                          onCheckedChange={(checked) => setMobileData({ ...mobileData, has_amoled: checked as boolean })}
                        />
                        <Label>AMOLED Display</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={mobileData.has_warranty}
                          onCheckedChange={(checked) => setMobileData({ ...mobileData, has_warranty: checked as boolean })}
                        />
                        <Label>Warranty</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={mobileData.has_box}
                          onCheckedChange={(checked) => setMobileData({ ...mobileData, has_box: checked as boolean })}
                        />
                        <Label>Original Box</Label>
                      </div>
                    </div>

                    <Button onClick={handlePredict} disabled={loading || !mobileData.brand} className="w-full mt-4">
                      {loading ? 'Calculating...' : 'Predict Price'}
                    </Button>
                  </TabsContent>

                  {/* Laptop Form */}
                  <TabsContent value="laptop" className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Brand</Label>
                        <Select value={laptopData.brand} onValueChange={(v) => setLaptopData({ ...laptopData, brand: v })}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select brand" />
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
                            {options.generation?.map((gen) => (
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
                            {options.ram?.map((ram) => (
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
                            {options.storage?.map((storage) => (
                              <SelectItem key={storage} value={String(storage)}>{storage} GB</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>GPU</Label>
                        <Select value={laptopData.gpu} onValueChange={(v) => setLaptopData({ ...laptopData, gpu: v })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {options.gpu?.map((gpu) => (
                              <SelectItem key={gpu} value={gpu}>{gpu}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Screen Size</Label>
                        <Select value={String(laptopData.screen_size)} onValueChange={(v) => setLaptopData({ ...laptopData, screen_size: parseFloat(v) })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {options.screen_size?.map((size) => (
                              <SelectItem key={size} value={String(size)}>{size}"</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Condition</Label>
                        <Select value={laptopData.condition} onValueChange={(v) => setLaptopData({ ...laptopData, condition: v })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {options.condition?.map((cond) => (
                              <SelectItem key={cond} value={cond}>{cond.charAt(0).toUpperCase() + cond.slice(1)}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="col-span-2">
                        <Label>Age (months)</Label>
                        <Select value={String(laptopData.age_months)} onValueChange={(v) => setLaptopData({ ...laptopData, age_months: parseInt(v) })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {options.age_months?.map((age) => (
                              <SelectItem key={age} value={String(age)}>
                                {age === 0 ? 'Brand New' : `${age} months`}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4 pt-4">
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={laptopData.has_ssd}
                          onCheckedChange={(checked) => setLaptopData({ ...laptopData, has_ssd: checked as boolean })}
                        />
                        <Label>SSD Storage</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={laptopData.is_gaming}
                          onCheckedChange={(checked) => setLaptopData({ ...laptopData, is_gaming: checked as boolean })}
                        />
                        <Label>Gaming Laptop</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={laptopData.is_touchscreen}
                          onCheckedChange={(checked) => setLaptopData({ ...laptopData, is_touchscreen: checked as boolean })}
                        />
                        <Label>Touchscreen</Label>
                      </div>
                    </div>

                    <Button onClick={handlePredict} disabled={loading || !laptopData.brand || !laptopData.processor} className="w-full mt-4">
                      {loading ? 'Calculating...' : 'Predict Price'}
                    </Button>
                  </TabsContent>

                  {/* Furniture Form */}
                  <TabsContent value="furniture" className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Material</Label>
                        <Select value={furnitureData.material} onValueChange={(v) => setFurnitureData({ ...furnitureData, material: v })}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select material" />
                          </SelectTrigger>
                          <SelectContent>
                            {options.materials?.map((material) => (
                              <SelectItem key={material} value={material}>{material}</SelectItem>
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
                            {options.seating_capacity?.map((seats) => (
                              <SelectItem key={seats} value={String(seats)}>
                                {seats === 0 ? 'Not Applicable' : `${seats} Seater`}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Length (cm)</Label>
                        <Select value={String(furnitureData.length)} onValueChange={(v) => setFurnitureData({ ...furnitureData, length: parseInt(v) })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {options.length_cm?.map((len) => (
                              <SelectItem key={len} value={String(len)}>{len} cm</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Width (cm)</Label>
                        <Select value={String(furnitureData.width)} onValueChange={(v) => setFurnitureData({ ...furnitureData, width: parseInt(v) })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {options.width_cm?.map((w) => (
                              <SelectItem key={w} value={String(w)}>{w} cm</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Height (cm)</Label>
                        <Select value={String(furnitureData.height)} onValueChange={(v) => setFurnitureData({ ...furnitureData, height: parseInt(v) })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {options.height_cm?.map((h) => (
                              <SelectItem key={h} value={String(h)}>{h} cm</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Condition</Label>
                        <Select value={furnitureData.condition} onValueChange={(v) => setFurnitureData({ ...furnitureData, condition: v })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {options.condition?.map((cond) => (
                              <SelectItem key={cond} value={cond}>{cond.charAt(0).toUpperCase() + cond.slice(1)}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 pt-4">
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={furnitureData.is_imported}
                          onCheckedChange={(checked) => setFurnitureData({ ...furnitureData, is_imported: checked as boolean })}
                        />
                        <Label>Imported</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={furnitureData.is_handmade}
                          onCheckedChange={(checked) => setFurnitureData({ ...furnitureData, is_handmade: checked as boolean })}
                        />
                        <Label>Handmade</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={furnitureData.has_storage}
                          onCheckedChange={(checked) => setFurnitureData({ ...furnitureData, has_storage: checked as boolean })}
                        />
                        <Label>Has Storage</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={furnitureData.is_modern}
                          onCheckedChange={(checked) => setFurnitureData({ ...furnitureData, is_modern: checked as boolean })}
                        />
                        <Label>Modern Design</Label>
                      </div>
                      <div className="flex items-center space-x-2 col-span-2">
                        <Checkbox
                          checked={furnitureData.is_antique}
                          onCheckedChange={(checked) => setFurnitureData({ ...furnitureData, is_antique: checked as boolean })}
                        />
                        <Label>Antique/Vintage</Label>
                      </div>
                    </div>

                    <Button onClick={handlePredict} disabled={loading || !furnitureData.material} className="w-full mt-4">
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
                      Confidence: {(prediction.confidence_score * 100).toFixed(1)}%
                    </div>
                    <div className="bg-white/60 rounded-lg p-3">
                      <div className="text-sm font-medium mb-1">Price Range</div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-green-600">{formatCurrency(prediction.price_range_min)}</span>
                        <TrendingUp className="h-4 w-4 text-gray-400" />
                        <span className="text-red-600">{formatCurrency(prediction.price_range_max)}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Extracted Features</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      {Object.entries(prediction.extracted_features).slice(0, 8).map(([key, value]) => (
                        <div key={key} className="flex justify-between">
                          <span className="text-muted-foreground capitalize">
                            {key.replace(/_/g, ' ')}:
                          </span>
                          <span className="font-medium">
                            {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}
                          </span>
                        </div>
                      ))}
                    </div>
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
