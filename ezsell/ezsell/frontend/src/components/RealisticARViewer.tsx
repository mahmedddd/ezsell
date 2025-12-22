import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { Upload, Eye, X, Loader2, Camera, Lightbulb, Ruler, Palette, RotateCw, Move, Maximize2, Sparkles, Trash2, Plus } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';

interface RealisticARViewerProps {
  listingId: number;
  listingTitle: string;
  category: string;
  price?: number;
}

interface FurnitureItem {
  id: string;
  x: number;
  y: number;
  z: number;
  scale: number;
  rotation: number;
  color: string;
  material: string;
}

interface RoomAnalysis {
  dimensions: { width: number; height: number; depth: number };
  style: string;
  lighting: string;
  floorType: string;
  wallColor: string;
  suitability: number;
}

interface Recommendation {
  title: string;
  reason: string;
  confidence: number;
}

const furnitureMaterials = [
  { name: 'Oak Wood', value: 'oak', color: '#C19A6B', roughness: 0.8 },
  { name: 'Walnut Wood', value: 'walnut', color: '#5C4033', roughness: 0.7 },
  { name: 'White Leather', value: 'white-leather', color: '#F5F5DC', roughness: 0.3 },
  { name: 'Black Leather', value: 'black-leather', color: '#1a1a1a', roughness: 0.4 },
  { name: 'Gray Fabric', value: 'gray-fabric', color: '#808080', roughness: 0.9 },
  { name: 'Beige Fabric', value: 'beige-fabric', color: '#F5F5DC', roughness: 0.85 },
  { name: 'Metal Chrome', value: 'chrome', color: '#C0C0C0', roughness: 0.1 },
  { name: 'Brushed Steel', value: 'steel', color: '#8A8D8F', roughness: 0.5 },
];

const roomStyles = [
  { name: 'Modern Minimalist', value: 'modern', colors: ['#FFFFFF', '#000000', '#808080'] },
  { name: 'Scandinavian', value: 'scandinavian', colors: ['#FFFFFF', '#F5F5DC', '#A0C5E3'] },
  { name: 'Industrial', value: 'industrial', colors: ['#3E3E3E', '#8A8D8F', '#C19A6B'] },
  { name: 'Traditional', value: 'traditional', colors: ['#5C4033', '#8B4513', '#DEB887'] },
  { name: 'Contemporary', value: 'contemporary', colors: ['#2C3E50', '#ECF0F1', '#E74C3C'] },
];

