import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { Upload, Eye, X, Loader2, Camera, Plus, Trash2, RotateCw, Move, Maximize2, Palette } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { arService } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface AR3DViewerProps {
  listingId: number;
  listingTitle: string;
  category: string;
}

interface PlacedFurniture {
  id: string;
  x: number;
  y: number;
  scale: number;
  rotation: number;
  color: string;
}

const furnitureColors = [
  { name: 'Wood', value: '#8B4513', hex: '8B4513' },
  { name: 'White', value: '#FFFFFF', hex: 'FFFFFF' },
  { name: 'Black', value: '#1a1a1a', hex: '1a1a1a' },
  { name: 'Gray', value: '#808080', hex: '808080' },
  { name: 'Beige', value: '#F5F5DC', hex: 'F5F5DC' },
  { name: 'Navy', value: '#000080', hex: '000080' },
];

export function AR3DViewer({ listingId, listingTitle, category }: AR3DViewerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [roomImage, setRoomImage] = useState<File | null>(null);
  const [roomImagePreview, setRoomImagePreview] = useState<string | null>(null);
  const [placedItems, setPlacedItems] = useState<PlacedFurniture[]>([]);
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('upload');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { toast } = useToast();

  // Only show for furniture
  if (category?.toLowerCase() !== 'furniture') {
    return null;
  }

  useEffect(() => {
    if (roomImagePreview && canvasRef.current) {
      renderCanvas();
    }
  }, [roomImagePreview, placedItems]);

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
    setActiveTab('customize');
  };

  const renderCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas || !roomImagePreview) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);

      // Draw all placed furniture items
      placedItems.forEach((item) => {
        drawFurniture(ctx, item, item.id === selectedItem);
      });
    };
    img.src = roomImagePreview;
  };

  const drawFurniture = (ctx: CanvasRenderingContext2D, item: PlacedFurniture, isSelected: boolean) => {
    ctx.save();
    
    const baseWidth = 150 * item.scale;
    const baseHeight = 100 * item.scale;

    // Translate to position
    ctx.translate(item.x, item.y);
    ctx.rotate((item.rotation * Math.PI) / 180);

    // Draw shadow
    ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
    ctx.fillRect(-baseWidth/2 + 5, -baseHeight/2 + 5, baseWidth, baseHeight);

    // Draw furniture (3D-like box)
    ctx.fillStyle = item.color;
    ctx.fillRect(-baseWidth/2, -baseHeight/2, baseWidth, baseHeight);

    // Add 3D effect
    const gradient = ctx.createLinearGradient(-baseWidth/2, -baseHeight/2, baseWidth/2, baseHeight/2);
    gradient.addColorStop(0, 'rgba(255, 255, 255, 0.3)');
    gradient.addColorStop(1, 'rgba(0, 0, 0, 0.3)');
    ctx.fillStyle = gradient;
    ctx.fillRect(-baseWidth/2, -baseHeight/2, baseWidth, baseHeight);

    // Draw border
    ctx.strokeStyle = isSelected ? '#143109' : '#666';
    ctx.lineWidth = isSelected ? 4 : 2;
    ctx.strokeRect(-baseWidth/2, -baseHeight/2, baseWidth, baseHeight);

    // Draw label
    ctx.fillStyle = '#fff';
    ctx.fillRect(-baseWidth/2, -baseHeight/2 - 25, baseWidth, 20);
    ctx.fillStyle = '#000';
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(listingTitle.substring(0, 20), 0, -baseHeight/2 - 10);

    ctx.restore();
  };

  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current) return;
    
    const rect = canvasRef.current.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Check if clicked on existing item
    const clickedItem = placedItems.find(item => {
      const halfWidth = (75 * item.scale);
      const halfHeight = (50 * item.scale);
      return x >= item.x - halfWidth && x <= item.x + halfWidth &&
             y >= item.y - halfHeight && y <= item.y + halfHeight;
    });

    if (clickedItem) {
      setSelectedItem(clickedItem.id);
    } else {
      setSelectedItem(null);
    }
  };

  const addFurniture = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const newItem: PlacedFurniture = {
      id: `furniture-${Date.now()}`,
      x: canvas.width / 2,
      y: canvas.height / 2,
      scale: 1,
      rotation: 0,
      color: furnitureColors[0].value,
    };

    setPlacedItems([...placedItems, newItem]);
    setSelectedItem(newItem.id);
    toast({
      title: "Furniture Added",
      description: "Click and drag to reposition",
    });
  };

  const removeSelectedFurniture = () => {
    if (!selectedItem) return;
    setPlacedItems(placedItems.filter(item => item.id !== selectedItem));
    setSelectedItem(null);
    toast({
      title: "Furniture Removed",
      description: "Item deleted successfully",
    });
  };

  const updateSelectedItem = (updates: Partial<PlacedFurniture>) => {
    if (!selectedItem) return;
    setPlacedItems(placedItems.map(item => 
      item.id === selectedItem ? { ...item, ...updates } : item
    ));
  };

  const selectedFurniture = placedItems.find(item => item.id === selectedItem);

  const handleReset = () => {
    setRoomImage(null);
    setRoomImagePreview(null);
    setPlacedItems([]);
    setSelectedItem(null);
    setActiveTab('upload');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const saveARPreview = async () => {
    if (!canvasRef.current) return;

    setLoading(true);
    try {
      // Convert canvas to blob
      const blob = await new Promise<Blob>((resolve) => {
        canvasRef.current!.toBlob((b) => resolve(b!), 'image/jpeg', 0.9);
      });

      // Create file from blob
      const file = new File([blob], 'ar-preview.jpg', { type: 'image/jpeg' });
      
      // Send to backend
      const response = await arService.generateARPreview(listingTitle, file);
      
      toast({
        title: "AR Preview Saved!",
        description: "Your custom furniture arrangement has been saved",
      });
    } catch (error: any) {
      console.error('Save error:', error);
      toast({
        title: "Save Failed",
        description: error.response?.data?.detail || "Failed to save AR preview",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="w-full border-[#143109] text-[#143109] hover:bg-[#143109] hover:text-white">
          <Camera className="mr-2 h-5 w-5" />
          3D AR Preview
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-6xl max-h-[95vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl">3D AR Preview: {listingTitle}</DialogTitle>
          <DialogDescription>
            Upload your room photo and place multiple furniture items with custom colors and sizes
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="upload">1. Upload Room</TabsTrigger>
            <TabsTrigger value="customize" disabled={!roomImagePreview}>2. Customize</TabsTrigger>
            <TabsTrigger value="preview" disabled={!roomImagePreview}>3. Final Preview</TabsTrigger>
          </TabsList>

          {/* Upload Tab */}
          <TabsContent value="upload" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Upload Room Photo</CardTitle>
                <CardDescription>Take or upload a clear photo of your room</CardDescription>
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
                      <Upload className="mx-auto h-16 w-16 text-gray-400 mb-4" />
                      <p className="text-lg font-medium mb-2">Click to upload room photo</p>
                      <p className="text-sm text-gray-500">PNG, JPG up to 10MB</p>
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
                {roomImagePreview && (
                  <Button 
                    onClick={() => setActiveTab('customize')}
                    className="w-full mt-4 bg-[#143109] hover:bg-[#AAAE7F]"
                  >
                    Continue to Customization
                  </Button>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Customize Tab */}
          <TabsContent value="customize" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-3">
              {/* Canvas Area */}
              <Card className="md:col-span-2">
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <div>
                      <CardTitle>Place Furniture</CardTitle>
                      <CardDescription>Click to select, drag to move</CardDescription>
                    </div>
                    <div className="flex gap-2">
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
                    className="w-full border-2 border-gray-200 rounded-lg cursor-pointer"
                    style={{ maxHeight: '500px', objectFit: 'contain' }}
                  />
                </CardContent>
              </Card>

              {/* Controls Panel */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Customization</CardTitle>
                  <CardDescription>
                    {selectedFurniture ? 'Adjust selected item' : 'Select an item to customize'}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {selectedFurniture ? (
                    <>
                      {/* Size Control */}
                      <div className="space-y-2">
                        <Label className="flex items-center gap-2">
                          <Maximize2 className="h-4 w-4" />
                          Size: {(selectedFurniture.scale * 100).toFixed(0)}%
                        </Label>
                        <Slider
                          value={[selectedFurniture.scale]}
                          onValueChange={([scale]) => updateSelectedItem({ scale })}
                          min={0.5}
                          max={2}
                          step={0.1}
                          className="w-full"
                        />
                      </div>

                      {/* Rotation Control */}
                      <div className="space-y-2">
                        <Label className="flex items-center gap-2">
                          <RotateCw className="h-4 w-4" />
                          Rotation: {selectedFurniture.rotation}°
                        </Label>
                        <Slider
                          value={[selectedFurniture.rotation]}
                          onValueChange={([rotation]) => updateSelectedItem({ rotation })}
                          min={0}
                          max={360}
                          step={15}
                          className="w-full"
                        />
                      </div>

                      {/* Color Selector */}
                      <div className="space-y-2">
                        <Label className="flex items-center gap-2">
                          <Palette className="h-4 w-4" />
                          Color
                        </Label>
                        <Select
                          value={selectedFurniture.color}
                          onValueChange={(color) => updateSelectedItem({ color })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {furnitureColors.map((color) => (
                              <SelectItem key={color.hex} value={color.value}>
                                <div className="flex items-center gap-2">
                                  <div 
                                    className="w-4 h-4 rounded border border-gray-300"
                                    style={{ backgroundColor: color.value }}
                                  />
                                  {color.name}
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      {/* Remove Button */}
                      <Button
                        variant="destructive"
                        onClick={removeSelectedFurniture}
                        className="w-full"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Remove Item
                      </Button>
                    </>
                  ) : (
                    <div className="text-center text-gray-500 py-8">
                      <Move className="h-12 w-12 mx-auto mb-3 opacity-30" />
                      <p className="text-sm">Click on furniture to customize</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setActiveTab('upload')} className="flex-1">
                Back
              </Button>
              <Button 
                onClick={() => setActiveTab('preview')}
                disabled={placedItems.length === 0}
                className="flex-1 bg-[#143109] hover:bg-[#AAAE7F]"
              >
                Preview Result
              </Button>
            </div>
          </TabsContent>

          {/* Preview Tab */}
          <TabsContent value="preview" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Final AR Preview</CardTitle>
                <CardDescription>Review your custom furniture arrangement</CardDescription>
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
                    You can save this preview or go back to make adjustments
                  </p>
                </div>
              </CardContent>
            </Card>

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setActiveTab('customize')} className="flex-1">
                Back to Editing
              </Button>
              <Button 
                onClick={saveARPreview}
                disabled={loading}
                className="flex-1 bg-[#143109] hover:bg-[#AAAE7F]"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Eye className="mr-2 h-4 w-4" />
                    Save AR Preview
                  </>
                )}
              </Button>
            </div>
          </TabsContent>
        </Tabs>

        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 className="text-sm font-semibold text-blue-900 mb-2">💡 Pro Tips:</h4>
          <ul className="text-xs text-blue-700 space-y-1">
            <li>• Click "Add" to place multiple furniture items</li>
            <li>• Click on any item to select and customize it</li>
            <li>• Adjust size, rotation, and color for each item</li>
            <li>• Use the slider controls for precise adjustments</li>
          </ul>
        </div>
      </DialogContent>
    </Dialog>
  );
}
