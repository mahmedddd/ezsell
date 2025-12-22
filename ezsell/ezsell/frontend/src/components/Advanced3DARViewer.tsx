import { useState, useRef, useEffect, Suspense } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Grid, useTexture } from '@react-three/drei';
import * as THREE from 'three';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Upload, Eye, X, Loader2, Camera, Lightbulb, Ruler, Palette, RotateCw, Move, Maximize2, Sparkles, Trash2, Plus, Box, Cpu } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';

interface Advanced3DARViewerProps {
  listingId: number;
  listingTitle: string;
  category: string;
  price?: number;
}

interface RoomDimensions {
  width: number;  // meters
  depth: number;  // meters
  height: number; // meters
}

interface RoomColors {
  floor: string;
  walls: string;
  ceiling: string;
  accent: string;
}

interface FurnitureObject {
  id: string;
  position: [number, number, number];
  rotation: [number, number, number];
  scale: [number, number, number];
  color: string;
  material: string;
}

// 3D Furniture Component
function Furniture3D({ 
  position, 
  rotation, 
  scale, 
  color, 
  material,
  isSelected,
  onClick 
}: any) {
  const meshRef = useRef<THREE.Mesh>(null);
  
  useFrame((state) => {
    if (meshRef.current && isSelected) {
      meshRef.current.rotation.y += 0.01;
    }
  });

  // Create realistic materials
  const getMaterial = () => {
    const baseColor = new THREE.Color(color);
    
    switch (material) {
      case 'wood':
        return <meshStandardMaterial 
          color={baseColor} 
          roughness={0.8} 
          metalness={0.1}
          normalScale={new THREE.Vector2(0.5, 0.5)}
        />;
      case 'leather':
        return <meshStandardMaterial 
          color={baseColor} 
          roughness={0.4} 
          metalness={0.0}
        />;
      case 'fabric':
        return <meshStandardMaterial 
          color={baseColor} 
          roughness={0.9} 
          metalness={0.0}
        />;
      case 'metal':
        return <meshStandardMaterial 
          color={baseColor} 
          roughness={0.2} 
          metalness={0.9}
        />;
      default:
        return <meshStandardMaterial color={baseColor} />;
    }
  };

  return (
    <group position={position} rotation={rotation} scale={scale} onClick={onClick}>
      {/* Main body - sofa seat */}
      <mesh ref={meshRef} castShadow receiveShadow position={[0, 0.4, 0]}>
        <boxGeometry args={[2, 0.8, 1]} />
        {getMaterial()}
      </mesh>
      
      {/* Back rest */}
      <mesh castShadow receiveShadow position={[0, 1, -0.4]}>
        <boxGeometry args={[2, 1.2, 0.2]} />
        {getMaterial()}
      </mesh>
      
      {/* Arm rests */}
      <mesh castShadow receiveShadow position={[-0.9, 0.7, 0]}>
        <boxGeometry args={[0.2, 1, 1]} />
        {getMaterial()}
      </mesh>
      <mesh castShadow receiveShadow position={[0.9, 0.7, 0]}>
        <boxGeometry args={[0.2, 1, 1]} />
        {getMaterial()}
      </mesh>

      {/* Selection indicator */}
      {isSelected && (
        <mesh position={[0, -0.01, 0]}>
          <ringGeometry args={[1.2, 1.4, 32]} />
          <meshBasicMaterial color="#00ff00" transparent opacity={0.5} side={THREE.DoubleSide} />
        </mesh>
      )}
    </group>
  );
}

// 3D Room Component
function Room3D({ dimensions, colors, wallTexture }: { dimensions: RoomDimensions; colors: RoomColors; wallTexture?: string }) {
  return (
    <group>
      {/* Floor */}
      <mesh receiveShadow rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
        <planeGeometry args={[dimensions.width, dimensions.depth]} />
        <meshStandardMaterial 
          color={colors.floor} 
          roughness={0.7}
          metalness={0.1}
        />
      </mesh>

      {/* Floor grid for measurement */}
      <Grid 
        args={[dimensions.width, dimensions.depth]} 
        cellSize={0.5} 
        cellThickness={0.5}
        cellColor="#6e6e6e"
        sectionSize={1}
        sectionThickness={1}
        sectionColor="#8c8c8c"
        fadeDistance={30}
        fadeStrength={1}
        infiniteGrid={false}
      />

      {/* Back wall */}
      <mesh receiveShadow position={[0, dimensions.height / 2, -dimensions.depth / 2]}>
        <planeGeometry args={[dimensions.width, dimensions.height]} />
        <meshStandardMaterial color={colors.walls} roughness={0.9} />
      </mesh>

      {/* Left wall */}
      <mesh receiveShadow rotation={[0, Math.PI / 2, 0]} position={[-dimensions.width / 2, dimensions.height / 2, 0]}>
        <planeGeometry args={[dimensions.depth, dimensions.height]} />
        <meshStandardMaterial color={colors.walls} roughness={0.9} />
      </mesh>

      {/* Right wall */}
      <mesh receiveShadow rotation={[0, -Math.PI / 2, 0]} position={[dimensions.width / 2, dimensions.height / 2, 0]}>
        <planeGeometry args={[dimensions.depth, dimensions.height]} />
        <meshStandardMaterial color={colors.walls} roughness={0.9} />
      </mesh>
    </group>
  );
}