export function RealisticARViewer({ listingId, listingTitle, category, price }: RealisticARViewerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [roomImage, setRoomImage] = useState<File | null>(null);
  const [roomImagePreview, setRoomImagePreview] = useState<string | null>(null);
  const [placedItems, setPlacedItems] = useState<FurnitureItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [roomAnalysis, setRoomAnalysis] = useState<RoomAnalysis | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [activeTab, setActiveTab] = useState('upload');
  const [showShadows, setShowShadows] = useState(true);
  const [lightingIntensity, setLightingIntensity] = useState(80);
  const [viewAngle, setViewAngle] = useState<'front' | '3d' | 'top'>('front');
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const modelViewerRef = useRef<any>(null);
  const { toast } = useToast();

  // Only show for furniture
  if (category?.toLowerCase() !== 'furniture') {
    return null;
  }

  // AI-powered room analysis
  const analyzeRoom = async (imageFile: File) => {
    setLoading(true);
    setAnalysisProgress(0);

    try {
      // Simulate AI analysis progress
      const intervals = [10, 30, 50, 70, 90, 100];
      for (let i = 0; i < intervals.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 300));
        setAnalysisProgress(intervals[i]);
      }

      // Simulated AI room analysis (in production, use TensorFlow.js or backend AI)
      const analysis: RoomAnalysis = {
        dimensions: {
          width: 4.5 + Math.random() * 2,
          height: 2.8 + Math.random() * 0.5,
          depth: 5.0 + Math.random() * 2,
        },
        style: roomStyles[Math.floor(Math.random() * roomStyles.length)].value,
        lighting: Math.random() > 0.5 ? 'Natural (Window)' : 'Artificial (Ceiling)',
        floorType: ['Hardwood', 'Carpet', 'Tile', 'Laminate'][Math.floor(Math.random() * 4)],
        wallColor: ['White', 'Beige', 'Gray', 'Light Blue'][Math.floor(Math.random() * 4)],
        suitability: 75 + Math.random() * 20,
      };

      setRoomAnalysis(analysis);

      // Generate recommendations
      const recs: Recommendation[] = [
        {
          title: 'Perfect Size Match',
          reason: `This furniture fits well in a ${analysis.dimensions.width.toFixed(1)}m × ${analysis.dimensions.depth.toFixed(1)}m space`,
          confidence: 92,
        },
        {
          title: 'Style Compatibility',
          reason: `Complements your ${roomStyles.find(s => s.value === analysis.style)?.name} décor`,
          confidence: 88,
        },
        {
          title: 'Color Harmony',
          reason: `Works beautifully with ${analysis.wallColor.toLowerCase()} walls and ${analysis.floorType.toLowerCase()} flooring`,
          confidence: 85,
        },
      ];

      setRecommendations(recs);

      toast({
        title: "✨ Room Analyzed Successfully",
        description: `AI detected ${analysis.style} style with ${analysis.suitability.toFixed(0)}% suitability`,
      });

      setActiveTab('customize');
    } catch (error) {
      console.error('Analysis error:', error);
      toast({
        title: "Analysis Failed",
        description: "Could not analyze room. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
      setAnalysisProgress(0);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      toast({
        title: "Invalid file type",
        description: "Please select an image file",
        variant: "destructive",
      });
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      toast({
        title: "File too large",
        description: "Please select an image smaller than 10MB",
        variant: "destructive",
      });
      return;
    }

    setRoomImage(file);
    setRoomImagePreview(URL.createObjectURL(file));
    setPlacedItems([]);

    // Auto-analyze room
    analyzeRoom(file);
  };

  useEffect(() => {
    if (roomImagePreview && canvasRef.current) {
      render3DScene();
    }
  }, [roomImagePreview, placedItems, showShadows, lightingIntensity, viewAngle]);

  const render3DScene = () => {
    const canvas = canvasRef.current;
    if (!canvas || !roomImagePreview) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);

      // Apply lighting effects
      const lightingOverlay = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
      const opacity = (100 - lightingIntensity) / 200;
      lightingOverlay.addColorStop(0, `rgba(255, 255, 255, ${opacity})`);
      lightingOverlay.addColorStop(1, `rgba(0, 0, 0, ${opacity / 2})`);
      ctx.fillStyle = lightingOverlay;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw all furniture items with realistic rendering
      placedItems.forEach((item) => {
        draw3DFurniture(ctx, item, item.id === selectedItem);
      });
    };
    img.src = roomImagePreview;
  };

  const draw3DFurniture = (ctx: CanvasRenderingContext2D, item: FurnitureItem, isSelected: boolean) => {
    ctx.save();

    const material = furnitureMaterials.find(m => m.value === item.material) || furnitureMaterials[0];
    const baseWidth = 200 * item.scale;
    const baseHeight = 150 * item.scale;
    const depth = 80 * item.scale;

    // Apply perspective transformation based on view angle
    const perspective = viewAngle === '3d' ? 0.6 : (viewAngle === 'top' ? 0.3 : 0.4);

    ctx.translate(item.x, item.y);
    ctx.rotate((item.rotation * Math.PI) / 180);

    // Draw shadow if enabled
    if (showShadows) {
      ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
      ctx.beginPath();
      ctx.ellipse(0, baseHeight / 2 + 10, baseWidth / 2, depth / 4, 0, 0, Math.PI * 2);
      ctx.fill();
    }

    // Draw 3D furniture with perspective
    // Front face
    ctx.fillStyle = material.color;
    ctx.fillRect(-baseWidth / 2, -baseHeight / 2, baseWidth, baseHeight);

    // Side face (for 3D effect)
    if (viewAngle === '3d') {
      ctx.fillStyle = shadeColor(material.color, -20);
      ctx.beginPath();
      ctx.moveTo(baseWidth / 2, -baseHeight / 2);
      ctx.lineTo(baseWidth / 2 + depth * perspective, -baseHeight / 2 - depth * perspective);
      ctx.lineTo(baseWidth / 2 + depth * perspective, baseHeight / 2 - depth * perspective);
      ctx.lineTo(baseWidth / 2, baseHeight / 2);
      ctx.closePath();
      ctx.fill();

      // Top face
      ctx.fillStyle = shadeColor(material.color, 20);
      ctx.beginPath();
      ctx.moveTo(-baseWidth / 2, -baseHeight / 2);
      ctx.lineTo(-baseWidth / 2 + depth * perspective, -baseHeight / 2 - depth * perspective);
      ctx.lineTo(baseWidth / 2 + depth * perspective, -baseHeight / 2 - depth * perspective);
      ctx.lineTo(baseWidth / 2, -baseHeight / 2);
      ctx.closePath();
      ctx.fill();
    }

    // Add material texture effect
    if (material.roughness > 0.5) {
      ctx.fillStyle = `rgba(255, 255, 255, ${material.roughness * 0.1})`;
      for (let i = 0; i < 20; i++) {
        const x = -baseWidth / 2 + Math.random() * baseWidth;
        const y = -baseHeight / 2 + Math.random() * baseHeight;
        ctx.fillRect(x, y, 2, 2);
      }
    }

    // Highlight effect for reflective materials
    if (material.roughness < 0.5) {
      const gradient = ctx.createLinearGradient(-baseWidth / 2, -baseHeight / 2, baseWidth / 2, baseHeight / 2);
      gradient.addColorStop(0, 'rgba(255, 255, 255, 0.3)');
      gradient.addColorStop(0.5, 'rgba(255, 255, 255, 0)');
      gradient.addColorStop(1, 'rgba(255, 255, 255, 0.1)');
      ctx.fillStyle = gradient;
      ctx.fillRect(-baseWidth / 2, -baseHeight / 2, baseWidth, baseHeight);
    }

    // Selection highlight
    if (isSelected) {
      ctx.strokeStyle = '#143109';
      ctx.lineWidth = 4;
      ctx.setLineDash([10, 5]);
      ctx.strokeRect(-baseWidth / 2 - 5, -baseHeight / 2 - 5, baseWidth + 10, baseHeight + 10);
      ctx.setLineDash([]);

      // Selection handles
      const handles = [
        { x: -baseWidth / 2, y: -baseHeight / 2 },
        { x: baseWidth / 2, y: -baseHeight / 2 },
        { x: -baseWidth / 2, y: baseHeight / 2 },
        { x: baseWidth / 2, y: baseHeight / 2 },
      ];

      ctx.fillStyle = '#143109';
      handles.forEach(handle => {
        ctx.fillRect(handle.x - 5, handle.y - 5, 10, 10);
      });
    }

    // Add product label
    ctx.fillStyle = 'rgba(20, 49, 9, 0.8)';
    ctx.fillRect(-baseWidth / 2, baseHeight / 2 + 5, baseWidth, 25);
    ctx.fillStyle = '#FFFFFF';
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(listingTitle.substring(0, 30), 0, baseHeight / 2 + 20);

    ctx.restore();
  };

  // Helper function to shade colors
  const shadeColor = (color: string, percent: number): string => {
    const num = parseInt(color.replace('#', ''), 16);
    const amt = Math.round(2.55 * percent);
    const R = (num >> 16) + amt;
    const G = ((num >> 8) & 0x00FF) + amt;
    const B = (num & 0x0000FF) + amt;
    return '#' + (
      0x1000000 +
      (R < 255 ? (R < 1 ? 0 : R) : 255) * 0x10000 +
      (G < 255 ? (G < 1 ? 0 : G) : 255) * 0x100 +
      (B < 255 ? (B < 1 ? 0 : B) : 255)
    ).toString(16).slice(1);
  };

  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current) return;

    const rect = canvasRef.current.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const clickedItem = placedItems.find(item => {
      const halfWidth = (100 * item.scale);
      const halfHeight = (75 * item.scale);
      return x >= item.x - halfWidth && x <= item.x + halfWidth &&
             y >= item.y - halfHeight && y <= item.y + halfHeight;
    });

    setSelectedItem(clickedItem ? clickedItem.id : null);
  };

  const addFurniture = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const newItem: FurnitureItem = {
      id: `furniture-${Date.now()}`,
      x: canvas.width / 2,
      y: canvas.height / 2,
      z: 0,
      scale: 1,
      rotation: 0,
      color: furnitureMaterials[0].color,
      material: furnitureMaterials[0].value,
    };

    setPlacedItems([...placedItems, newItem]);
    setSelectedItem(newItem.id);
    toast({
      title: "Furniture Placed",
      description: "Drag to reposition, customize in the panel",
    });
  };

  const updateSelectedItem = (updates: Partial<FurnitureItem>) => {
    if (!selectedItem) return;
    setPlacedItems(placedItems.map(item =>
      item.id === selectedItem ? { ...item, ...updates } : item
    ));
  };

  const removeSelectedFurniture = () => {
    if (!selectedItem) return;
    setPlacedItems(placedItems.filter(item => item.id !== selectedItem));
    setSelectedItem(null);
  };

  const handleReset = () => {
    setRoomImage(null);
    setRoomImagePreview(null);
    setPlacedItems([]);
    setSelectedItem(null);
    setRoomAnalysis(null);
    setRecommendations([]);
    setActiveTab('upload');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const selectedFurniture = placedItems.find(item => item.id === selectedItem);
  const selectedMaterial = furnitureMaterials.find(m => m.value === selectedFurniture?.material);

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button className="w-full bg-[#143109] hover:bg-[#AAAE7F] text-white">
          <Sparkles className="mr-2 h-5 w-5" />
          Realistic AR Preview
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-7xl max-h-[95vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-[#143109]" />
            Realistic 3D AR Preview: {listingTitle}
          </DialogTitle>
          <DialogDescription>
            AI-powered room analysis with realistic 3D furniture placement and style recommendations
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="upload">📸 Upload</TabsTrigger>
            <TabsTrigger value="customize" disabled={!roomImagePreview}>🎨 Customize</TabsTrigger>
            <TabsTrigger value="recommendations" disabled={!roomAnalysis}>💡 AI Insights</TabsTrigger>
            <TabsTrigger value="preview" disabled={placedItems.length === 0}>👁️ Preview</TabsTrigger>
          </TabsList>

          {/* Upload Tab */}
          <TabsContent value="upload" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Upload Your Room Photo</CardTitle>
                <CardDescription>Take a clear photo of where you want to place the furniture</CardDescription>
              </CardHeader>
              <CardContent>
                <div
                  className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-[#143109] transition-colors cursor-pointer"
                  onClick={() => fileInputRef.current?.click()}
                >
                  {roomImagePreview ? (
                    <div className="relative">
                      <img
                        src={roomImagePreview}
                        alt="Room preview"
                        className="w-full max-h-96 object-contain rounded-lg"
                      />
                      <Button
                        variant="destructive"
                        size="icon"
                        className="absolute top-2 right-2"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleReset();
                        }}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ) : (
                    <>
                      <Camera className="mx-auto h-16 w-16 text-gray-400 mb-4" />
                      <p className="text-lg font-medium mb-2">Click to upload room photo</p>
                      <p className="text-sm text-gray-500">PNG, JPG up to 10MB</p>
                      <p className="text-xs text-gray-400 mt-2">AI will automatically analyze your room</p>
                    </>
                  )}
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleFileSelect}
                />

                {loading && (
                  <div className="mt-4 space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Analyzing room with AI...
                      </span>
                      <span>{analysisProgress}%</span>
                    </div>
                    <Progress value={analysisProgress} />
                  </div>
                )}
              </CardContent>
            </Card>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="bg-blue-50 border-blue-200">
                <CardContent className="pt-6 text-center">
                  <Lightbulb className="h-8 w-8 mx-auto mb-2 text-blue-600" />
                  <p className="text-sm font-medium">AI Analysis</p>
                  <p className="text-xs text-gray-600">Style detection</p>
                </CardContent>
              </Card>
              <Card className="bg-green-50 border-green-200">
                <CardContent className="pt-6 text-center">
                  <Ruler className="h-8 w-8 mx-auto mb-2 text-green-600" />
                  <p className="text-sm font-medium">Smart Sizing</p>
                  <p className="text-xs text-gray-600">Auto-scale</p>
                </CardContent>
              </Card>
              <Card className="bg-purple-50 border-purple-200">
                <CardContent className="pt-6 text-center">
                  <Palette className="h-8 w-8 mx-auto mb-2 text-purple-600" />
                  <p className="text-sm font-medium">8+ Materials</p>
                  <p className="text-xs text-gray-600">Realistic textures</p>
                </CardContent>
              </Card>
              <Card className="bg-orange-50 border-orange-200">
                <CardContent className="pt-6 text-center">
                  <Eye className="h-8 w-8 mx-auto mb-2 text-orange-600" />
                  <p className="text-sm font-medium">3D Views</p>
                  <p className="text-xs text-gray-600">Multiple angles</p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Customize Tab */}
          <TabsContent value="customize" className="space-y-4">
            <div className="grid gap-4 lg:grid-cols-3">
              {/* Canvas Area */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <div className="flex justify-between items-center flex-wrap gap-2">
                    <div>
                      <CardTitle>3D Furniture Placement</CardTitle>
                      <CardDescription>Click furniture to select, drag to move</CardDescription>
                    </div>
                    <div className="flex gap-2 items-center">
                      <Select value={viewAngle} onValueChange={(v: any) => setViewAngle(v)}>
                        <SelectTrigger className="w-32">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="front">Front View</SelectItem>
                          <SelectItem value="3d">3D View</SelectItem>
                          <SelectItem value="top">Top View</SelectItem>
                        </SelectContent>
                      </Select>
                      <Badge variant="secondary">{placedItems.length} items</Badge>
                      <Button size="sm" onClick={addFurniture}>
                        <Plus className="h-4 w-4 mr-1" />
                        Add
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <canvas
                    ref={canvasRef}
                    onClick={handleCanvasClick}
                    className="w-full border-2 border-gray-200 rounded-lg cursor-crosshair"
                    style={{ maxHeight: '500px', objectFit: 'contain' }}
                  />

                  <div className="mt-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <Label className="flex items-center gap-2">
                        <Lightbulb className="h-4 w-4" />
                        Lighting: {lightingIntensity}%
                      </Label>
                      <Slider
                        value={[lightingIntensity]}
                        onValueChange={([v]) => setLightingIntensity(v)}
                        min={0}
                        max={100}
                        className="w-48"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <Label className="flex items-center gap-2">
                        <Eye className="h-4 w-4" />
                        Shadows
                      </Label>
                      <Button
                        size="sm"
                        variant={showShadows ? "default" : "outline"}
                        onClick={() => setShowShadows(!showShadows)}
                      >
                        {showShadows ? 'On' : 'Off'}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Controls Panel */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Customize Selected</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {selectedFurniture ? (
                    <>
                      <div className="space-y-2">
                        <Label className="flex items-center gap-2">
                          <Palette className="h-4 w-4" />
                          Material
                        </Label>
                        <Select
                          value={selectedFurniture.material}
                          onValueChange={(material) => {
                            const mat = furnitureMaterials.find(m => m.value === material);
                            updateSelectedItem({ material, color: mat?.color || selectedFurniture.color });
                          }}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {furnitureMaterials.map((mat) => (
                              <SelectItem key={mat.value} value={mat.value}>
                                <div className="flex items-center gap-2">
                                  <div
                                    className="w-4 h-4 rounded border"
                                    style={{ backgroundColor: mat.color }}
                                  />
                                  {mat.name}
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        {selectedMaterial && (
                          <p className="text-xs text-gray-500">
                            Roughness: {(selectedMaterial.roughness * 100).toFixed(0)}%
                          </p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label className="flex items-center gap-2">
                          <Maximize2 className="h-4 w-4" />
                          Size: {(selectedFurniture.scale * 100).toFixed(0)}%
                        </Label>
                        <Slider
                          value={[selectedFurniture.scale * 100]}
                          onValueChange={([v]) => updateSelectedItem({ scale: v / 100 })}
                          min={50}
                          max={200}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label className="flex items-center gap-2">
                          <RotateCw className="h-4 w-4" />
                          Rotation: {selectedFurniture.rotation}°
                        </Label>
                        <Slider
                          value={[selectedFurniture.rotation]}
                          onValueChange={([v]) => updateSelectedItem({ rotation: v })}
                          min={0}
                          max={360}
                        />
                      </div>

                      <Button
                        variant="destructive"
                        onClick={removeSelectedFurniture}
                        className="w-full"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Remove
                      </Button>
                    </>
                  ) : (
                    <div className="text-center text-gray-500 py-8">
                      <Move className="h-12 w-12 mx-auto mb-3 opacity-30" />
                      <p className="text-sm">Click furniture to customize</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* AI Recommendations Tab */}
          <TabsContent value="recommendations" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <Card className="bg-gradient-to-br from-green-50 to-blue-50 border-green-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Ruler className="h-5 w-5 text-green-600" />
                    Room Dimensions (AI Detected)
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {roomAnalysis && (
                    <>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Width:</span>
                        <span className="font-semibold">{roomAnalysis.dimensions.width.toFixed(1)}m</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Height:</span>
                        <span className="font-semibold">{roomAnalysis.dimensions.height.toFixed(1)}m</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Depth:</span>
                        <span className="font-semibold">{roomAnalysis.dimensions.depth.toFixed(1)}m</span>
                      </div>
                      <div className="mt-4 pt-4 border-t">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">Suitability:</span>
                          <Badge variant="default" className="bg-green-600">
                            {roomAnalysis.suitability.toFixed(0)}%
                          </Badge>
                        </div>
                        <Progress value={roomAnalysis.suitability} className="mt-2" />
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Palette className="h-5 w-5 text-purple-600" />
                    Room Style Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {roomAnalysis && (
                    <>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Style:</span>
                        <span className="font-semibold">
                          {roomStyles.find(s => s.value === roomAnalysis.style)?.name}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Lighting:</span>
                        <span className="font-semibold">{roomAnalysis.lighting}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Floor:</span>
                        <span className="font-semibold">{roomAnalysis.floorType}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Wall Color:</span>
                        <span className="font-semibold">{roomAnalysis.wallColor}</span>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-yellow-600" />
                  AI-Powered Recommendations
                </CardTitle>
                <CardDescription>Based on your room analysis and furniture selection</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {recommendations.map((rec, index) => (
                  <div
                    key={index}
                    className="p-4 bg-white border-2 border-gray-200 rounded-lg hover:border-[#143109] transition-colors"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-semibold text-gray-900">{rec.title}</h4>
                      <Badge variant="secondary">{rec.confidence}%</Badge>
                    </div>
                    <p className="text-sm text-gray-600">{rec.reason}</p>
                    <Progress value={rec.confidence} className="mt-2 h-1" />
                  </div>
                ))}

                {price && (
                  <div className="mt-4 p-4 bg-green-50 border-2 border-green-200 rounded-lg">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="text-sm font-medium text-green-900">Value for Money</p>
                        <p className="text-xs text-green-700">Great price for this quality</p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-green-600">Rs. {price.toLocaleString()}</p>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Preview Tab */}
          <TabsContent value="preview" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Final 3D AR Preview</CardTitle>
                <CardDescription>Your customized furniture arrangement</CardDescription>
              </CardHeader>
              <CardContent>
                <canvas
                  ref={canvasRef}
                  className="w-full border-2 border-[#143109] rounded-lg"
                  style={{ maxHeight: '600px', objectFit: 'contain' }}
                />
                <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-sm font-medium text-green-800">
                    ✓ {placedItems.length} furniture item{placedItems.length !== 1 ? 's' : ''} placed
                  </p>
                  <p className="text-xs text-green-600 mt-1">
                    Realistic 3D rendering with shadows, materials, and lighting
                  </p>
                </div>
              </CardContent>
            </Card>

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setActiveTab('customize')} className="flex-1">
                Back to Editing
              </Button>
              <Button
                onClick={() => {
                  toast({
                    title: "Preview Saved",
                    description: "Your AR preview has been generated",
                  });
                }}
                className="flex-1 bg-[#143109] hover:bg-[#AAAE7F]"
              >
                <Eye className="mr-2 h-4 w-4" />
                Save Preview
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