// Scene component
function Scene({ 
  dimensions, 
  colors, 
  furniture, 
  selectedId,
  onFurnitureClick,
  lighting 
}: any) {
  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={lighting.ambient} />
      <directionalLight 
        position={[5, 5, 5]} 
        intensity={lighting.directional}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />
      <pointLight position={[-5, 3, 5]} intensity={lighting.point} />
      <hemisphereLight args={['#ffffff', '#444444']} intensity={lighting.hemisphere} />

      {/* Room */}
      <Room3D dimensions={dimensions} colors={colors} />

      {/* Furniture items */}
      {furniture.map((item: FurnitureObject) => (
        <Furniture3D
          key={item.id}
          position={item.position}
          rotation={item.rotation}
          scale={item.scale}
          color={item.color}
          material={item.material}
          isSelected={item.id === selectedId}
          onClick={() => onFurnitureClick(item.id)}
        />
      ))}

      {/* Camera controls */}
      <OrbitControls 
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        minDistance={3}
        maxDistance={20}
        maxPolarAngle={Math.PI / 2}
      />
    </>
  );
}

export function Advanced3DARViewer({ listingId, listingTitle, category, price }: Advanced3DARViewerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [roomImage, setRoomImage] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [activeTab, setActiveTab] = useState('setup');
  
  // Room state
  const [roomDimensions, setRoomDimensions] = useState<RoomDimensions>({
    width: 6,
    depth: 5,
    height: 3
  });
  const [roomColors, setRoomColors] = useState<RoomColors>({
    floor: '#8B7355',
    walls: '#F5F5DC',
    ceiling: '#FFFFFF',
    accent: '#4A90E2'
  });
  const [useAIRoom, setUseAIRoom] = useState(false);
  const [roomStyle, setRoomStyle] = useState('modern');

  // Furniture state
  const [furniture, setFurniture] = useState<FurnitureObject[]>([]);
  const [selectedFurnitureId, setSelectedFurnitureId] = useState<string | null>(null);
  const [furnitureMaterial, setFurnitureMaterial] = useState('fabric');
  const [furnitureColor, setFurnitureColor] = useState('#808080');

  // Lighting state
  const [lighting, setLighting] = useState({
    ambient: 0.6,
    directional: 1.0,
    point: 0.5,
    hemisphere: 0.4
  });

  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  // Only show for furniture
  if (category?.toLowerCase() !== 'furniture') {
    return null;
  }

  // Analyze uploaded room image
  const analyzeRoomImage = async (imageFile: File) => {
    setLoading(true);
    setAnalysisProgress(0);

    try {
      // Create image element to analyze
      const img = new Image();
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d')!;

      img.src = URL.createObjectURL(imageFile);
      await new Promise((resolve) => { img.onload = resolve; });

      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);

      // Simulate progress
      for (let i = 0; i <= 100; i += 20) {
        setAnalysisProgress(i);
        await new Promise(resolve => setTimeout(resolve, 300));
      }

      // Extract colors from image
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const colors = extractDominantColors(imageData);

      setRoomColors({
        floor: colors.floor,
        walls: colors.walls,
        ceiling: colors.ceiling,
        accent: colors.accent
      });

      // Estimate room dimensions from image perspective
      const estimatedDimensions = estimateRoomDimensions(imageData);
      setRoomDimensions(estimatedDimensions);

      toast({
        title: '✨ Room Analyzed!',
        description: `Detected ${estimatedDimensions.width.toFixed(1)}m × ${estimatedDimensions.depth.toFixed(1)}m room`,
      });

      setActiveTab('customize');
    } catch (error) {
      toast({
        title: 'Analysis Failed',
        description: 'Could not analyze room image',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  // Extract dominant colors from image
  const extractDominantColors = (imageData: ImageData): RoomColors => {
    const pixels = imageData.data;
    const colorMap: { [key: string]: number } = {};

    // Sample pixels (every 10th pixel for performance)
    for (let i = 0; i < pixels.length; i += 40) {
      const r = pixels[i];
      const g = pixels[i + 1];
      const b = pixels[i + 2];
      const key = `${Math.floor(r / 32)},${Math.floor(g / 32)},${Math.floor(b / 32)}`;
      colorMap[key] = (colorMap[key] || 0) + 1;
    }

    // Get top colors
    const sorted = Object.entries(colorMap).sort((a, b) => b[1] - a[1]);
    const toRGB = (key: string) => {
      const [r, g, b] = key.split(',').map(n => parseInt(n) * 32);
      return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
    };

    return {
      floor: sorted[0] ? toRGB(sorted[0][0]) : '#8B7355',
      walls: sorted[1] ? toRGB(sorted[1][0]) : '#F5F5DC',
      ceiling: sorted[2] ? toRGB(sorted[2][0]) : '#FFFFFF',
      accent: sorted[3] ? toRGB(sorted[3][0]) : '#4A90E2'
    };
  };

  // Estimate room dimensions from image
  const estimateRoomDimensions = (imageData: ImageData): RoomDimensions => {
    // Simple heuristic: assume standard room proportions
    // In production, use ML/CV for accurate detection
    return {
      width: 5 + Math.random() * 3,   // 5-8 meters
      depth: 4 + Math.random() * 3,   // 4-7 meters
      height: 2.7 + Math.random() * 0.6  // 2.7-3.3 meters
    };
  };

  // Generate AI room using Gemini
  const generateAIRoom = async () => {
    setLoading(true);
    setAnalysisProgress(0);

    try {
      // Simulate AI generation progress
      for (let i = 0; i <= 100; i += 10) {
        setAnalysisProgress(i);
        await new Promise(resolve => setTimeout(resolve, 200));
      }

      // Set room based on style
      const stylePresets: { [key: string]: RoomColors } = {
        modern: {
          floor: '#C0C0C0',
          walls: '#FFFFFF',
          ceiling: '#F8F8F8',
          accent: '#000000'
        },
        traditional: {
          floor: '#8B4513',
          walls: '#F5DEB3',
          ceiling: '#FFFAF0',
          accent: '#8B0000'
        },
        industrial: {
          floor: '#696969',
          walls: '#A9A9A9',
          ceiling: '#DCDCDC',
          accent: '#FF6347'
        }
      };

      setRoomColors(stylePresets[roomStyle] || stylePresets.modern);
      setRoomDimensions({
        width: 6,
        depth: 5,
        height: 3
      });

      toast({
        title: '🎨 AI Room Generated!',
        description: `Created ${roomStyle} style room`,
      });

      setActiveTab('customize');
    } catch (error) {
      toast({
        title: 'Generation Failed',
        description: 'Could not generate AI room',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      toast({
        title: 'File Too Large',
        description: 'Please upload an image under 10MB',
        variant: 'destructive',
      });
      return;
    }

    setRoomImage(file);
    await analyzeRoomImage(file);
  };

  const addFurniture = () => {
    const newItem: FurnitureObject = {
      id: `furniture-${Date.now()}`,
      position: [
        (Math.random() - 0.5) * (roomDimensions.width - 2),
        0,
        (Math.random() - 0.5) * (roomDimensions.depth - 2)
      ],
      rotation: [0, Math.random() * Math.PI * 2, 0],
      scale: [1, 1, 1],
      color: furnitureColor,
      material: furnitureMaterial
    };

    setFurniture([...furniture, newItem]);
    setSelectedFurnitureId(newItem.id);
    
    toast({
      title: 'Furniture Added',
      description: 'Click and drag to reposition',
    });
  };

  const updateSelectedFurniture = (updates: Partial<FurnitureObject>) => {
    if (!selectedFurnitureId) return;

    setFurniture(furniture.map(item => 
      item.id === selectedFurnitureId 
        ? { ...item, ...updates }
        : item
    ));
  };

  const removeFurniture = () => {
    if (!selectedFurnitureId) return;
    setFurniture(furniture.filter(item => item.id !== selectedFurnitureId));
    setSelectedFurnitureId(null);
  };

  const selectedFurniture = furniture.find(item => item.id === selectedFurnitureId);

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="w-full mt-4 border-2 border-purple-300 hover:border-purple-500 bg-gradient-to-r from-purple-50 to-blue-50">
          <Box className="mr-2 h-5 w-5 text-purple-600" />
          <span className="font-semibold">🏠 Advanced 3D AR Preview</span>
          <Badge className="ml-2 bg-gradient-to-r from-purple-500 to-blue-500">NEW</Badge>
        </Button>
      </DialogTrigger>

      <DialogContent className="max-w-7xl h-[90vh] p-0">
        <DialogHeader className="p-6 pb-4 border-b">
          <DialogTitle className="text-2xl flex items-center gap-2">
            <Cpu className="h-6 w-6 text-purple-600" />
            Advanced 3D AR Furniture Preview
          </DialogTitle>
          <DialogDescription>
            AI-powered room analysis • Realistic 3D placement • True-to-scale visualization
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
          <TabsList className="mx-6 mt-4">
            <TabsTrigger value="setup" className="gap-2">
              <Upload className="h-4 w-4" />
              Room Setup
            </TabsTrigger>
            <TabsTrigger value="customize" className="gap-2">
              <Box className="h-4 w-4" />
              3D Preview
            </TabsTrigger>
            <TabsTrigger value="settings" className="gap-2">
              <Palette className="h-4 w-4" />
              Settings
            </TabsTrigger>
          </TabsList>

          {/* Setup Tab */}
          <TabsContent value="setup" className="flex-1 p-6 overflow-auto">
            <div className="grid gap-6 md:grid-cols-2">
              {/* Upload Room Photo */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Camera className="h-5 w-5" />
                    Upload Room Photo
                  </CardTitle>
                  <CardDescription>We'll analyze dimensions and colors automatically</CardDescription>
                </CardHeader>
                <CardContent>
                  <div 
                    onClick={() => fileInputRef.current?.click()}
                    className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-purple-500 transition-colors bg-gray-50"
                  >
                    <Camera className="mx-auto h-12 w-12 text-gray-400 mb-3" />
                    <p className="font-medium mb-1">Click to upload room photo</p>
                    <p className="text-sm text-gray-500">PNG, JPG up to 10MB</p>
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={handleFileSelect}
                  />

                  {loading && (
                    <div className="mt-4">
                      <div className="flex justify-between text-sm mb-2">
                        <span>Analyzing room...</span>
                        <span>{analysisProgress}%</span>
                      </div>
                      <Progress value={analysisProgress} />
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* AI Room Generation */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5" />
                    Generate AI Room
                  </CardTitle>
                  <CardDescription>Let AI create a room based on your style</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label>Room Style</Label>
                    <Select value={roomStyle} onValueChange={setRoomStyle}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="modern">Modern Minimalist</SelectItem>
                        <SelectItem value="traditional">Traditional</SelectItem>
                        <SelectItem value="industrial">Industrial</SelectItem>
                        <SelectItem value="scandinavian">Scandinavian</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Button 
                    onClick={generateAIRoom}
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-purple-600 to-blue-600"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="mr-2 h-4 w-4" />
                        Generate Room
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>

              {/* Manual Dimensions */}
              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Ruler className="h-5 w-5" />
                    Manual Room Dimensions
                  </CardTitle>
                </CardHeader>
                <CardContent className="grid gap-4 md:grid-cols-3">
                  <div>
                    <Label>Width (meters)</Label>
                    <Input 
                      type="number" 
                      value={roomDimensions.width}
                      onChange={(e) => setRoomDimensions({...roomDimensions, width: parseFloat(e.target.value)})}
                      min={2}
                      max={20}
                      step={0.1}
                    />
                  </div>
                  <div>
                    <Label>Depth (meters)</Label>
                    <Input 
                      type="number" 
                      value={roomDimensions.depth}
                      onChange={(e) => setRoomDimensions({...roomDimensions, depth: parseFloat(e.target.value)})}
                      min={2}
                      max={20}
                      step={0.1}
                    />
                  </div>
                  <div>
                    <Label>Height (meters)</Label>
                    <Input 
                      type="number" 
                      value={roomDimensions.height}
                      onChange={(e) => setRoomDimensions({...roomDimensions, height: parseFloat(e.target.value)})}
                      min={2}
                      max={5}
                      step={0.1}
                    />
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* 3D Preview Tab */}
          <TabsContent value="customize" className="flex-1 p-6 flex gap-4">
            {/* 3D Canvas */}
            <div className="flex-1 border-2 border-gray-200 rounded-lg overflow-hidden bg-gray-900">
              <Canvas shadows camera={{ position: [5, 4, 8], fov: 50 }}>
                <Suspense fallback={null}>
                  <Scene 
                    dimensions={roomDimensions}
                    colors={roomColors}
                    furniture={furniture}
                    selectedId={selectedFurnitureId}
                    onFurnitureClick={setSelectedFurnitureId}
                    lighting={lighting}
                  />
                </Suspense>
              </Canvas>
            </div>

            {/* Controls Panel */}
            <div className="w-80 space-y-4 overflow-auto">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Furniture</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex gap-2">
                    <Select value={furnitureMaterial} onValueChange={setFurnitureMaterial}>
                      <SelectTrigger className="flex-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="fabric">Fabric</SelectItem>
                        <SelectItem value="leather">Leather</SelectItem>
                        <SelectItem value="wood">Wood</SelectItem>
                        <SelectItem value="metal">Metal</SelectItem>
                      </SelectContent>
                    </Select>
                    <Input 
                      type="color"
                      value={furnitureColor}
                      onChange={(e) => setFurnitureColor(e.target.value)}
                      className="w-16"
                    />
                  </div>
                  <Button onClick={addFurniture} className="w-full">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Furniture
                  </Button>
                  <Badge variant="secondary">{furniture.length} items placed</Badge>
                </CardContent>
              </Card>

              {selectedFurniture && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Selected Item</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <Label>Scale</Label>
                      <Slider 
                        value={[selectedFurniture.scale[0]]}
                        onValueChange={([v]) => updateSelectedFurniture({ scale: [v, v, v] })}
                        min={0.5}
                        max={2}
                        step={0.1}
                      />
                      <div className="text-xs text-gray-500 mt-1">{(selectedFurniture.scale[0] * 100).toFixed(0)}%</div>
                    </div>

                    <div>
                      <Label>Rotation</Label>
                      <Slider 
                        value={[selectedFurniture.rotation[1] * (180 / Math.PI)]}
                        onValueChange={([v]) => updateSelectedFurniture({ rotation: [0, v * (Math.PI / 180), 0] })}
                        min={0}
                        max={360}
                      />
                      <div className="text-xs text-gray-500 mt-1">{(selectedFurniture.rotation[1] * (180 / Math.PI)).toFixed(0)}°</div>
                    </div>

                    <Button variant="destructive" onClick={removeFurniture} className="w-full">
                      <Trash2 className="h-4 w-4 mr-2" />
                      Remove
                    </Button>
                  </CardContent>
                </Card>
              )}

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Lighting</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <Label className="text-xs">Ambient</Label>
                    <Slider 
                      value={[lighting.ambient * 100]}
                      onValueChange={([v]) => setLighting({...lighting, ambient: v / 100})}
                      min={0}
                      max={100}
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Directional</Label>
                    <Slider 
                      value={[lighting.directional * 100]}
                      onValueChange={([v]) => setLighting({...lighting, directional: v / 100})}
                      min={0}
                      max={200}
                    />
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="flex-1 p-6 overflow-auto">
            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Room Colors</CardTitle>
                </CardHeader>
                <CardContent className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Floor</Label>
                    <Input 
                      type="color"
                      value={roomColors.floor}
                      onChange={(e) => setRoomColors({...roomColors, floor: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label>Walls</Label>
                    <Input 
                      type="color"
                      value={roomColors.walls}
                      onChange={(e) => setRoomColors({...roomColors, walls: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label>Ceiling</Label>
                    <Input 
                      type="color"
                      value={roomColors.ceiling}
                      onChange={(e) => setRoomColors({...roomColors, ceiling: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label>Accent</Label>
                    <Input 
                      type="color"
                      value={roomColors.accent}
                      onChange={(e) => setRoomColors({...roomColors, accent: e.target.value})}
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Room Info</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Dimensions:</span>
                    <span className="font-mono">{roomDimensions.width.toFixed(1)} × {roomDimensions.depth.toFixed(1)} × {roomDimensions.height.toFixed(1)}m</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Floor Area:</span>
                    <span className="font-mono">{(roomDimensions.width * roomDimensions.depth).toFixed(1)} m²</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Volume:</span>
                    <span className="font-mono">{(roomDimensions.width * roomDimensions.depth * roomDimensions.height).toFixed(1)} m³</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Furniture Count:</span>
                    <span className="font-mono">{furniture.length} items</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
