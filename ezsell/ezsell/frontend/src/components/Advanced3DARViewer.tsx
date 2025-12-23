import { useState, useRef, useEffect, Suspense, useMemo } from 'react';
import { Canvas, useFrame, useThree, useLoader } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Grid, useTexture, Environment, ContactShadows, Plane, Text, RoundedBox, Float, SoftShadows, AccumulativeShadows, RandomizedLight, BakeShadows } from '@react-three/drei';
import * as THREE from 'three';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Upload, Eye, X, Loader2, Camera, Lightbulb, Ruler, Palette, RotateCw, Move, Maximize2, Sparkles, Trash2, Plus, Box, Cpu, Save, FolderOpen, Check, Star, ThumbsUp, Zap, Heart, DollarSign, Info, Settings, Image as ImageIcon, Layers } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';

interface Advanced3DARViewerProps {
  listingId: number;
  listingTitle: string;
  category: string;
  price?: number;
  furnitureImageUrl?: string; // URL of the listing's furniture image
  furnitureType?: string; // Type of furniture from listing (sofa, chair, table, etc.)
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

interface RoomAnalysis {
  dominantColors: string[];
  colorPalette: { color: string; percentage: number; name: string }[];
  brightness: number; // 0-100
  warmth: number; // -100 cold to +100 warm
  detectedStyle: string;
  style: string; // Simplified style name
  detectedObjects: string[];
  ambiance: 'cozy' | 'modern' | 'industrial' | 'minimalist' | 'traditional' | 'luxurious';
  lightingCondition: 'bright' | 'moderate' | 'dim' | 'natural' | 'artificial';
  suggestedFurnitureColors: string[];
  extractedColors: string[]; // Colors extracted from room image
  suggestedColors: string[]; // AI suggested complementary colors
  roomType: string;
  estimatedSize: string; // e.g., "Medium", "Large"
}

// AI Suggestion Interface
interface AISuggestion {
  id: string;
  type: 'color' | 'placement' | 'style' | 'value';
  title: string;
  description: string;
  confidence: number; // 0-100
  action?: () => void;
  icon: 'palette' | 'move' | 'sparkles' | 'thumbsup' | 'star' | 'zap';
}

// Saved Room Configuration Interface
interface SavedRoomConfig {
  id: string;
  name: string;
  listingId: number;
  listingTitle: string;
  thumbnail?: string;
  roomDimensions: RoomDimensions;
  roomColors: RoomColors;
  furniture: FurnitureObject[];
  lighting: any;
  roomAnalysis?: RoomAnalysis;
  createdAt: string;
  price?: number;
}

interface FurnitureObject {
  id: string;
  type: 'sofa' | 'chair' | 'table' | 'bed' | 'cabinet' | 'lamp' | 'plant' | 'rug';
  position: [number, number, number];
  rotation: [number, number, number];
  scale: [number, number, number];
  color: string;
  material: string;
  imageUrl?: string; // URL of actual furniture image
}

interface RoomObject {
  type: string;
  position: [number, number, number];
  color: string;
  size: 'small' | 'medium' | 'large';
}

// Production-Quality 3D Furniture with Real Geometry and Image Texture
// Renders actual 3D furniture models textured with the product image
function ImageBasedFurniture3D({
  imageUrl,
  position,
  rotation,
  scale,
  furnitureType,
  isSelected,
  onClick,
  color
}: {
  imageUrl: string;
  position: [number, number, number];
  rotation: [number, number, number];
  scale: [number, number, number];
  furnitureType: string;
  isSelected: boolean;
  onClick: () => void;
  color?: string;
}) {
  const meshRef = useRef<THREE.Group>(null);
  const [texture, setTexture] = useState<THREE.Texture | null>(null);
  const [dominantColor, setDominantColor] = useState(color || '#808080');
  const [secondaryColor, setSecondaryColor] = useState('#4a4a4a');
  const [useCustomColor, setUseCustomColor] = useState(false);

  // Update colors when color prop changes (user customization)
  useEffect(() => {
    if (color && color !== '#808080') {
      setUseCustomColor(true);
      setDominantColor(color);
      // Create complementary secondary color (darker shade)
      const c = new THREE.Color(color);
      c.multiplyScalar(0.7); // Make it darker
      setSecondaryColor(`#${c.getHexString()}`);
    }
  }, [color]);

  // Load furniture image as texture
  useEffect(() => {
    if (!imageUrl) {
      console.log('⚠️ No imageUrl provided for furniture');
      return;
    }
    
    console.log('🖼️ Loading furniture texture from:', imageUrl);
    
    const loader = new THREE.TextureLoader();
    loader.crossOrigin = 'anonymous';
    
    loader.load(
      imageUrl,
      (loadedTexture) => {
        console.log('✅ Furniture texture loaded successfully');
        loadedTexture.colorSpace = THREE.SRGBColorSpace;
        loadedTexture.minFilter = THREE.LinearMipmapLinearFilter;
        loadedTexture.magFilter = THREE.LinearFilter;
        loadedTexture.anisotropy = 16;
        loadedTexture.wrapS = THREE.ClampToEdgeWrapping;
        loadedTexture.wrapT = THREE.ClampToEdgeWrapping;
        
        setTexture(loadedTexture);
        
        // Extract colors from the image only if no custom color is set
        if (!useCustomColor) {
          const img = loadedTexture.image;
          if (img) {
            const canvas = document.createElement('canvas');
            canvas.width = 50;
            canvas.height = 50;
            const ctx = canvas.getContext('2d')!;
            ctx.drawImage(img, 0, 0, 50, 50);
            const data = ctx.getImageData(0, 0, 50, 50).data;
            
            // Get average color
            let r = 0, g = 0, b = 0, count = 0;
            for (let i = 0; i < data.length; i += 4) {
              const brightness = (data[i] + data[i+1] + data[i+2]) / 3;
              if (brightness > 20 && brightness < 240) {
                r += data[i];
                g += data[i + 1];
                b += data[i + 2];
                count++;
              }
            }
            if (count > 0) {
              r = Math.round(r / count);
              g = Math.round(g / count);
              b = Math.round(b / count);
              const extractedColor = `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
              setDominantColor(extractedColor);
              setSecondaryColor(`#${Math.max(0, r-40).toString(16).padStart(2, '0')}${Math.max(0, g-40).toString(16).padStart(2, '0')}${Math.max(0, b-40).toString(16).padStart(2, '0')}`);
            }
          }
        }
      },
      undefined,
      (error) => {
        console.error('❌ Texture load failed:', error);
      }
    );
  }, [imageUrl, useCustomColor]);

  // Animate selection with subtle float
  useFrame((state) => {
    if (meshRef.current && isSelected) {
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 2) * 0.02;
    }
  });

  // Create textured material with color tinting
  const getTexturedMaterial = (isMain: boolean = true) => {
    // If user has set a custom color, apply it as a tint
    if (useCustomColor) {
      return (
        <meshStandardMaterial 
          color={isMain ? dominantColor : secondaryColor}
          roughness={0.7}
          metalness={0.05}
          envMapIntensity={0.3}
        />
      );
    }
    
    // Use texture if available
    if (texture && isMain) {
      return (
        <meshStandardMaterial 
          map={texture}
          roughness={0.7}
          metalness={0.05}
          envMapIntensity={0.3}
        />
      );
    }
    return (
      <meshStandardMaterial 
        color={isMain ? dominantColor : secondaryColor}
        roughness={0.75}
        metalness={0.05}
        envMapIntensity={0.2}
      />
    );
  };

  // Render 3D furniture based on type
  const renderFurniture = () => {
    switch (furnitureType) {
      case 'sofa':
        return (
          <group>
            {/* Sofa base/seat */}
            <mesh castShadow receiveShadow position={[0, 0.3, 0]}>
              <boxGeometry args={[2.2, 0.4, 1]} />
              {getTexturedMaterial(true)}
            </mesh>
            {/* Sofa back */}
            <mesh castShadow receiveShadow position={[0, 0.7, -0.4]}>
              <boxGeometry args={[2.2, 0.7, 0.2]} />
              {getTexturedMaterial(true)}
            </mesh>
            {/* Left armrest */}
            <mesh castShadow receiveShadow position={[-1, 0.45, 0]}>
              <boxGeometry args={[0.2, 0.5, 1]} />
              {getTexturedMaterial(false)}
            </mesh>
            {/* Right armrest */}
            <mesh castShadow receiveShadow position={[1, 0.45, 0]}>
              <boxGeometry args={[0.2, 0.5, 1]} />
              {getTexturedMaterial(false)}
            </mesh>
            {/* Legs */}
            {[[-0.9, 0.05, 0.35], [0.9, 0.05, 0.35], [-0.9, 0.05, -0.35], [0.9, 0.05, -0.35]].map((pos, i) => (
              <mesh key={i} castShadow position={pos as [number, number, number]}>
                <cylinderGeometry args={[0.04, 0.04, 0.1, 8]} />
                <meshStandardMaterial color="#2a2a2a" metalness={0.6} roughness={0.3} />
              </mesh>
            ))}
            {/* Cushions */}
            <mesh castShadow position={[-0.5, 0.55, 0]}>
              <boxGeometry args={[0.8, 0.12, 0.85]} />
              {getTexturedMaterial(true)}
            </mesh>
            <mesh castShadow position={[0.5, 0.55, 0]}>
              <boxGeometry args={[0.8, 0.12, 0.85]} />
              {getTexturedMaterial(true)}
            </mesh>
          </group>
        );

      case 'bed':
        return (
          <group>
            {/* Mattress */}
            <mesh castShadow receiveShadow position={[0, 0.35, 0]}>
              <boxGeometry args={[2, 0.3, 2.2]} />
              {getTexturedMaterial(true)}
            </mesh>
            {/* Bed frame base */}
            <mesh castShadow receiveShadow position={[0, 0.15, 0]}>
              <boxGeometry args={[2.1, 0.2, 2.3]} />
              {getTexturedMaterial(false)}
            </mesh>
            {/* Headboard */}
            <mesh castShadow receiveShadow position={[0, 0.8, -1.1]}>
              <boxGeometry args={[2.1, 1.0, 0.1]} />
              {getTexturedMaterial(true)}
            </mesh>
            {/* Pillows */}
            <mesh castShadow position={[-0.5, 0.55, -0.8]}>
              <boxGeometry args={[0.6, 0.15, 0.4]} />
              <meshStandardMaterial color="#ffffff" roughness={0.9} />
            </mesh>
            <mesh castShadow position={[0.5, 0.55, -0.8]}>
              <boxGeometry args={[0.6, 0.15, 0.4]} />
              <meshStandardMaterial color="#ffffff" roughness={0.9} />
            </mesh>
            {/* Legs */}
            {[[-0.95, 0.05, 1.05], [0.95, 0.05, 1.05], [-0.95, 0.05, -1.05], [0.95, 0.05, -1.05]].map((pos, i) => (
              <mesh key={i} castShadow position={pos as [number, number, number]}>
                <cylinderGeometry args={[0.05, 0.05, 0.1, 8]} />
                <meshStandardMaterial color="#3a3a3a" metalness={0.5} roughness={0.4} />
              </mesh>
            ))}
          </group>
        );

      case 'chair':
        return (
          <group>
            {/* Seat */}
            <mesh castShadow receiveShadow position={[0, 0.45, 0]}>
              <boxGeometry args={[0.5, 0.08, 0.5]} />
              {getTexturedMaterial(true)}
            </mesh>
            {/* Back */}
            <mesh castShadow receiveShadow position={[0, 0.85, -0.22]}>
              <boxGeometry args={[0.5, 0.7, 0.06]} />
              {getTexturedMaterial(true)}
            </mesh>
            {/* Legs */}
            {[[-0.2, 0.22, 0.2], [0.2, 0.22, 0.2], [-0.2, 0.22, -0.2], [0.2, 0.22, -0.2]].map((pos, i) => (
              <mesh key={i} castShadow position={pos as [number, number, number]}>
                <cylinderGeometry args={[0.025, 0.025, 0.44, 8]} />
                <meshStandardMaterial color={secondaryColor} metalness={0.4} roughness={0.5} />
              </mesh>
            ))}
          </group>
        );

      case 'table':
        return (
          <group>
            {/* Table top */}
            <mesh castShadow receiveShadow position={[0, 0.75, 0]}>
              <boxGeometry args={[1.4, 0.05, 0.8]} />
              {getTexturedMaterial(true)}
            </mesh>
            {/* Legs */}
            {[[-0.6, 0.37, 0.3], [0.6, 0.37, 0.3], [-0.6, 0.37, -0.3], [0.6, 0.37, -0.3]].map((pos, i) => (
              <mesh key={i} castShadow position={pos as [number, number, number]}>
                <boxGeometry args={[0.06, 0.74, 0.06]} />
                {getTexturedMaterial(false)}
              </mesh>
            ))}
            {/* Support beams */}
            <mesh castShadow position={[0, 0.65, 0.3]}>
              <boxGeometry args={[1.2, 0.04, 0.04]} />
              {getTexturedMaterial(false)}
            </mesh>
            <mesh castShadow position={[0, 0.65, -0.3]}>
              <boxGeometry args={[1.2, 0.04, 0.04]} />
              {getTexturedMaterial(false)}
            </mesh>
          </group>
        );

      case 'cabinet':
        return (
          <group>
            {/* Main body */}
            <mesh castShadow receiveShadow position={[0, 0.7, 0]}>
              <boxGeometry args={[1.2, 1.4, 0.5]} />
              {getTexturedMaterial(true)}
            </mesh>
            {/* Doors */}
            <mesh castShadow position={[-0.3, 0.7, 0.26]}>
              <boxGeometry args={[0.58, 1.35, 0.02]} />
              {getTexturedMaterial(true)}
            </mesh>
            <mesh castShadow position={[0.3, 0.7, 0.26]}>
              <boxGeometry args={[0.58, 1.35, 0.02]} />
              {getTexturedMaterial(true)}
            </mesh>
            {/* Handles */}
            <mesh castShadow position={[-0.08, 0.7, 0.28]}>
              <boxGeometry args={[0.02, 0.15, 0.02]} />
              <meshStandardMaterial color="#888888" metalness={0.8} roughness={0.2} />
            </mesh>
            <mesh castShadow position={[0.08, 0.7, 0.28]}>
              <boxGeometry args={[0.02, 0.15, 0.02]} />
              <meshStandardMaterial color="#888888" metalness={0.8} roughness={0.2} />
            </mesh>
            {/* Base */}
            <mesh castShadow position={[0, 0.03, 0]}>
              <boxGeometry args={[1.2, 0.06, 0.5]} />
              {getTexturedMaterial(false)}
            </mesh>
          </group>
        );

      case 'lamp':
        return (
          <group>
            {/* Base */}
            <mesh castShadow receiveShadow position={[0, 0.02, 0]}>
              <cylinderGeometry args={[0.15, 0.18, 0.04, 16]} />
              {getTexturedMaterial(false)}
            </mesh>
            {/* Stand */}
            <mesh castShadow position={[0, 0.6, 0]}>
              <cylinderGeometry args={[0.02, 0.02, 1.16, 8]} />
              <meshStandardMaterial color="#888888" metalness={0.7} roughness={0.3} />
            </mesh>
            {/* Shade */}
            <mesh castShadow position={[0, 1.25, 0]}>
              <cylinderGeometry args={[0.15, 0.25, 0.35, 16]} />
              {getTexturedMaterial(true)}
            </mesh>
            {/* Light glow */}
            <pointLight position={[0, 1.1, 0]} intensity={0.5} color="#FFF5E0" distance={3} decay={2} />
          </group>
        );

      case 'plant':
        return (
          <group>
            {/* Pot */}
            <mesh castShadow receiveShadow position={[0, 0.15, 0]}>
              <cylinderGeometry args={[0.15, 0.12, 0.3, 16]} />
              {getTexturedMaterial(false)}
            </mesh>
            {/* Soil */}
            <mesh position={[0, 0.28, 0]}>
              <cylinderGeometry args={[0.14, 0.14, 0.04, 16]} />
              <meshStandardMaterial color="#3d2817" roughness={0.95} />
            </mesh>
            {/* Plant foliage - simplified as spheres */}
            <mesh castShadow position={[0, 0.55, 0]}>
              <sphereGeometry args={[0.25, 16, 16]} />
              <meshStandardMaterial color="#2d5a27" roughness={0.9} />
            </mesh>
            <mesh castShadow position={[0.1, 0.7, 0.05]}>
              <sphereGeometry args={[0.18, 16, 16]} />
              <meshStandardMaterial color="#3a7a32" roughness={0.9} />
            </mesh>
            <mesh castShadow position={[-0.08, 0.65, -0.05]}>
              <sphereGeometry args={[0.15, 16, 16]} />
              <meshStandardMaterial color="#4a8a42" roughness={0.9} />
            </mesh>
          </group>
        );

      case 'rug':
        return (
          <group>
            {/* Rug - flat on floor */}
            <mesh receiveShadow position={[0, 0.01, 0]} rotation={[-Math.PI / 2, 0, 0]}>
              <planeGeometry args={[2.5, 1.8]} />
              {texture ? (
                <meshStandardMaterial map={texture} roughness={0.95} />
              ) : (
                <meshStandardMaterial color={dominantColor} roughness={0.95} />
              )}
            </mesh>
            {/* Rug edge/fringe */}
            <mesh receiveShadow position={[0, 0.005, 0]} rotation={[-Math.PI / 2, 0, 0]}>
              <ringGeometry args={[1.24, 1.27, 64]} />
              <meshStandardMaterial color={secondaryColor} roughness={0.9} />
            </mesh>
          </group>
        );

      default:
        // Generic furniture - box with texture
        return (
          <group>
            <mesh castShadow receiveShadow position={[0, 0.5, 0]}>
              <boxGeometry args={[1, 1, 1]} />
              {getTexturedMaterial(true)}
            </mesh>
          </group>
        );
    }
  };

  return (
    <group ref={meshRef} position={position} rotation={rotation} scale={scale} onClick={onClick}>
      {renderFurniture()}
      
      {/* Selection indicator */}
      {isSelected && (
        <>
          <Float speed={2} rotationIntensity={0.1} floatIntensity={0.15}>
            <mesh position={[0, 0.02, 0]} rotation={[-Math.PI / 2, 0, 0]}>
              <ringGeometry args={[1.3, 1.4, 64]} />
              <meshBasicMaterial color="#4A90E2" transparent opacity={0.6} side={THREE.DoubleSide} />
            </mesh>
          </Float>
          <pointLight position={[0, 1, 0]} intensity={0.3} color="#4A90E2" distance={3} />
        </>
      )}
    </group>
  );
}

// Production-Quality 3D Furniture Component with Multiple Types
function Furniture3D({ 
  position, 
  rotation, 
  scale, 
  color, 
  material,
  furnitureType = 'sofa',
  isSelected,
  onClick 
}: any) {
  const meshRef = useRef<THREE.Mesh>(null);
  const groupRef = useRef<THREE.Group>(null);

  // Create realistic PBR materials
  const getMaterial = (customColor?: string) => {
    const baseColor = new THREE.Color(customColor || color);
    
    switch (material) {
      case 'wood':
        return <meshStandardMaterial 
          color={baseColor} 
          roughness={0.75} 
          metalness={0.05}
          envMapIntensity={0.3}
        />;
      case 'leather':
        return <meshStandardMaterial 
          color={baseColor} 
          roughness={0.35} 
          metalness={0.02}
          envMapIntensity={0.4}
        />;
      case 'fabric':
        return <meshStandardMaterial 
          color={baseColor} 
          roughness={0.95} 
          metalness={0.0}
          envMapIntensity={0.1}
        />;
      case 'metal':
        return <meshStandardMaterial 
          color={baseColor} 
          roughness={0.15} 
          metalness={0.95}
          envMapIntensity={0.8}
        />;
      case 'glass':
        return <meshStandardMaterial 
          color={baseColor} 
          roughness={0.05} 
          metalness={0.1}
          transparent
          opacity={0.3}
          envMapIntensity={1}
        />;
      case 'velvet':
        return <meshStandardMaterial 
          color={baseColor} 
          roughness={0.98} 
          metalness={0.0}
          envMapIntensity={0.05}
        />;
      default:
        return <meshStandardMaterial color={baseColor} roughness={0.7} />;
    }
  };

  // Render different furniture types
  const renderFurniture = () => {
    switch (furnitureType) {
      case 'sofa':
        return (
          <>
            {/* Sofa seat */}
            <mesh castShadow receiveShadow position={[0, 0.35, 0]}>
              <boxGeometry args={[2, 0.5, 1]} />
              {getMaterial()}
            </mesh>
            {/* Sofa back */}
            <mesh castShadow receiveShadow position={[0, 0.85, -0.4]}>
              <boxGeometry args={[2, 0.8, 0.2]} />
              {getMaterial()}
            </mesh>
            {/* Sofa arm left */}
            <mesh castShadow receiveShadow position={[-0.9, 0.55, 0]}>
              <boxGeometry args={[0.2, 0.7, 1]} />
              {getMaterial()}
            </mesh>
            {/* Sofa arm right */}
            <mesh castShadow receiveShadow position={[0.9, 0.55, 0]}>
              <boxGeometry args={[0.2, 0.7, 1]} />
              {getMaterial()}
            </mesh>
            {/* Sofa legs */}
            <mesh castShadow position={[-0.8, 0.05, 0.35]}>
              <cylinderGeometry args={[0.05, 0.05, 0.1, 8]} />
              <meshStandardMaterial color="#2a2a2a" metalness={0.6} roughness={0.3} />
            </mesh>
            <mesh castShadow position={[0.8, 0.05, 0.35]}>
              <cylinderGeometry args={[0.05, 0.05, 0.1, 8]} />
              <meshStandardMaterial color="#2a2a2a" metalness={0.6} roughness={0.3} />
            </mesh>
            <mesh castShadow position={[-0.8, 0.05, -0.35]}>
              <cylinderGeometry args={[0.05, 0.05, 0.1, 8]} />
              <meshStandardMaterial color="#2a2a2a" metalness={0.6} roughness={0.3} />
            </mesh>
            <mesh castShadow position={[0.8, 0.05, -0.35]}>
              <cylinderGeometry args={[0.05, 0.05, 0.1, 8]} />
              <meshStandardMaterial color="#2a2a2a" metalness={0.6} roughness={0.3} />
            </mesh>
            {/* Cushions */}
            <mesh castShadow position={[-0.5, 0.65, 0]}>
              <boxGeometry args={[0.6, 0.1, 0.8]} />
              {getMaterial()}
            </mesh>
            <mesh castShadow position={[0.5, 0.65, 0]}>
              <boxGeometry args={[0.6, 0.1, 0.8]} />
              {getMaterial()}
            </mesh>
          </>
        );

      case 'chair':
        return (
          <>
            {/* Chair seat */}
            <mesh castShadow receiveShadow position={[0, 0.45, 0]}>
              <boxGeometry args={[0.5, 0.08, 0.5]} />
              {getMaterial()}
            </mesh>
            {/* Chair back */}
            <mesh castShadow receiveShadow position={[0, 0.85, -0.22]}>
              <boxGeometry args={[0.5, 0.7, 0.06]} />
              {getMaterial()}
            </mesh>
            {/* Chair legs */}
            {[[-0.2, -0.2], [0.2, -0.2], [-0.2, 0.2], [0.2, 0.2]].map(([x, z], i) => (
              <mesh key={i} castShadow position={[x, 0.2, z]}>
                <cylinderGeometry args={[0.025, 0.025, 0.4, 8]} />
                <meshStandardMaterial color="#4a3728" roughness={0.7} />
              </mesh>
            ))}
          </>
        );

      case 'table':
        return (
          <>
            {/* Table top */}
            <mesh castShadow receiveShadow position={[0, 0.75, 0]}>
              <boxGeometry args={[1.2, 0.04, 0.8]} />
              {getMaterial()}
            </mesh>
            {/* Table legs */}
            {[[-0.5, -0.3], [0.5, -0.3], [-0.5, 0.3], [0.5, 0.3]].map(([x, z], i) => (
              <mesh key={i} castShadow position={[x, 0.37, z]}>
                <boxGeometry args={[0.06, 0.73, 0.06]} />
                {getMaterial()}
              </mesh>
            ))}
          </>
        );

      case 'bed':
        return (
          <>
            {/* Mattress */}
            <mesh castShadow receiveShadow position={[0, 0.4, 0]}>
              <boxGeometry args={[2, 0.3, 2.2]} />
              <meshStandardMaterial color="#f5f5f5" roughness={0.95} />
            </mesh>
            {/* Bed frame */}
            <mesh castShadow position={[0, 0.15, 0]}>
              <boxGeometry args={[2.1, 0.3, 2.3]} />
              {getMaterial()}
            </mesh>
            {/* Headboard */}
            <mesh castShadow position={[0, 0.9, -1.05]}>
              <boxGeometry args={[2.1, 1, 0.1]} />
              {getMaterial()}
            </mesh>
            {/* Pillows */}
            <mesh castShadow position={[-0.5, 0.65, -0.8]}>
              <boxGeometry args={[0.5, 0.2, 0.4]} />
              <meshStandardMaterial color="#ffffff" roughness={0.9} />
            </mesh>
            <mesh castShadow position={[0.5, 0.65, -0.8]}>
              <boxGeometry args={[0.5, 0.2, 0.4]} />
              <meshStandardMaterial color="#ffffff" roughness={0.9} />
            </mesh>
          </>
        );

      case 'cabinet':
        return (
          <>
            {/* Cabinet body */}
            <mesh castShadow receiveShadow position={[0, 0.5, 0]}>
              <boxGeometry args={[1, 1, 0.4]} />
              {getMaterial()}
            </mesh>
            {/* Doors */}
            <mesh castShadow position={[-0.24, 0.5, 0.21]}>
              <boxGeometry args={[0.48, 0.9, 0.02]} />
              {getMaterial()}
            </mesh>
            <mesh castShadow position={[0.24, 0.5, 0.21]}>
              <boxGeometry args={[0.48, 0.9, 0.02]} />
              {getMaterial()}
            </mesh>
            {/* Handles */}
            <mesh castShadow position={[-0.08, 0.5, 0.23]}>
              <boxGeometry args={[0.03, 0.1, 0.02]} />
              <meshStandardMaterial color="#c0c0c0" metalness={0.8} roughness={0.2} />
            </mesh>
            <mesh castShadow position={[0.08, 0.5, 0.23]}>
              <boxGeometry args={[0.03, 0.1, 0.02]} />
              <meshStandardMaterial color="#c0c0c0" metalness={0.8} roughness={0.2} />
            </mesh>
          </>
        );

      case 'lamp':
        return (
          <>
            {/* Lamp base */}
            <mesh castShadow position={[0, 0.05, 0]}>
              <cylinderGeometry args={[0.15, 0.2, 0.1, 16]} />
              <meshStandardMaterial color="#3a3a3a" metalness={0.7} roughness={0.3} />
            </mesh>
            {/* Lamp pole */}
            <mesh castShadow position={[0, 0.7, 0]}>
              <cylinderGeometry args={[0.02, 0.02, 1.2, 8]} />
              <meshStandardMaterial color="#4a4a4a" metalness={0.6} roughness={0.3} />
            </mesh>
            {/* Lamp shade */}
            <mesh castShadow position={[0, 1.3, 0]}>
              <coneGeometry args={[0.25, 0.3, 16, 1, true]} />
              <meshStandardMaterial color="#f5e6d3" roughness={0.8} side={THREE.DoubleSide} />
            </mesh>
            {/* Light bulb glow */}
            <pointLight position={[0, 1.2, 0]} intensity={0.5} color="#fff5e6" distance={3} />
          </>
        );

      case 'plant':
        return (
          <>
            {/* Pot */}
            <mesh castShadow position={[0, 0.15, 0]}>
              <cylinderGeometry args={[0.15, 0.12, 0.3, 16]} />
              <meshStandardMaterial color="#8B4513" roughness={0.9} />
            </mesh>
            {/* Soil */}
            <mesh position={[0, 0.28, 0]}>
              <cylinderGeometry args={[0.13, 0.13, 0.04, 16]} />
              <meshStandardMaterial color="#3d2817" roughness={1} />
            </mesh>
            {/* Plant leaves - simplified */}
            {[0, 60, 120, 180, 240, 300].map((angle, i) => (
              <mesh key={i} castShadow position={[
                Math.sin(angle * Math.PI / 180) * 0.1,
                0.5 + Math.random() * 0.2,
                Math.cos(angle * Math.PI / 180) * 0.1
              ]} rotation={[0.3, angle * Math.PI / 180, 0.2]}>
                <boxGeometry args={[0.15, 0.3, 0.02]} />
                <meshStandardMaterial color="#228B22" roughness={0.8} />
              </mesh>
            ))}
          </>
        );

      case 'rug':
        return (
          <mesh receiveShadow rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 0]}>
            <planeGeometry args={[2, 1.5]} />
            {getMaterial()}
          </mesh>
        );

      default:
        return (
          <mesh castShadow receiveShadow>
            <boxGeometry args={[1, 1, 1]} />
            {getMaterial()}
          </mesh>
        );
    }
  };

  return (
    <group ref={groupRef} position={position} rotation={rotation} scale={scale} onClick={onClick}>
      {renderFurniture()}
      
      {/* Selection indicator - glowing ring on floor */}
      {isSelected && (
        <>
          <mesh position={[0, 0.02, 0]} rotation={[-Math.PI / 2, 0, 0]}>
            <ringGeometry args={[1.3, 1.5, 64]} />
            <meshBasicMaterial color="#4A90E2" transparent opacity={0.7} side={THREE.DoubleSide} />
          </mesh>
          {/* Selection glow */}
          <pointLight position={[0, 0.5, 0]} intensity={0.3} color="#4A90E2" distance={2} />
        </>
      )}
    </group>
  );
}

// Draggable Furniture Wrapper with click-and-drag functionality
function DraggableFurniture({ 
  furniture, 
  isSelected, 
  onPositionChange, 
  onClick,
  roomDimensions
}: any) {
  const meshRef = useRef<THREE.Group>(null);
  const { camera, raycaster, gl } = useThree();
  const [isDragging, setIsDragging] = useState(false);
  const floorPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
  const dragOffset = useRef(new THREE.Vector3());

  useEffect(() => {
    if (!isSelected) return;

    const handlePointerMove = (e: PointerEvent) => {
      if (!isDragging || !meshRef.current) return;
      
      // Calculate mouse position in normalized device coordinates
      const rect = gl.domElement.getBoundingClientRect();
      const mouse = new THREE.Vector2(
        ((e.clientX - rect.left) / rect.width) * 2 - 1,
        -((e.clientY - rect.top) / rect.height) * 2 + 1
      );
      
      // Update raycaster
      raycaster.setFromCamera(mouse, camera);
      
      // Find intersection with floor plane
      const intersection = new THREE.Vector3();
      raycaster.ray.intersectPlane(floorPlane, intersection);
      
      if (intersection) {
        // Clamp to room bounds
        const halfWidth = roomDimensions.width / 2 - 0.5;
        const halfDepth = roomDimensions.depth / 2 - 0.5;
        
        const newX = Math.max(-halfWidth, Math.min(halfWidth, intersection.x - dragOffset.current.x));
        const newZ = Math.max(-halfDepth, Math.min(halfDepth, intersection.z - dragOffset.current.z));
        
        onPositionChange([newX, 0, newZ]);
      }
    };

    const handlePointerUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      gl.domElement.addEventListener('pointermove', handlePointerMove);
      gl.domElement.addEventListener('pointerup', handlePointerUp);
    }

    return () => {
      gl.domElement.removeEventListener('pointermove', handlePointerMove);
      gl.domElement.removeEventListener('pointerup', handlePointerUp);
    };
  }, [isDragging, isSelected, camera, raycaster, gl, onPositionChange, roomDimensions]);

  const handlePointerDown = (e: any) => {
    e.stopPropagation();
    onClick();
    
    if (isSelected) {
      // Calculate drag offset
      const rect = gl.domElement.getBoundingClientRect();
      const mouse = new THREE.Vector2(
        ((e.clientX - rect.left) / rect.width) * 2 - 1,
        -((e.clientY - rect.top) / rect.height) * 2 + 1
      );
      
      raycaster.setFromCamera(mouse, camera);
      const intersection = new THREE.Vector3();
      raycaster.ray.intersectPlane(floorPlane, intersection);
      
      if (intersection) {
        dragOffset.current.set(
          intersection.x - furniture.position[0],
          0,
          intersection.z - furniture.position[2]
        );
      }
      
      setIsDragging(true);
    }
  };

  return (
    <group 
      ref={meshRef}
      onPointerDown={handlePointerDown}
    >
      <Furniture3D
        position={furniture.position}
        rotation={furniture.rotation}
        scale={furniture.scale}
        color={furniture.color}
        material={furniture.material}
        furnitureType={furniture.type || 'sofa'}
        isSelected={isSelected}
        onClick={() => {}}
      />
    </group>
  );
}

// Draggable Image-Based Furniture Component
function DraggableImageFurniture({ 
  furniture, 
  isSelected, 
  onPositionChange, 
  onClick,
  roomDimensions
}: any) {
  const meshRef = useRef<THREE.Group>(null);
  const { camera, raycaster, gl } = useThree();
  const [isDragging, setIsDragging] = useState(false);
  const floorPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
  const dragOffset = useRef(new THREE.Vector3());

  useEffect(() => {
    if (!isSelected) return;

    const handlePointerMove = (e: PointerEvent) => {
      if (!isDragging || !meshRef.current) return;
      
      const rect = gl.domElement.getBoundingClientRect();
      const mouse = new THREE.Vector2(
        ((e.clientX - rect.left) / rect.width) * 2 - 1,
        -((e.clientY - rect.top) / rect.height) * 2 + 1
      );
      
      raycaster.setFromCamera(mouse, camera);
      const intersection = new THREE.Vector3();
      raycaster.ray.intersectPlane(floorPlane, intersection);
      
      if (intersection) {
        const halfWidth = roomDimensions.width / 2 - 0.5;
        const halfDepth = roomDimensions.depth / 2 - 0.5;
        
        const newX = Math.max(-halfWidth, Math.min(halfWidth, intersection.x - dragOffset.current.x));
        const newZ = Math.max(-halfDepth, Math.min(halfDepth, intersection.z - dragOffset.current.z));
        
        onPositionChange([newX, 0, newZ]);
      }
    };

    const handlePointerUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      gl.domElement.addEventListener('pointermove', handlePointerMove);
      gl.domElement.addEventListener('pointerup', handlePointerUp);
    }

    return () => {
      gl.domElement.removeEventListener('pointermove', handlePointerMove);
      gl.domElement.removeEventListener('pointerup', handlePointerUp);
    };
  }, [isDragging, isSelected, camera, raycaster, gl, onPositionChange, roomDimensions]);

  const handlePointerDown = (e: any) => {
    e.stopPropagation();
    onClick();
    
    if (isSelected) {
      const rect = gl.domElement.getBoundingClientRect();
      const mouse = new THREE.Vector2(
        ((e.clientX - rect.left) / rect.width) * 2 - 1,
        -((e.clientY - rect.top) / rect.height) * 2 + 1
      );
      
      raycaster.setFromCamera(mouse, camera);
      const intersection = new THREE.Vector3();
      raycaster.ray.intersectPlane(floorPlane, intersection);
      
      if (intersection) {
        dragOffset.current.set(
          intersection.x - furniture.position[0],
          0,
          intersection.z - furniture.position[2]
        );
      }
      
      setIsDragging(true);
    }
  };

  return (
    <group 
      ref={meshRef}
      onPointerDown={handlePointerDown}
    >
      <ImageBasedFurniture3D
        imageUrl={furniture.imageUrl}
        position={furniture.position}
        rotation={furniture.rotation}
        scale={furniture.scale}
        furnitureType={furniture.type}
        isSelected={isSelected}
        onClick={() => {}}
        color={furniture.color}
      />
    </group>
  );
}

// Production-Quality 3D Room Component with Windows and Realistic Details
function Room3D({ dimensions, colors, ambiance, showGrid = true, roomImageUrl }: { 
  dimensions: RoomDimensions; 
  colors: RoomColors; 
  ambiance?: string;
  showGrid?: boolean;
  roomImageUrl?: string | null;
}) {
  // Calculate ambient lighting based on room colors
  const floorColor = new THREE.Color(colors.floor);
  const wallColor = new THREE.Color(colors.walls);
  
  // Subtle color variations for realism
  const wallColorLeft = wallColor.clone().offsetHSL(0, 0, -0.03);
  const wallColorRight = wallColor.clone().offsetHSL(0, 0, 0.03);
  const wallColorBack = wallColor.clone();

  // Window dimensions
  const windowWidth = Math.min(1.5, dimensions.width * 0.25);
  const windowHeight = Math.min(1.8, dimensions.height * 0.5);
  const windowY = dimensions.height * 0.55;

  return (
    <group>
      {/* ============ FLOOR ============ */}
      {/* Main floor */}
      <mesh receiveShadow rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
        <planeGeometry args={[dimensions.width, dimensions.depth, 32, 32]} />
        <meshStandardMaterial 
          color={colors.floor}
          roughness={0.65}
          metalness={0.05}
          envMapIntensity={0.3}
        />
      </mesh>

      {/* Floor grid for measurement - optional */}
      {showGrid && (
        <Grid 
          args={[dimensions.width, dimensions.depth]} 
          cellSize={0.5} 
          cellThickness={0.4}
          cellColor="#555555"
          sectionSize={1}
          sectionThickness={1}
          sectionColor="#777777"
          fadeDistance={30}
          fadeStrength={1}
          infiniteGrid={false}
        />
      )}

      {/* ============ CEILING ============ */}
      <mesh receiveShadow rotation={[Math.PI / 2, 0, 0]} position={[0, dimensions.height, 0]}>
        <planeGeometry args={[dimensions.width, dimensions.depth]} />
        <meshStandardMaterial color={colors.ceiling} roughness={0.98} metalness={0} />
      </mesh>

      {/* Ceiling light fixture */}
      <group position={[0, dimensions.height - 0.05, 0]}>
        {/* Ceiling medallion */}
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.3, 0.35, 0.03, 32]} />
          <meshStandardMaterial color="#f0f0f0" roughness={0.7} />
        </mesh>
        {/* Light bulb glow */}
        <pointLight position={[0, -0.3, 0]} intensity={0.8} color="#FFF8E7" distance={8} decay={2} />
      </group>

      {/* ============ BACK WALL ============ */}
      <mesh receiveShadow position={[0, dimensions.height / 2, -dimensions.depth / 2]}>
        <planeGeometry args={[dimensions.width, dimensions.height, 64, 64]} />
        <meshStandardMaterial 
          color={colors.walls} 
          roughness={0.95} 
          metalness={0}
          envMapIntensity={0.12}
        />
      </mesh>

      {/* ============ LEFT WALL ============ */}
      <mesh receiveShadow rotation={[0, Math.PI / 2, 0]} position={[-dimensions.width / 2, dimensions.height / 2, 0]}>
        <planeGeometry args={[dimensions.depth, dimensions.height]} />
        <meshStandardMaterial 
          color={`#${wallColorLeft.getHexString()}`} 
          roughness={0.92} 
          metalness={0} 
          envMapIntensity={0.15} 
        />
      </mesh>

      {/* ============ RIGHT WALL ============ */}
      <mesh receiveShadow rotation={[0, -Math.PI / 2, 0]} position={[dimensions.width / 2, dimensions.height / 2, 0]}>
        <planeGeometry args={[dimensions.depth, dimensions.height]} />
        <meshStandardMaterial 
          color={`#${wallColorRight.getHexString()}`} 
          roughness={0.92} 
          metalness={0} 
          envMapIntensity={0.15} 
        />
      </mesh>

      {/* Corner accent lights */}
      <pointLight position={[-dimensions.width/2 + 0.5, dimensions.height - 0.5, -dimensions.depth/2 + 0.5]} intensity={0.12} color="#FFF5E6" distance={4} />
      <pointLight position={[dimensions.width/2 - 0.5, dimensions.height - 0.5, -dimensions.depth/2 + 0.5]} intensity={0.12} color="#FFF5E6" distance={4} />
    </group>
  );
}

// Production-Quality Scene Component
function Scene({ 
  dimensions, 
  colors, 
  furniture, 
  selectedId,
  onFurnitureClick,
  lighting,
  roomImageUrl,
  listingFurnitureUrl,
  showGrid = true
}: any) {
  // Use refs for lights to update them imperatively for better performance
  const ambientRef = useRef<THREE.AmbientLight>(null);
  const directionalRef = useRef<THREE.DirectionalLight>(null);
  const fillLightRef = useRef<THREE.DirectionalLight>(null);
  const rimLightRef = useRef<THREE.DirectionalLight>(null);
  const pointLight1Ref = useRef<THREE.PointLight>(null);
  const pointLight2Ref = useRef<THREE.PointLight>(null);
  const hemiRef = useRef<THREE.HemisphereLight>(null);

  // Update lights when lighting state changes
  useFrame(() => {
    if (ambientRef.current) {
      ambientRef.current.intensity = lighting.ambient * 0.8;
    }
    if (directionalRef.current) {
      directionalRef.current.intensity = lighting.directional * 1.2;
    }
    if (fillLightRef.current) {
      fillLightRef.current.intensity = lighting.directional * 0.4;
    }
    if (rimLightRef.current) {
      rimLightRef.current.intensity = lighting.directional * 0.3;
    }
    if (pointLight1Ref.current) {
      pointLight1Ref.current.intensity = lighting.point * 0.6;
    }
    if (pointLight2Ref.current) {
      pointLight2Ref.current.intensity = lighting.point * 0.4;
    }
    if (hemiRef.current) {
      hemiRef.current.intensity = lighting.hemisphere * 0.6;
    }
  });

  return (
    <>
      {/* ============ PRODUCTION SOFT SHADOWS ============ */}
      <SoftShadows size={40} samples={20} focus={0.5} />
      
      {/* ============ PRODUCTION LIGHTING SETUP ============ */}
      {/* Base ambient light */}
      <ambientLight ref={ambientRef} intensity={lighting.ambient * 0.8} color="#FFF8F0" />
      
      {/* Main key light (sun simulation) */}
      <directionalLight 
        ref={directionalRef}
        position={[8, 10, 5]} 
        intensity={lighting.directional * 1.2}
        castShadow
        shadow-mapSize-width={4096}
        shadow-mapSize-height={4096}
        shadow-camera-far={50}
        shadow-camera-left={-10}
        shadow-camera-right={10}
        shadow-camera-top={10}
        shadow-camera-bottom={-10}
        shadow-bias={-0.0001}
        color="#FFF8E0"
      />
      
      {/* Fill light (window simulation) */}
      <directionalLight 
        ref={fillLightRef}
        position={[-5, 4, 3]} 
        intensity={lighting.directional * 0.4}
        color="#E8F0FF"
      />
      
      {/* Rim/back light for depth */}
      <directionalLight 
        ref={rimLightRef}
        position={[0, 5, -5]} 
        intensity={lighting.directional * 0.3}
        color="#FFE8D0"
      />
      
      {/* Point lights for local illumination */}
      <pointLight ref={pointLight1Ref} position={[-3, 3, 3]} intensity={lighting.point * 0.6} color="#FFF5E6" decay={2} distance={8} />
      <pointLight ref={pointLight2Ref} position={[3, 3, 3]} intensity={lighting.point * 0.4} color="#E8F0FF" decay={2} distance={8} />
      
      {/* Hemisphere light for realistic sky/ground bounce */}
      <hemisphereLight 
        ref={hemiRef}
        args={['#87CEEB', '#8B7355', lighting.hemisphere * 0.6]} 
      />

      {/* ============ ROOM ============ */}
      <Room3D 
        dimensions={dimensions} 
        colors={colors} 
        showGrid={showGrid}
        roomImageUrl={roomImageUrl}
      />

      {/* ============ ACCUMULATIVE SHADOWS FOR PHOTOREALISM ============ */}
      <AccumulativeShadows
        temporal
        frames={100}
        alphaTest={0.85}
        opacity={0.75}
        scale={dimensions.width * 2}
        position={[0, 0.01, 0]}
        color="#000000"
      >
        <RandomizedLight
          amount={8}
          radius={5}
          ambient={0.5}
          intensity={1}
          position={[8, 10, 5]}
          bias={0.001}
        />
      </AccumulativeShadows>

      {/* ============ FURNITURE ITEMS ============ */}
      {furniture.map((item: FurnitureObject) => {
        // If item has imageUrl, render image-based 3D furniture with dragging
        if (item.imageUrl) {
          return (
            <DraggableImageFurniture
              key={item.id}
              furniture={item}
              isSelected={item.id === selectedId}
              roomDimensions={dimensions}
              onPositionChange={(newPos: [number, number, number]) => {
                const event = new CustomEvent('furnitureMove', { 
                  detail: { id: item.id, position: newPos } 
                });
                window.dispatchEvent(event);
              }}
              onClick={() => onFurnitureClick(item.id)}
            />
          );
        }
        
        // Fallback to draggable procedural furniture
        return (
          <DraggableFurniture
            key={item.id}
            furniture={item}
            isSelected={item.id === selectedId}
            roomDimensions={dimensions}
            onPositionChange={(newPos: [number, number, number]) => {
              const event = new CustomEvent('furnitureMove', { 
                detail: { id: item.id, position: newPos } 
              });
              window.dispatchEvent(event);
            }}
            onClick={() => onFurnitureClick(item.id)}
          />
        );
      })}

      {/* ============ CAMERA CONTROLS ============ */}
      <OrbitControls 
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        minDistance={2}
        maxDistance={25}
        maxPolarAngle={Math.PI / 2.1}
        minPolarAngle={Math.PI / 6}
        dampingFactor={0.05}
        enableDamping={true}
        target={[0, 0.5, 0]}
      />
      
      {/* ============ ENVIRONMENT FOR REALISTIC REFLECTIONS ============ */}
      <Environment
        background={false}
        blur={0.8}
        preset="apartment"
      />
      
      {/* Subtle fog for depth perception */}
      <fog attach="fog" args={['#f8f8f8', 15, 30]} />
    </>
  );
}

export function Advanced3DARViewer({ listingId, listingTitle, category, price, furnitureImageUrl, furnitureType: propFurnitureType }: Advanced3DARViewerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [roomImage, setRoomImage] = useState<File | null>(null);
  const [roomImageUrl, setRoomImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [activeTab, setActiveTab] = useState('setup');
  
  // Listing furniture image state
  const [listingFurnitureUrl, setListingFurnitureUrl] = useState<string | null>(furnitureImageUrl || null);
  const [detectedFurnitureType, setDetectedFurnitureType] = useState<'sofa' | 'chair' | 'table' | 'bed' | 'cabinet' | 'lamp' | 'plant' | 'rug'>('sofa');
  const [furnitureAnalyzed, setFurnitureAnalyzed] = useState(false);
  const [extractedFurnitureColor, setExtractedFurnitureColor] = useState<string>('#808080');
  
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
  
  // Room analysis state
  const [roomAnalysis, setRoomAnalysis] = useState<RoomAnalysis | null>(null);
  const [showGrid, setShowGrid] = useState(true);

  // Single furniture from listing (not multiple)
  const [furniture, setFurniture] = useState<FurnitureObject[]>([]);
  const [selectedFurnitureId, setSelectedFurnitureId] = useState<string | null>(null);
  const [furnitureMaterial, setFurnitureMaterial] = useState('fabric');
  const [furnitureColor, setFurnitureColor] = useState('#808080');
  const [furnitureType, setFurnitureType] = useState<'sofa' | 'chair' | 'table' | 'bed' | 'cabinet' | 'lamp' | 'plant' | 'rug'>('sofa');

  // Lighting state
  const [lighting, setLighting] = useState({
    ambient: 0.6,
    directional: 1.0,
    point: 0.5,
    hemisphere: 0.4
  });

  // AI Suggestions state
  const [aiSuggestions, setAiSuggestions] = useState<AISuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(true);

  // Saved configurations state
  const [savedConfigs, setSavedConfigs] = useState<SavedRoomConfig[]>([]);
  const [savingConfig, setSavingConfig] = useState(false);
  const [configName, setConfigName] = useState('');
  const [showGallery, setShowGallery] = useState(false);
  const [loadingGallery, setLoadingGallery] = useState(false);

  // Get auth from localStorage
  const token = localStorage.getItem('authToken');
  const user = localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')!) : null;

  const fileInputRef = useRef<HTMLInputElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { toast } = useToast();

  // Detect furniture type from listing title
  const detectFurnitureTypeFromTitle = (title: string): 'sofa' | 'chair' | 'table' | 'bed' | 'cabinet' | 'lamp' | 'plant' | 'rug' => {
    const lowerTitle = title.toLowerCase();
    
    if (lowerTitle.includes('sofa') || lowerTitle.includes('couch') || lowerTitle.includes('settee')) return 'sofa';
    if (lowerTitle.includes('chair') || lowerTitle.includes('seat') || lowerTitle.includes('stool') || lowerTitle.includes('armchair')) return 'chair';
    if (lowerTitle.includes('table') || lowerTitle.includes('desk') || lowerTitle.includes('coffee')) return 'table';
    if (lowerTitle.includes('bed') || lowerTitle.includes('mattress') || lowerTitle.includes('cot')) return 'bed';
    if (lowerTitle.includes('cabinet') || lowerTitle.includes('wardrobe') || lowerTitle.includes('cupboard') || lowerTitle.includes('shelf') || lowerTitle.includes('drawer') || lowerTitle.includes('almirah') || lowerTitle.includes('almari')) return 'cabinet';
    if (lowerTitle.includes('lamp') || lowerTitle.includes('light') || lowerTitle.includes('chandelier')) return 'lamp';
    if (lowerTitle.includes('plant') || lowerTitle.includes('flower') || lowerTitle.includes('pot')) return 'plant';
    if (lowerTitle.includes('rug') || lowerTitle.includes('carpet') || lowerTitle.includes('mat')) return 'rug';
    
    // Default based on common furniture
    return 'sofa';
  };

  // Extract dominant color from furniture image
  const extractFurnitureColor = async (imageUrl: string): Promise<string> => {
    return new Promise((resolve) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        if (!ctx) {
          resolve('#808080');
          return;
        }
        
        // Sample center region of image (where furniture likely is)
        const sampleSize = 100;
        canvas.width = sampleSize;
        canvas.height = sampleSize;
        
        // Draw center portion of image
        const startX = (img.width - img.width * 0.6) / 2;
        const startY = (img.height - img.height * 0.6) / 2;
        ctx.drawImage(img, startX, startY, img.width * 0.6, img.height * 0.6, 0, 0, sampleSize, sampleSize);
        
        const imageData = ctx.getImageData(0, 0, sampleSize, sampleSize);
        const pixels = imageData.data;
        
        // Simple color clustering
        let r = 0, g = 0, b = 0, count = 0;
        
        for (let i = 0; i < pixels.length; i += 4) {
          // Skip very bright (white/background) and very dark pixels
          const brightness = (pixels[i] + pixels[i + 1] + pixels[i + 2]) / 3;
          if (brightness > 30 && brightness < 230) {
            r += pixels[i];
            g += pixels[i + 1];
            b += pixels[i + 2];
            count++;
          }
        }
        
        if (count > 0) {
          r = Math.round(r / count);
          g = Math.round(g / count);
          b = Math.round(b / count);
          resolve(`#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`);
        } else {
          resolve('#808080');
        }
      };
      img.onerror = () => resolve('#808080');
      img.src = imageUrl;
    });
  };

  // Initialize listing furniture on mount
  useEffect(() => {
    const initializeFurniture = async () => {
      // Detect furniture type from title
      const detectedType = propFurnitureType 
        ? (propFurnitureType as 'sofa' | 'chair' | 'table' | 'bed' | 'cabinet' | 'lamp' | 'plant' | 'rug')
        : detectFurnitureTypeFromTitle(listingTitle);
      
      setDetectedFurnitureType(detectedType);
      setFurnitureType(detectedType);
      
      // Extract color from furniture image if available
      if (furnitureImageUrl) {
        const color = await extractFurnitureColor(furnitureImageUrl);
        setExtractedFurnitureColor(color);
        setFurnitureColor(color);
      }
      
      setFurnitureAnalyzed(true);
    };
    
    initializeFurniture();
  }, [listingTitle, furnitureImageUrl, propFurnitureType]);

  // Load saved configurations on mount
  useEffect(() => {
    loadSavedConfigs();
  }, []);

  // Update furniture color when color state changes
  useEffect(() => {
    if (selectedFurnitureId && furnitureColor) {
      setFurniture(prev => prev.map(item => 
        item.id === selectedFurnitureId 
          ? { ...item, color: furnitureColor }
          : item
      ));
    }
  }, [furnitureColor, selectedFurnitureId]);

  // Update furniture material when material state changes
  useEffect(() => {
    if (selectedFurnitureId && furnitureMaterial) {
      setFurniture(prev => prev.map(item => 
        item.id === selectedFurnitureId 
          ? { ...item, material: furnitureMaterial }
          : item
      ));
    }
  }, [furnitureMaterial, selectedFurnitureId]);

  // Generate AI suggestions when room analysis changes
  useEffect(() => {
    if (roomAnalysis) {
      console.log('🤖 Generating AI suggestions...');
      generateAISuggestions();
    }
  }, [roomAnalysis, furniture, price]);

  // Handle furniture position updates
  useEffect(() => {
    const handleFurnitureMove = (e: any) => {
      const { id, position } = e.detail;
      setFurniture(prev => prev.map(item => 
        item.id === id ? { ...item, position } : item
      ));
    };

    window.addEventListener('furnitureMove', handleFurnitureMove);
    return () => window.removeEventListener('furnitureMove', handleFurnitureMove);
  }, []);

  // Load saved room configurations from backend
  const loadSavedConfigs = async () => {
    if (!token) {
      // Load from localStorage if not logged in
      const localConfigs = localStorage.getItem(`ar_configs_${user?.id || 'guest'}`);
      if (localConfigs) {
        setSavedConfigs(JSON.parse(localConfigs));
      }
      return;
    }
    
    setLoadingGallery(true);
    try {
      const response = await fetch('/api/v1/ar-configs', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        // Convert backend snake_case to frontend camelCase
        const frontendConfigs: SavedRoomConfig[] = data.map((config: any) => ({
          id: config.id,
          name: config.name,
          listingId: config.listing_id,
          listingTitle: config.listing_title,
          thumbnail: config.thumbnail,
          roomDimensions: config.room_dimensions,
          roomColors: config.room_colors,
          furniture: config.furniture,
          lighting: config.lighting,
          roomAnalysis: config.room_analysis,
          createdAt: config.created_at,
          price: config.price
        }));
        setSavedConfigs(frontendConfigs);
      }
    } catch (error) {
      console.error('Failed to load saved configs:', error);
      // Load from localStorage as fallback
      const localConfigs = localStorage.getItem(`ar_configs_${user?.id}`);
      if (localConfigs) {
        setSavedConfigs(JSON.parse(localConfigs));
      }
    } finally {
      setLoadingGallery(false);
    }
  };

  // Save current room configuration
  const saveRoomConfig = async () => {
    if (!user) {
      toast({
        title: 'Login Required',
        description: 'Please login to save your room configurations',
        variant: 'destructive',
      });
      return;
    }

    if (!configName.trim()) {
      toast({
        title: 'Name Required',
        description: 'Please enter a name for your configuration',
        variant: 'destructive',
      });
      return;
    }

    setSavingConfig(true);

    const newConfig: SavedRoomConfig = {
      id: `config-${Date.now()}`,
      name: configName.trim(),
      listingId,
      listingTitle,
      roomDimensions,
      roomColors,
      furniture,
      lighting,
      roomAnalysis: roomAnalysis || undefined,
      createdAt: new Date().toISOString(),
      price,
    };

    try {
      // Try to save to backend - convert to snake_case for API
      const apiPayload = {
        name: configName.trim(),
        listing_id: listingId,
        listing_title: listingTitle,
        room_dimensions: {
          width: roomDimensions.width,
          depth: roomDimensions.depth,
          height: roomDimensions.height
        },
        room_colors: {
          floor: roomColors.floor,
          walls: roomColors.walls,
          ceiling: roomColors.ceiling,
          accent: roomColors.accent
        },
        furniture: furniture.map(f => ({
          id: f.id,
          type: f.type,
          position: f.position,
          rotation: f.rotation,
          scale: f.scale,
          color: f.color,
          material: f.material
        })),
        lighting: {
          ambient: lighting.ambient,
          directional: lighting.directional,
          point: lighting.point,
          hemisphere: lighting.hemisphere || 0.4
        },
        room_analysis: roomAnalysis || null,
        price: price
      };

      const response = await fetch('/api/v1/ar-configs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(apiPayload)
      });

      if (response.ok) {
        const savedConfig = await response.json();
        // Convert backend response to frontend format
        const frontendConfig: SavedRoomConfig = {
          id: savedConfig.id,
          name: savedConfig.name,
          listingId: savedConfig.listing_id,
          listingTitle: savedConfig.listing_title,
          thumbnail: savedConfig.thumbnail,
          roomDimensions: savedConfig.room_dimensions,
          roomColors: savedConfig.room_colors,
          furniture: savedConfig.furniture,
          lighting: savedConfig.lighting,
          roomAnalysis: savedConfig.room_analysis,
          createdAt: savedConfig.created_at,
          price: savedConfig.price
        };
        setSavedConfigs(prev => [...prev, frontendConfig]);
      } else {
        throw new Error('Backend save failed');
      }
    } catch (error) {
      // Fallback to localStorage
      const updatedConfigs = [...savedConfigs, newConfig];
      setSavedConfigs(updatedConfigs);
      localStorage.setItem(`ar_configs_${user.id}`, JSON.stringify(updatedConfigs));
    }

    toast({
      title: '✅ Configuration Saved!',
      description: `"${configName}" has been saved to your gallery`,
    });

    setConfigName('');
    setSavingConfig(false);
  };

  // Load a saved configuration
  const loadSavedConfig = (config: SavedRoomConfig) => {
    setRoomDimensions(config.roomDimensions);
    setRoomColors(config.roomColors);
    setFurniture(config.furniture);
    setLighting(config.lighting);
    if (config.roomAnalysis) {
      setRoomAnalysis(config.roomAnalysis);
    }
    setShowGallery(false);
    setActiveTab('customize');

    toast({
      title: '✅ Configuration Loaded',
      description: `"${config.name}" has been loaded`,
    });
  };

  // Delete a saved configuration
  const deleteSavedConfig = async (configId: string) => {
    try {
      await fetch(`/api/v1/ar-configs/${configId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
    } catch (error) {
      // Continue with local delete
    }

    const updatedConfigs = savedConfigs.filter(c => c.id !== configId);
    setSavedConfigs(updatedConfigs);
    localStorage.setItem(`ar_configs_${user?.id}`, JSON.stringify(updatedConfigs));

    toast({
      title: 'Configuration Deleted',
      description: 'The saved configuration has been removed',
    });
  };

  // Generate AI suggestions based on room analysis
  const generateAISuggestions = () => {
    if (!roomAnalysis) return;

    console.log('🤖 Generating AI suggestions...', { roomAnalysis, furnitureCount: furniture.length });

    const suggestions: AISuggestion[] = [];

    // Color matching suggestion
    if (roomAnalysis.dominantColors.length > 0) {
      const bestMatchColor = roomAnalysis.dominantColors[0];
      const complementaryColor = getComplementaryColor(bestMatchColor);
      
      suggestions.push({
        id: 'color-match',
        type: 'color',
        title: 'Perfect Color Match',
        description: `This furniture in ${roomAnalysis.colorPalette[0]?.name || 'neutral'} tones will blend beautifully with your room's ${roomAnalysis.ambiance} ambiance.`,
        confidence: 92,
        icon: 'palette',
        action: () => setFurnitureColor(bestMatchColor)
      });

      suggestions.push({
        id: 'color-contrast',
        type: 'color',
        title: 'Bold Contrast Option',
        description: `For a striking look, try a complementary ${getColorName(complementaryColor)} tone to create visual interest.`,
        confidence: 78,
        icon: 'sparkles',
        action: () => setFurnitureColor(complementaryColor)
      });
    }

    // Placement suggestion
    suggestions.push({
      id: 'placement-optimal',
      type: 'placement',
      title: 'Optimal Placement',
      description: `Based on your ${roomDimensions.width.toFixed(1)}m × ${roomDimensions.depth.toFixed(1)}m room, place furniture 0.5-1m from walls for best flow.`,
      confidence: 88,
      icon: 'move',
    });

    // Style suggestion
    suggestions.push({
      id: 'style-match',
      type: 'style',
      title: `${roomAnalysis.ambiance.charAt(0).toUpperCase() + roomAnalysis.ambiance.slice(1)} Style Match`,
      description: `Your room has a ${roomAnalysis.ambiance} feel. This ${listingTitle} complements that aesthetic perfectly.`,
      confidence: 85,
      icon: 'star',
    });

    // Value/Price justification
    if (price) {
      const valueScore = calculateValueScore(roomAnalysis, price);
      suggestions.push({
        id: 'value-assessment',
        type: 'value',
        title: valueScore >= 80 ? '🔥 Excellent Value!' : valueScore >= 60 ? '👍 Good Value' : '💡 Fair Price',
        description: getValueDescription(valueScore, price, roomAnalysis),
        confidence: valueScore,
        icon: 'thumbsup',
      });
    }

    // Lighting suggestion
    if (roomAnalysis.lightingCondition === 'dim') {
      suggestions.push({
        id: 'lighting-tip',
        type: 'style',
        title: 'Lighting Enhancement',
        description: 'Your room has dim lighting. Lighter colored furniture will brighten the space.',
        confidence: 82,
        icon: 'zap',
        action: () => setFurnitureColor('#E8E4E0')
      });
    }

    console.log('✅ AI Suggestions generated:', suggestions.length, 'suggestions');
    setAiSuggestions(suggestions);
  };

  // Auto-generate AI suggestions when room analysis is ready
  useEffect(() => {
    if (roomAnalysis && furniture.length > 0) {
      generateAISuggestions();
    }
  }, [roomAnalysis, furniture.length]);

  // Helper: Get complementary color
  const getComplementaryColor = (hex: string): string => {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    
    const compR = 255 - r;
    const compG = 255 - g;
    const compB = 255 - b;
    
    return `#${compR.toString(16).padStart(2, '0')}${compG.toString(16).padStart(2, '0')}${compB.toString(16).padStart(2, '0')}`;
  };

  // Helper: Generate harmonious color palette from a base color
  const generateHarmoniousColors = (baseHex: string): string[] => {
    const r = parseInt(baseHex.slice(1, 3), 16);
    const g = parseInt(baseHex.slice(3, 5), 16);
    const b = parseInt(baseHex.slice(5, 7), 16);
    
    // Convert to HSL
    const max = Math.max(r, g, b) / 255;
    const min = Math.min(r, g, b) / 255;
    const l = (max + min) / 2;
    let h = 0, s = 0;
    
    if (max !== min) {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      switch (max) {
        case r / 255: h = ((g / 255 - b / 255) / d + (g < b ? 6 : 0)) / 6; break;
        case g / 255: h = ((b / 255 - r / 255) / d + 2) / 6; break;
        case b / 255: h = ((r / 255 - g / 255) / d + 4) / 6; break;
      }
    }
    
    // Generate colors with different relationships
    const hslToHex = (h: number, s: number, l: number): string => {
      let r, g, b;
      if (s === 0) {
        r = g = b = l;
      } else {
        const hue2rgb = (p: number, q: number, t: number) => {
          if (t < 0) t += 1;
          if (t > 1) t -= 1;
          if (t < 1/6) return p + (q - p) * 6 * t;
          if (t < 1/2) return q;
          if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
          return p;
        };
        const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        const p = 2 * l - q;
        r = hue2rgb(p, q, h + 1/3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1/3);
      }
      return `#${Math.round(r * 255).toString(16).padStart(2, '0')}${Math.round(g * 255).toString(16).padStart(2, '0')}${Math.round(b * 255).toString(16).padStart(2, '0')}`;
    };
    
    return [
      hslToHex((h + 0.08) % 1, Math.min(s * 0.9, 1), l), // Analogous 1
      hslToHex((h - 0.08 + 1) % 1, Math.min(s * 0.9, 1), l), // Analogous 2
      hslToHex(h, s * 0.6, Math.min(l + 0.2, 0.95)), // Lighter shade
      hslToHex(h, s * 0.6, Math.max(l - 0.2, 0.15)), // Darker shade
      hslToHex((h + 0.5) % 1, s * 0.7, l), // Complementary (softer)
      hslToHex((h + 0.33) % 1, s * 0.5, Math.min(l + 0.1, 0.9)), // Triadic accent
    ];
  };

  // Helper: Get descriptive color name from hex
  const getColorName = (hex: string): string => {
    if (!hex || hex.length < 7) return 'Unknown';
    
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    
    // Convert to HSL for better color identification
    const max = Math.max(r, g, b) / 255;
    const min = Math.min(r, g, b) / 255;
    const l = (max + min) / 2;
    
    let h = 0, s = 0;
    if (max !== min) {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      switch (max) {
        case r / 255: h = ((g / 255 - b / 255) / d + (g < b ? 6 : 0)) * 60; break;
        case g / 255: h = ((b / 255 - r / 255) / d + 2) * 60; break;
        case b / 255: h = ((r / 255 - g / 255) / d + 4) * 60; break;
      }
    }
    
    // Determine lightness prefix
    let lightPrefix = '';
    if (l < 0.15) lightPrefix = 'Very Dark ';
    else if (l < 0.3) lightPrefix = 'Dark ';
    else if (l > 0.85) lightPrefix = 'Very Light ';
    else if (l > 0.7) lightPrefix = 'Light ';
    else if (l > 0.55) lightPrefix = 'Soft ';
    
    // Handle achromatic colors (grays, black, white)
    if (s < 0.1) {
      if (l < 0.1) return 'Charcoal Black';
      if (l < 0.2) return 'Onyx';
      if (l < 0.3) return 'Dark Slate';
      if (l < 0.4) return 'Graphite';
      if (l < 0.5) return 'Steel Gray';
      if (l < 0.6) return 'Ash Gray';
      if (l < 0.7) return 'Silver';
      if (l < 0.8) return 'Pearl Gray';
      if (l < 0.9) return 'Ivory';
      return 'Snow White';
    }
    
    // Determine saturation descriptor
    let satDesc = '';
    if (s < 0.25) satDesc = 'Muted ';
    else if (s < 0.5) satDesc = 'Dusty ';
    else if (s > 0.85) satDesc = 'Vivid ';
    else if (s > 0.7) satDesc = 'Rich ';
    
    // Get base color name from hue
    let baseName = '';
    if (h < 10 || h >= 350) {
      // Reds
      if (s > 0.7 && l > 0.4 && l < 0.6) baseName = 'Crimson';
      else if (l < 0.3) baseName = 'Burgundy';
      else if (l > 0.7) baseName = 'Rose';
      else if (s < 0.4) baseName = 'Mauve';
      else baseName = 'Red';
    } else if (h < 25) {
      // Red-Orange
      if (l > 0.6) baseName = 'Coral';
      else if (l < 0.35) baseName = 'Rust';
      else baseName = 'Vermillion';
    } else if (h < 40) {
      // Orange
      if (l > 0.7) baseName = 'Peach';
      else if (l < 0.4) baseName = 'Burnt Orange';
      else if (s > 0.8) baseName = 'Tangerine';
      else baseName = 'Orange';
    } else if (h < 50) {
      // Orange-Yellow
      if (l > 0.7) baseName = 'Apricot';
      else if (l < 0.4) baseName = 'Amber';
      else baseName = 'Gold';
    } else if (h < 65) {
      // Yellow
      if (l > 0.8) baseName = 'Cream';
      else if (l < 0.5) baseName = 'Mustard';
      else if (s > 0.7) baseName = 'Lemon';
      else baseName = 'Yellow';
    } else if (h < 80) {
      // Yellow-Green
      if (l > 0.7) baseName = 'Chartreuse';
      else if (l < 0.4) baseName = 'Olive';
      else baseName = 'Lime';
    } else if (h < 150) {
      // Green
      if (l < 0.25) baseName = 'Forest';
      else if (l > 0.7) baseName = 'Mint';
      else if (s < 0.4) baseName = 'Sage';
      else if (h < 100) baseName = 'Lime Green';
      else if (h < 130) baseName = 'Emerald';
      else baseName = 'Green';
    } else if (h < 180) {
      // Cyan/Teal
      if (l < 0.3) baseName = 'Deep Teal';
      else if (l > 0.7) baseName = 'Aqua';
      else if (s > 0.6) baseName = 'Turquoise';
      else baseName = 'Teal';
    } else if (h < 210) {
      // Cyan-Blue
      if (l > 0.7) baseName = 'Sky Blue';
      else if (l < 0.3) baseName = 'Petrol';
      else baseName = 'Cyan';
    } else if (h < 250) {
      // Blue
      if (l < 0.25) baseName = 'Navy';
      else if (l > 0.7) baseName = 'Powder Blue';
      else if (s > 0.7) baseName = 'Royal Blue';
      else if (s < 0.4) baseName = 'Steel Blue';
      else baseName = 'Blue';
    } else if (h < 280) {
      // Blue-Purple
      if (l < 0.3) baseName = 'Indigo';
      else if (l > 0.7) baseName = 'Periwinkle';
      else baseName = 'Violet';
    } else if (h < 320) {
      // Purple
      if (l < 0.3) baseName = 'Plum';
      else if (l > 0.7) baseName = 'Lavender';
      else if (s > 0.7) baseName = 'Purple';
      else baseName = 'Mauve';
    } else {
      // Magenta/Pink
      if (l > 0.7) baseName = 'Pink';
      else if (l < 0.3) baseName = 'Magenta';
      else if (s > 0.7) baseName = 'Hot Pink';
      else baseName = 'Fuchsia';
    }
    
    // Special case overrides for common furniture colors
    // Browns (low saturation oranges/yellows)
    if (h >= 20 && h <= 45 && s >= 0.2 && s <= 0.7 && l >= 0.15 && l <= 0.5) {
      if (l < 0.2) return 'Espresso';
      if (l < 0.3) return 'Chocolate';
      if (l < 0.35) return 'Walnut';
      if (l < 0.4) return 'Mahogany';
      if (l < 0.45) return 'Chestnut';
      return 'Caramel';
    }
    
    // Beiges/Tans
    if (h >= 25 && h <= 50 && s >= 0.1 && s <= 0.4 && l >= 0.5 && l <= 0.8) {
      if (l > 0.7) return 'Cream';
      if (l > 0.6) return 'Beige';
      return 'Tan';
    }
    
    // Build final name - avoid redundant prefixes
    if (lightPrefix && !baseName.includes('Dark') && !baseName.includes('Light')) {
      return `${lightPrefix}${baseName}`;
    }
    if (satDesc && baseName !== 'Mauve' && baseName !== 'Sage') {
      return `${satDesc}${baseName}`;
    }
    
    return baseName;
  };

  // Helper: Calculate value score
  const calculateValueScore = (analysis: RoomAnalysis, itemPrice: number): number => {
    let score = 70; // Base score
    
    // Higher score for better room fit
    if (analysis.ambiance === 'luxurious') score += 10;
    if (analysis.brightness > 60) score += 5;
    if (analysis.lightingCondition === 'natural') score += 5;
    
    // Price consideration (assuming furniture)
    if (itemPrice < 50000) score += 10; // Budget friendly
    else if (itemPrice < 150000) score += 5; // Mid-range
    
    return Math.min(100, score);
  };

  // Helper: Get value description
  const getValueDescription = (score: number, itemPrice: number, analysis: RoomAnalysis): string => {
    const priceStr = itemPrice.toLocaleString();
    
    if (score >= 80) {
      return `At PKR ${priceStr}, this piece offers exceptional quality for your ${analysis.ambiance} space. The style and colors are a perfect match!`;
    } else if (score >= 60) {
      return `Priced at PKR ${priceStr}, this furniture provides good value and fits well with your room's ${analysis.lightingCondition} lighting.`;
    } else {
      return `At PKR ${priceStr}, consider if the style matches your ${analysis.ambiance} aesthetic. It could work with some adjustments.`;
    }
  };

  // Only show for furniture
  if (category?.toLowerCase() !== 'furniture') {
    return null;
  }

  // Advanced color analysis utilities
  const rgbToHsl = (r: number, g: number, b: number): [number, number, number] => {
    r /= 255; g /= 255; b /= 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h = 0, s = 0;
    const l = (max + min) / 2;

    if (max !== min) {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      switch (max) {
        case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
        case g: h = ((b - r) / d + 2) / 6; break;
        case b: h = ((r - g) / d + 4) / 6; break;
      }
    }
    return [h * 360, s * 100, l * 100];
  };

  const getColorNameFromRGB = (r: number, g: number, b: number): string => {
    const [h, s, l] = rgbToHsl(r, g, b);
    
    // Handle achromatic colors
    if (s < 10) {
      if (l < 10) return 'Charcoal';
      if (l < 20) return 'Onyx';
      if (l < 30) return 'Dark Slate';
      if (l < 40) return 'Graphite';
      if (l < 50) return 'Steel Gray';
      if (l < 60) return 'Ash Gray';
      if (l < 70) return 'Silver';
      if (l < 80) return 'Pearl';
      if (l < 90) return 'Ivory';
      return 'Snow White';
    }
    
    // Browns - special handling for furniture-common colors
    if (h >= 20 && h <= 45 && s >= 15 && s <= 70 && l >= 10 && l <= 50) {
      if (l < 18) return 'Espresso';
      if (l < 25) return 'Chocolate';
      if (l < 32) return 'Walnut';
      if (l < 38) return 'Mahogany';
      if (l < 45) return 'Chestnut';
      return 'Caramel';
    }
    
    // Beige/Tan tones
    if (h >= 25 && h <= 50 && s >= 10 && s <= 40 && l >= 50 && l <= 85) {
      if (l > 75) return 'Cream';
      if (l > 65) return 'Beige';
      if (l > 55) return 'Tan';
      return 'Sand';
    }
    
    // Determine saturation prefix
    let satPrefix = '';
    if (s < 25) satPrefix = 'Muted ';
    else if (s < 40) satPrefix = 'Soft ';
    else if (s > 80) satPrefix = 'Vivid ';
    else if (s > 65) satPrefix = 'Rich ';
    
    // Determine lightness prefix
    let lightPrefix = '';
    if (l < 20) lightPrefix = 'Deep ';
    else if (l < 35) lightPrefix = 'Dark ';
    else if (l > 80) lightPrefix = 'Pale ';
    else if (l > 65) lightPrefix = 'Light ';
    
    // Get base color from hue
    let baseName = '';
    if (h < 10 || h >= 350) {
      if (l > 70) baseName = 'Rose';
      else if (l < 30) baseName = 'Burgundy';
      else baseName = 'Red';
    } else if (h < 25) {
      if (l > 65) baseName = 'Coral';
      else if (l < 35) baseName = 'Rust';
      else baseName = 'Vermillion';
    } else if (h < 40) {
      if (l > 70) baseName = 'Peach';
      else if (l < 40) baseName = 'Burnt Orange';
      else baseName = 'Orange';
    } else if (h < 55) {
      if (l > 75) baseName = 'Cream';
      else if (l < 45) baseName = 'Amber';
      else baseName = 'Gold';
    } else if (h < 70) {
      if (l > 80) baseName = 'Lemon';
      else if (l < 50) baseName = 'Mustard';
      else baseName = 'Yellow';
    } else if (h < 85) {
      if (l < 40) baseName = 'Olive';
      else baseName = 'Chartreuse';
    } else if (h < 150) {
      if (l < 25) baseName = 'Forest';
      else if (l > 70) baseName = 'Mint';
      else if (s < 40) baseName = 'Sage';
      else if (h < 120) baseName = 'Lime';
      else baseName = 'Emerald';
    } else if (h < 180) {
      if (l > 70) baseName = 'Aqua';
      else if (l < 35) baseName = 'Deep Teal';
      else baseName = 'Teal';
    } else if (h < 210) {
      if (l > 70) baseName = 'Sky Blue';
      else baseName = 'Cyan';
    } else if (h < 250) {
      if (l < 25) baseName = 'Navy';
      else if (l > 70) baseName = 'Powder Blue';
      else if (s > 60) baseName = 'Royal Blue';
      else baseName = 'Blue';
    } else if (h < 280) {
      if (l < 30) baseName = 'Indigo';
      else if (l > 70) baseName = 'Periwinkle';
      else baseName = 'Violet';
    } else if (h < 320) {
      if (l < 30) baseName = 'Plum';
      else if (l > 70) baseName = 'Lavender';
      else baseName = 'Purple';
    } else {
      if (l > 70) baseName = 'Pink';
      else if (s > 70) baseName = 'Magenta';
      else baseName = 'Fuchsia';
    }
    
    // Combine prefixes intelligently
    if (lightPrefix && !baseName.includes('Deep') && !baseName.includes('Dark') && !baseName.includes('Light') && !baseName.includes('Pale')) {
      return `${lightPrefix}${baseName}`;
    }
    if (satPrefix && s < 50) {
      return `${satPrefix}${baseName}`;
    }
    
    return baseName;
  };

  // Analyze uploaded room image with advanced feature extraction
  const analyzeRoomImage = async (imageFile: File) => {
    setLoading(true);
    setAnalysisProgress(0);

    try {
      const img = new Image();
      const imageUrl = URL.createObjectURL(imageFile);
      img.src = imageUrl;
      setRoomImageUrl(imageUrl);
      
      await new Promise((resolve) => { img.onload = resolve; });

      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d')!;
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);

      setAnalysisProgress(10);
      await new Promise(resolve => setTimeout(resolve, 200));

      // Get image data
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const pixels = imageData.data;

      setAnalysisProgress(20);

      // Advanced color extraction with clustering
      const colorClusters: { r: number; g: number; b: number; count: number }[] = [];
      const sampleRate = 10; // Sample every 10th pixel

      for (let i = 0; i < pixels.length; i += 4 * sampleRate) {
        const r = pixels[i];
        const g = pixels[i + 1];
        const b = pixels[i + 2];
        const a = pixels[i + 3];
        
        if (a < 128) continue; // Skip transparent pixels

        // Find or create cluster
        let found = false;
        for (const cluster of colorClusters) {
          const dist = Math.sqrt(
            Math.pow(cluster.r - r, 2) +
            Math.pow(cluster.g - g, 2) +
            Math.pow(cluster.b - b, 2)
          );
          if (dist < 40) { // Cluster threshold
            cluster.r = (cluster.r * cluster.count + r) / (cluster.count + 1);
            cluster.g = (cluster.g * cluster.count + g) / (cluster.count + 1);
            cluster.b = (cluster.b * cluster.count + b) / (cluster.count + 1);
            cluster.count++;
            found = true;
            break;
          }
        }
        if (!found && colorClusters.length < 20) {
          colorClusters.push({ r, g, b, count: 1 });
        }
      }

      setAnalysisProgress(40);
      await new Promise(resolve => setTimeout(resolve, 200));

      // Sort by frequency
      colorClusters.sort((a, b) => b.count - a.count);
      const totalPixels = colorClusters.reduce((sum, c) => sum + c.count, 0);

      // Create color palette
      const colorPalette = colorClusters.slice(0, 8).map(c => ({
        color: `#${Math.round(c.r).toString(16).padStart(2, '0')}${Math.round(c.g).toString(16).padStart(2, '0')}${Math.round(c.b).toString(16).padStart(2, '0')}`,
        percentage: Math.round((c.count / totalPixels) * 100),
        name: getColorNameFromRGB(c.r, c.g, c.b)
      }));

      setAnalysisProgress(60);

      // Calculate brightness (0-100)
      let totalBrightness = 0;
      for (let i = 0; i < pixels.length; i += 4 * sampleRate) {
        totalBrightness += (pixels[i] * 0.299 + pixels[i + 1] * 0.587 + pixels[i + 2] * 0.114) / 255;
      }
      const brightness = Math.round((totalBrightness / (pixels.length / (4 * sampleRate))) * 100);

      // Calculate warmth (-100 to +100)
      let totalWarmth = 0;
      for (let i = 0; i < pixels.length; i += 4 * sampleRate) {
        totalWarmth += (pixels[i] - pixels[i + 2]); // Red - Blue
      }
      const warmth = Math.round((totalWarmth / (pixels.length / (4 * sampleRate))) / 2.55);

      setAnalysisProgress(75);

      // Detect room style based on colors
      let detectedStyle = 'modern';
      if (warmth > 30 && brightness < 60) detectedStyle = 'traditional';
      else if (brightness > 75) detectedStyle = 'minimalist';
      else if (warmth < -20) detectedStyle = 'industrial';
      else if (warmth > 40 && brightness > 50) detectedStyle = 'cozy';

      // Detect ambiance
      let ambiance: RoomAnalysis['ambiance'] = 'modern';
      if (brightness > 70 && warmth > 10) ambiance = 'cozy';
      else if (brightness > 75 && warmth < 10) ambiance = 'minimalist';
      else if (brightness < 50 && warmth < 0) ambiance = 'industrial';
      else if (brightness > 60 && warmth > 30) ambiance = 'traditional';
      else if (brightness > 65 && colorPalette.some(c => c.name === 'Purple' || c.name === 'Blue')) ambiance = 'luxurious';

      // Detect lighting condition
      let lightingCondition: RoomAnalysis['lightingCondition'] = 'moderate';
      if (brightness > 75) lightingCondition = 'bright';
      else if (brightness < 40) lightingCondition = 'dim';
      else if (warmth > 25) lightingCondition = 'natural';
      else if (warmth < -10) lightingCondition = 'artificial';

      setAnalysisProgress(85);

      // Suggest furniture colors based on room colors
      const suggestedFurnitureColors = colorPalette.slice(0, 3).map(c => {
        // Create complementary/harmonious colors
        const [h, s, l] = rgbToHsl(
          parseInt(c.color.substring(1, 3), 16),
          parseInt(c.color.substring(3, 5), 16),
          parseInt(c.color.substring(5, 7), 16)
        );
        // Shift hue slightly for harmony
        const newH = (h + 30) % 360;
        const newL = l > 50 ? l - 20 : l + 20;
        return `hsl(${newH}, ${Math.min(s + 10, 100)}%, ${newL}%)`;
      });

      // Detect potential objects in room (simplified - based on color regions)
      const detectedObjects: string[] = [];
      if (colorPalette.some(c => c.name === 'Green' && c.percentage > 5)) detectedObjects.push('Plants');
      if (colorPalette.some(c => (c.name === 'White' || c.name === 'Light Gray') && c.percentage > 30)) detectedObjects.push('Windows/Natural Light');
      if (colorPalette.some(c => c.name.includes('Brown') || c.name === 'Orange') && warmth > 20) detectedObjects.push('Wooden Elements');

      setAnalysisProgress(95);

      // Generate complementary/suggested colors
      const extractedColors = colorPalette.slice(0, 6).map(c => c.color);
      const suggestedColors = colorPalette.slice(0, 4).map(c => {
        // Get complementary color
        const r = parseInt(c.color.substring(1, 3), 16);
        const g = parseInt(c.color.substring(3, 5), 16);
        const b = parseInt(c.color.substring(5, 7), 16);
        // Shift to complementary
        const compR = Math.min(255, Math.max(0, 255 - r));
        const compG = Math.min(255, Math.max(0, 255 - g));
        const compB = Math.min(255, Math.max(0, 255 - b));
        // Blend with neutral for softer match
        const blendR = Math.round((compR + 128) / 2);
        const blendG = Math.round((compG + 128) / 2);
        const blendB = Math.round((compB + 128) / 2);
        return `#${blendR.toString(16).padStart(2, '0')}${blendG.toString(16).padStart(2, '0')}${blendB.toString(16).padStart(2, '0')}`;
      });

      // Estimate room size based on brightness and color distribution
      const roomSizeEstimate = brightness > 70 ? 'Large' : brightness > 45 ? 'Medium' : 'Small';

      // Create room analysis object
      const analysis: RoomAnalysis = {
        dominantColors: colorPalette.slice(0, 5).map(c => c.color),
        colorPalette,
        brightness,
        warmth,
        detectedStyle,
        style: detectedStyle, // Simplified style name
        detectedObjects,
        ambiance,
        lightingCondition,
        suggestedFurnitureColors,
        extractedColors,
        suggestedColors,
        roomType: brightness > 60 ? 'Living Room' : 'Bedroom',
        estimatedSize: roomSizeEstimate
      };

      setRoomAnalysis(analysis);

      // Set room colors based on analysis
      const floorColor = colorPalette.find(c => c.percentage > 15 && (c.name.includes('Brown') || c.name.includes('Gray')))?.color || colorPalette[0]?.color || '#8B7355';
      const wallColor = colorPalette.find(c => c.percentage > 10 && (c.name.includes('White') || c.name.includes('Gray') || c.name === 'Beige'))?.color || colorPalette[1]?.color || '#F5F5DC';
      
      setRoomColors({
        floor: floorColor,
        walls: wallColor,
        ceiling: '#FFFFFF',
        accent: colorPalette[2]?.color || '#4A90E2'
      });

      // Set furniture color to complement room
      if (suggestedFurnitureColors.length > 0) {
        setFurnitureColor(colorPalette[0]?.color || '#808080');
      }

      // Adjust lighting based on analysis
      setLighting({
        ambient: brightness > 60 ? 0.7 : 0.5,
        directional: brightness > 60 ? 0.9 : 1.2,
        point: 0.5,
        hemisphere: warmth > 0 ? 0.5 : 0.3
      });

      // Estimate room dimensions
      const estimatedDimensions = estimateRoomDimensions(imageData);
      setRoomDimensions(estimatedDimensions);

      setAnalysisProgress(100);

      toast({
        title: '✨ Advanced Room Analysis Complete!',
        description: `${analysis.roomType} detected • ${ambiance} ambiance • ${lightingCondition} lighting`,
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

  // Advanced room dimension estimation with perspective analysis
  const estimateRoomDimensions = (imageData: ImageData): RoomDimensions => {
    const { width: imgWidth, height: imgHeight } = imageData;
    const aspectRatio = imgWidth / imgHeight;
    
    // Analyze image for depth cues
    const pixels = imageData.data;
    let topBrightness = 0;
    let bottomBrightness = 0;
    let leftDensity = 0;
    let rightDensity = 0;
    
    // Sample top third
    for (let y = 0; y < imgHeight / 3; y++) {
      for (let x = 0; x < imgWidth; x += 5) {
        const idx = (y * imgWidth + x) * 4;
        topBrightness += (pixels[idx] + pixels[idx + 1] + pixels[idx + 2]) / 3;
      }
    }
    
    // Sample bottom third
    for (let y = (imgHeight * 2) / 3; y < imgHeight; y++) {
      for (let x = 0; x < imgWidth; x += 5) {
        const idx = (y * imgWidth + x) * 4;
        bottomBrightness += (pixels[idx] + pixels[idx + 1] + pixels[idx + 2]) / 3;
      }
    }
    
    // Sample left and right edges for perspective
    for (let y = 0; y < imgHeight; y += 5) {
      for (let x = 0; x < imgWidth / 5; x++) {
        const idx = (y * imgWidth + x) * 4;
        leftDensity += (pixels[idx] + pixels[idx + 1] + pixels[idx + 2]) / 3;
      }
      for (let x = (imgWidth * 4) / 5; x < imgWidth; x++) {
        const idx = (y * imgWidth + x) * 4;
        rightDensity += (pixels[idx] + pixels[idx + 1] + pixels[idx + 2]) / 3;
      }
    }
    
    // Normalize
    topBrightness /= ((imgHeight / 3) * (imgWidth / 5));
    bottomBrightness /= ((imgHeight / 3) * (imgWidth / 5));
    leftDensity /= ((imgHeight / 5) * (imgWidth / 5));
    rightDensity /= ((imgHeight / 5) * (imgWidth / 5));
    
    // Calculate perspective factor
    const depthFactor = bottomBrightness > topBrightness ? 1.15 : 0.95;
    const widthFactor = Math.abs(leftDensity - rightDensity) > 20 ? 1.2 : 1.0;
    
    // Base dimensions based on aspect ratio
    let baseWidth = 5.5;
    let baseDepth = 4.5;
    let baseHeight = 2.8;
    
    if (aspectRatio > 1.6) {
      // Wide panoramic view
      baseWidth = 7.5 * widthFactor;
      baseDepth = 5.5 * depthFactor;
      baseHeight = 3.0;
    } else if (aspectRatio > 1.2) {
      // Standard landscape
      baseWidth = 6.0 * widthFactor;
      baseDepth = 5.0 * depthFactor;
      baseHeight = 2.9;
    } else if (aspectRatio < 0.8) {
      // Portrait/narrow view
      baseWidth = 4.5;
      baseDepth = 6.0 * depthFactor;
      baseHeight = 3.2;
    }
    
    return {
      width: baseWidth,
      depth: baseDepth,
      height: baseHeight
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

  // Add the listing's furniture to the 3D room
  const addListingFurniture = () => {
    const imageUrlToUse = listingFurnitureUrl || furnitureImageUrl;
    console.log('🪑 Adding listing furniture:', {
      type: detectedFurnitureType,
      imageUrl: imageUrlToUse,
      listingFurnitureUrl,
      furnitureImageUrl,
      hasImage: !!imageUrlToUse
    });
    
    const newItem: FurnitureObject = {
      id: `listing-furniture-${listingId}-${Date.now()}`, // Unique ID each time
      type: detectedFurnitureType,
      position: [0, 0, 0], // Center of room
      rotation: [0, 0, 0],
      scale: [1, 1, 1],
      color: extractedFurnitureColor || furnitureColor,
      material: furnitureMaterial,
      imageUrl: imageUrlToUse || undefined // Use the listing's product image
    };

    console.log('🪑 Created furniture item:', newItem);
    
    // Replace all furniture with just the listing furniture
    setFurniture([newItem]);
    setSelectedFurnitureId(newItem.id);
    
    // Generate AI suggestions after adding furniture
    setTimeout(() => generateAISuggestions(), 500);
    
    toast({
      title: `${listingTitle} Added to Room`,
      description: `${detectedFurnitureType.charAt(0).toUpperCase() + detectedFurnitureType.slice(1)} placed in center. Drag to reposition.`,
    });
  };

  // Auto-add furniture when room is analyzed
  useEffect(() => {
    if (roomAnalysis && furnitureAnalyzed) {
      addListingFurniture();
    }
  }, [roomAnalysis, furnitureAnalyzed]);

  const addFurniture = () => {
    const newItem: FurnitureObject = {
      id: `furniture-${Date.now()}`,
      type: furnitureType,
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
      title: `${furnitureType.charAt(0).toUpperCase() + furnitureType.slice(1)} Added`,
      description: 'Click to select, drag to move',
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
    const removed = furniture.find(item => item.id === selectedFurnitureId);
    setFurniture(furniture.filter(item => item.id !== selectedFurnitureId));
    setSelectedFurnitureId(null);
    toast({
      title: 'Furniture Removed',
      description: `${removed?.type || 'Item'} has been removed from the room`,
    });
  };

  const clearAllFurniture = () => {
    setFurniture([]);
    setSelectedFurnitureId(null);
    toast({
      title: 'Room Cleared',
      description: 'All furniture has been removed',
    });
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

      <DialogContent className="max-w-7xl h-[90vh] p-0 flex flex-col overflow-hidden">
        <DialogHeader className="p-6 pb-4 border-b flex-shrink-0">
          <DialogTitle className="text-2xl flex items-center gap-2">
            <Cpu className="h-6 w-6 text-purple-600" />
            Advanced 3D AR Furniture Preview
          </DialogTitle>
          <DialogDescription>
            AI-powered room analysis • Realistic 3D placement • True-to-scale visualization
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col min-h-0 overflow-hidden">
          <TabsList className="mx-6 mt-4 flex-shrink-0">
            <TabsTrigger value="setup" className="gap-2">
              <Upload className="h-4 w-4" />
              Room Setup
            </TabsTrigger>
            <TabsTrigger value="customize" className="gap-2">
              <Box className="h-4 w-4" />
              3D Preview
            </TabsTrigger>
            <TabsTrigger value="suggestions" className="gap-2">
              <Sparkles className="h-4 w-4" />
              AI Suggestions
            </TabsTrigger>
            <TabsTrigger value="gallery" className="gap-2">
              <FolderOpen className="h-4 w-4" />
              My Gallery
              {savedConfigs.length > 0 && (
                <Badge variant="secondary" className="ml-1 h-5 px-1.5">{savedConfigs.length}</Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="settings" className="gap-2">
              <Palette className="h-4 w-4" />
              Settings
            </TabsTrigger>
          </TabsList>

          {/* Setup Tab */}
          <TabsContent value="setup" className="flex-1 p-4 overflow-y-auto min-h-0">
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

              {/* Listing Furniture Preview */}
              <Card className="md:col-span-2 border-2 border-purple-200 bg-purple-50/50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Box className="h-5 w-5 text-purple-600" />
                    Furniture to Preview: {listingTitle}
                  </CardTitle>
                  <CardDescription>This furniture will be placed in your 3D room</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-start gap-6">
                    {/* Furniture Image */}
                    <div className="w-48 h-48 rounded-lg border-2 border-gray-200 overflow-hidden bg-white flex-shrink-0">
                      {furnitureImageUrl ? (
                        <img 
                          src={furnitureImageUrl} 
                          alt={listingTitle}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-gray-100">
                          <Box className="h-16 w-16 text-gray-300" />
                        </div>
                      )}
                    </div>
                    
                    {/* Furniture Details */}
                    <div className="flex-1 space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label className="text-gray-500 text-xs">Detected Type</Label>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge className="bg-purple-100 text-purple-700 text-sm">
                              {detectedFurnitureType.charAt(0).toUpperCase() + detectedFurnitureType.slice(1)}
                            </Badge>
                            {furnitureAnalyzed && <Check className="h-4 w-4 text-green-500" />}
                          </div>
                        </div>
                        <div>
                          <Label className="text-gray-500 text-xs">Extracted Color</Label>
                          <div className="flex items-center gap-2 mt-1">
                            <div 
                              className="w-8 h-8 rounded-lg border-2 border-white shadow-md"
                              style={{ backgroundColor: extractedFurnitureColor }}
                            />
                            <span className="text-sm text-gray-600">{extractedFurnitureColor}</span>
                          </div>
                        </div>
                      </div>
                      
                      {price && (
                        <div>
                          <Label className="text-gray-500 text-xs">Price</Label>
                          <p className="text-xl font-bold text-green-600">EGP {price.toLocaleString()}</p>
                        </div>
                      )}
                      
                      <div className="pt-2">
                        <Button 
                          onClick={() => {
                            if (roomImageUrl || useAIRoom) {
                              setActiveTab('customize');
                            } else {
                              toast({
                                title: 'Room Required',
                                description: 'Please upload a room photo or generate an AI room first',
                                variant: 'destructive',
                              });
                            }
                          }}
                          className="bg-purple-600 hover:bg-purple-700"
                          disabled={!roomImageUrl && !useAIRoom}
                        >
                          <Eye className="mr-2 h-4 w-4" />
                          View in 3D Room
                        </Button>
                        <p className="text-xs text-gray-500 mt-2">
                          {roomImageUrl || useAIRoom 
                            ? '✅ Room ready - Click to preview furniture'
                            : '⚠️ Upload a room photo above to continue'}
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* 3D Preview Tab - Always mounted to preserve WebGL context */}
          <TabsContent 
            value="customize" 
            className="flex-1 p-4 flex gap-4 min-h-0 overflow-hidden"
            forceMount
            style={{ display: activeTab === 'customize' ? 'flex' : 'none' }}
          >
            {/* 3D Canvas */}
            <div className="flex-1 border-2 border-gray-200 rounded-xl overflow-hidden bg-gradient-to-b from-gray-900 to-gray-800 relative min-h-0">
              {/* Room preview image overlay - faded */}
              {roomImageUrl && (
                <div 
                  className="absolute inset-0 opacity-10 pointer-events-none bg-cover bg-center z-0"
                  style={{ backgroundImage: `url(${roomImageUrl})` }}
                />
              )}
              
              <Canvas 
                shadows="soft"
                camera={{ position: [5, 4, 8], fov: 50 }}
                gl={{
                  antialias: true,
                  toneMapping: THREE.ACESFilmicToneMapping,
                  toneMappingExposure: 1.2,
                  outputColorSpace: THREE.SRGBColorSpace,
                  powerPreference: 'high-performance',
                  alpha: true
                }}
                onCreated={({ gl }) => {
                  gl.shadowMap.enabled = true;
                  gl.shadowMap.type = THREE.PCFSoftShadowMap;
                }}
                dpr={[1, 2]}
                performance={{ min: 0.5 }}
              >
                <Suspense fallback={null}>
                  <Scene 
                    dimensions={roomDimensions}
                    colors={roomColors}
                    furniture={furniture}
                    selectedId={selectedFurnitureId}
                    onFurnitureClick={setSelectedFurnitureId}
                    lighting={lighting}
                    roomImageUrl={roomImageUrl}
                    listingFurnitureUrl={listingFurnitureUrl}
                    showGrid={showGrid}
                  />
                </Suspense>
              </Canvas>

              {/* Room Analysis Overlay */}
              {roomAnalysis && (
                <div className="absolute top-4 left-4 bg-black/60 backdrop-blur-sm rounded-lg p-3 text-white text-xs space-y-1 z-10">
                  <div className="font-semibold text-purple-300">Room Analysis</div>
                  <div>🏠 {roomAnalysis.roomType}</div>
                  <div>✨ {roomAnalysis.ambiance} ambiance</div>
                  <div>💡 {roomAnalysis.lightingCondition} lighting</div>
                  <div>🌡️ Brightness: {roomAnalysis.brightness}%</div>
                  <div className="flex gap-1 items-center">
                    <span>🎨</span>
                    {roomAnalysis.dominantColors.slice(0, 4).map((color, i) => (
                      <div 
                        key={i} 
                        className="w-4 h-4 rounded-full border border-white/30" 
                        style={{ backgroundColor: color }}
                        title={roomAnalysis.colorPalette[i]?.name}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Controls overlay */}
              <div className="absolute bottom-4 left-4 flex gap-2 z-10">
                <Button 
                  size="sm" 
                  variant={showGrid ? "secondary" : "outline"}
                  onClick={() => setShowGrid(!showGrid)}
                  className="bg-black/50 hover:bg-black/70 text-white border-white/20"
                >
                  <Ruler className="h-4 w-4 mr-1" />
                  Grid
                </Button>
              </div>
            </div>

            {/* Controls Panel */}
            <div className="w-80 flex-shrink-0 overflow-y-auto space-y-4">
              {/* Listing Furniture Preview Card */}
              <Card className="border-2 border-purple-200 bg-gradient-to-br from-purple-50 to-blue-50">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Eye className="h-4 w-4 text-purple-600" />
                    Product 3D Preview
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {/* Furniture Image from Listing */}
                  {furnitureImageUrl && (
                    <div className="relative">
                      <div className="w-full h-32 rounded-lg overflow-hidden bg-white shadow-inner">
                        <img 
                          src={furnitureImageUrl} 
                          alt={listingTitle || 'Product'} 
                          className="w-full h-full object-contain"
                        />
                      </div>
                      <div className="absolute top-2 right-2">
                        <Badge className="bg-purple-600 text-white">
                          {detectedFurnitureType.charAt(0).toUpperCase() + detectedFurnitureType.slice(1)}
                        </Badge>
                      </div>
                    </div>
                  )}

                  {/* Product Info */}
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-gray-800 line-clamp-2">{listingTitle}</p>
                    {price && (
                      <div className="flex items-center gap-1">
                        <span className="text-lg font-bold text-green-600">EGP {price.toLocaleString()}</span>
                      </div>
                    )}
                  </div>

                  {/* Extracted Color */}
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-8 h-8 rounded-md border-2 border-gray-300 shadow-inner"
                      style={{ backgroundColor: extractedFurnitureColor }}
                    />
                    <div className="text-xs text-gray-600">
                      <p className="font-medium">Detected Color</p>
                      <p className="uppercase">{extractedFurnitureColor}</p>
                    </div>
                  </div>

                  {/* Status */}
                  <div className="p-2 bg-white/50 rounded-lg">
                    {!roomAnalysis ? (
                      <div className="flex items-center gap-2 text-amber-600">
                        <ImageIcon className="h-4 w-4" />
                        <span className="text-xs">Upload a room image to preview this furniture in 3D</span>
                      </div>
                    ) : furniture.length === 0 ? (
                      <div className="flex items-center gap-2 text-blue-600">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-xs">Adding furniture to room...</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-green-600">
                        <Check className="h-4 w-4" />
                        <span className="text-xs">Furniture placed in room! Drag to reposition.</span>
                      </div>
                    )}
                  </div>

                  {/* Re-add button if furniture was removed */}
                  {roomAnalysis && furniture.length === 0 && (
                    <Button onClick={addListingFurniture} className="w-full bg-gradient-to-r from-purple-600 to-blue-600">
                      <Plus className="h-4 w-4 mr-2" />
                      Add to Room
                    </Button>
                  )}
                </CardContent>
              </Card>

              {/* Selected Furniture Card - Customize the listing furniture */}
              {selectedFurniture && (
                <Card className="border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <Settings className="h-4 w-4 text-blue-600" />
                        Customize 3D Model
                      </span>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={() => setSelectedFurnitureId(null)}
                        className="h-6 w-6 p-0"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <Label className="text-xs">Size</Label>
                        <span className="text-xs text-gray-500">{(selectedFurniture.scale[0] * 100).toFixed(0)}%</span>
                      </div>
                      <Slider 
                        value={[selectedFurniture.scale[0]]}
                        onValueChange={([v]) => updateSelectedFurniture({ scale: [v, v, v] })}
                        min={0.5}
                        max={2}
                        step={0.05}
                      />
                    </div>

                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <Label className="text-xs">Rotation</Label>
                        <span className="text-xs text-gray-500">{(selectedFurniture.rotation[1] * (180 / Math.PI)).toFixed(0)}°</span>
                      </div>
                      <Slider 
                        value={[selectedFurniture.rotation[1] * (180 / Math.PI)]}
                        onValueChange={([v]) => updateSelectedFurniture({ rotation: [0, v * (Math.PI / 180), 0] })}
                        min={0}
                        max={360}
                      />
                    </div>

                    {/* Change color of selected item */}
                    <div className="space-y-2">
                      <Label className="text-xs font-medium">Furniture Color</Label>
                      
                      {/* Color picker */}
                      <div className="flex gap-2 items-center">
                        <Input 
                          type="color"
                          value={selectedFurniture.color || '#808080'}
                          onChange={(e) => updateSelectedFurniture({ color: e.target.value })}
                          className="w-14 h-8 p-1 cursor-pointer"
                        />
                        <span className="text-xs text-gray-500">Custom</span>
                      </div>
                      
                      {/* Room-matching colors */}
                      {roomAnalysis && (
                        <div className="space-y-1">
                          <p className="text-xs text-gray-500">Room Colors</p>
                          <div className="flex gap-1 flex-wrap">
                            {roomAnalysis.dominantColors.slice(0, 5).map((color, i) => (
                              <button
                                key={`room-${i}`}
                                className={`w-7 h-7 rounded border-2 transition-all ${selectedFurniture.color === color ? 'border-blue-500 scale-110' : 'border-gray-200 hover:border-blue-400 hover:scale-105'}`}
                                style={{ backgroundColor: color }}
                                onClick={() => updateSelectedFurniture({ color })}
                                title={getColorName(color)}
                              />
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Harmonious color suggestions */}
                      {selectedFurniture.color && (
                        <div className="space-y-1">
                          <p className="text-xs text-gray-500">Harmonious Options</p>
                          <div className="flex gap-1 flex-wrap">
                            {generateHarmoniousColors(selectedFurniture.color).map((color, i) => (
                              <button
                                key={`harmony-${i}`}
                                className={`w-7 h-7 rounded border-2 transition-all ${selectedFurniture.color === color ? 'border-blue-500 scale-110' : 'border-gray-200 hover:border-blue-400 hover:scale-105'}`}
                                style={{ backgroundColor: color }}
                                onClick={() => updateSelectedFurniture({ color })}
                                title={getColorName(color)}
                              />
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Quick color presets */}
                      <div className="space-y-1">
                        <p className="text-xs text-gray-500">Popular Furniture Colors</p>
                        <div className="flex gap-1 flex-wrap">
                          {['#2C1810', '#5C4033', '#8B7355', '#D2B48C', '#F5F5DC', '#1C1C1C', '#FFFFFF', '#87CEEB'].map((color, i) => (
                            <button
                              key={`preset-${i}`}
                              className={`w-7 h-7 rounded border-2 transition-all ${selectedFurniture.color === color ? 'border-blue-500 scale-110' : 'border-gray-200 hover:border-blue-400 hover:scale-105'}`}
                              style={{ backgroundColor: color }}
                              onClick={() => updateSelectedFurniture({ color })}
                              title={['Dark Walnut', 'Chocolate', 'Mocha', 'Tan', 'Beige', 'Charcoal', 'White', 'Sky Blue'][i]}
                            />
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="pt-2 border-t">
                      <p className="text-xs text-gray-500 mb-2">Position: Drag the furniture in the 3D view</p>
                      <Button variant="outline" onClick={removeFurniture} className="w-full text-red-600 hover:text-red-700 hover:bg-red-50">
                        <Trash2 className="h-4 w-4 mr-2" />
                        Remove from Room
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Lighting Card */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Lightbulb className="h-4 w-4" />
                    Room Lighting
                  </CardTitle>
                  <p className="text-xs text-gray-500">Adjust lighting to match your room's conditions</p>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Ambient (base room light) */}
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-gradient-to-r from-gray-300 to-gray-100" />
                        <Label className="text-xs">Ambient Light</Label>
                      </div>
                      <span className="text-xs text-gray-500 font-medium">{Math.round(lighting.ambient * 100)}%</span>
                    </div>
                    <Slider 
                      value={[lighting.ambient * 100]}
                      onValueChange={([v]) => setLighting({...lighting, ambient: v / 100})}
                      min={0}
                      max={100}
                      className="cursor-pointer"
                    />
                    <p className="text-xs text-gray-400 mt-1">Base room illumination</p>
                  </div>
                  
                  {/* Sunlight (main directional light) */}
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-gradient-to-r from-yellow-400 to-orange-300" />
                        <Label className="text-xs">Sunlight</Label>
                      </div>
                      <span className="text-xs text-gray-500 font-medium">{Math.round(lighting.directional * 100)}%</span>
                    </div>
                    <Slider 
                      value={[lighting.directional * 100]}
                      onValueChange={([v]) => setLighting({...lighting, directional: v / 100})}
                      min={0}
                      max={200}
                      className="cursor-pointer"
                    />
                    <p className="text-xs text-gray-400 mt-1">Natural window light intensity</p>
                  </div>
                  
                  {/* Point Lights (indoor lamps) */}
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-gradient-to-r from-amber-300 to-yellow-200" />
                        <Label className="text-xs">Point Lights</Label>
                      </div>
                      <span className="text-xs text-gray-500 font-medium">{Math.round(lighting.point * 100)}%</span>
                    </div>
                    <Slider 
                      value={[lighting.point * 100]}
                      onValueChange={([v]) => setLighting({...lighting, point: v / 100})}
                      min={0}
                      max={150}
                      className="cursor-pointer"
                    />
                    <p className="text-xs text-gray-400 mt-1">Indoor lamps & ceiling lights</p>
                  </div>
                  
                  {/* Hemisphere (sky/ground bounce) */}
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-gradient-to-b from-sky-300 to-amber-200" />
                        <Label className="text-xs">Sky/Ground Bounce</Label>
                      </div>
                      <span className="text-xs text-gray-500 font-medium">{Math.round(lighting.hemisphere * 100)}%</span>
                    </div>
                    <Slider 
                      value={[lighting.hemisphere * 100]}
                      onValueChange={([v]) => setLighting({...lighting, hemisphere: v / 100})}
                      min={0}
                      max={100}
                      className="cursor-pointer"
                    />
                    <p className="text-xs text-gray-400 mt-1">Realistic light bounce from sky & floor</p>
                  </div>
                  
                  {/* Quick Presets */}
                  <div className="pt-2 border-t">
                    <Label className="text-xs text-gray-600 mb-2 block">Quick Presets</Label>
                    <div className="flex gap-2 flex-wrap">
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="text-xs h-7"
                        onClick={() => setLighting({ ambient: 0.8, directional: 1.5, point: 0.3, hemisphere: 0.5 })}
                      >
                        ☀️ Daylight
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="text-xs h-7"
                        onClick={() => setLighting({ ambient: 0.3, directional: 0.4, point: 0.8, hemisphere: 0.3 })}
                      >
                        🌙 Evening
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="text-xs h-7"
                        onClick={() => setLighting({ ambient: 0.5, directional: 0.8, point: 0.5, hemisphere: 0.4 })}
                      >
                        🏠 Cozy
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="text-xs h-7"
                        onClick={() => setLighting({ ambient: 0.9, directional: 1.2, point: 0.6, hemisphere: 0.6 })}
                      >
                        💡 Bright
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* AI Suggestions Tab */}
          <TabsContent 
            value="suggestions" 
            className="flex-1 p-4 overflow-y-auto min-h-0"
            onFocus={() => {
              if (roomAnalysis && aiSuggestions.length === 0) {
                generateAISuggestions();
              }
            }}
          >
            <div className="grid gap-6">
              {/* Generate Suggestions Button if empty */}
              {aiSuggestions.length === 0 && roomAnalysis && (
                <Card className="border-2 border-dashed border-purple-300">
                  <CardContent className="py-8 text-center">
                    <Sparkles className="h-12 w-12 mx-auto mb-4 text-purple-400" />
                    <p className="text-gray-600 mb-4">Click to generate AI suggestions for your room</p>
                    <Button onClick={() => generateAISuggestions()} className="bg-purple-600 hover:bg-purple-700">
                      <Sparkles className="mr-2 h-4 w-4" />
                      Generate AI Suggestions
                    </Button>
                  </CardContent>
                </Card>
              )}

              {/* Value Assessment Card */}
              {price && roomAnalysis && (
                <Card className="border-2 border-green-200 bg-gradient-to-r from-green-50 to-emerald-50">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <DollarSign className="h-5 w-5 text-green-600" />
                      Price-Value Analysis
                    </CardTitle>
                    <p className="text-sm text-gray-600">AI assessment of this furniture's value for your space</p>
                  </CardHeader>
                  <CardContent>
                    {(() => {
                      const valueScore = calculateValueScore(roomAnalysis, price);
                      const valueDesc = getValueDescription(valueScore, price, roomAnalysis);
                      return (
                        <div className="space-y-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-3xl font-bold text-green-700">PKR {price.toLocaleString()}</p>
                              <p className="text-sm text-gray-500">{listingTitle}</p>
                            </div>
                            <div className="text-right">
                              <div className="flex items-center gap-2">
                                <span className="text-2xl font-bold text-green-600">{valueScore}</span>
                                <span className="text-gray-500">/100</span>
                              </div>
                              <p className="text-sm font-medium text-green-600">Value Score</p>
                            </div>
                          </div>
                          
                          <div className="w-full bg-gray-200 rounded-full h-3">
                            <div 
                              className={`h-3 rounded-full transition-all ${
                                valueScore >= 80 ? 'bg-green-500' : 
                                valueScore >= 60 ? 'bg-yellow-500' : 
                                valueScore >= 40 ? 'bg-orange-500' : 'bg-red-500'
                              }`}
                              style={{ width: `${valueScore}%` }}
                            />
                          </div>
                          
                          <div className="bg-white rounded-lg p-4 border">
                            <p className="text-gray-700">{valueDesc}</p>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div className="bg-white rounded-lg p-3 border">
                              <p className="font-medium text-gray-700">Room Compatibility</p>
                              <p className="text-green-600 font-semibold">
                                {roomAnalysis.style === 'modern' ? 'Perfect for Modern Spaces' :
                                 roomAnalysis.style === 'traditional' ? 'Classic Elegance' :
                                 roomAnalysis.style === 'minimalist' ? 'Clean & Simple' : 'Versatile Match'}
                              </p>
                            </div>
                            <div className="bg-white rounded-lg p-3 border">
                              <p className="font-medium text-gray-700">Color Harmony</p>
                              <p className="text-purple-600 font-semibold">
                                {roomAnalysis.ambiance.charAt(0).toUpperCase() + roomAnalysis.ambiance.slice(1)} Ambiance
                              </p>
                            </div>
                          </div>
                        </div>
                      );
                    })()}
                  </CardContent>
                </Card>
              )}

              {/* AI Suggestions Cards */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-purple-600" />
                    AI-Powered Suggestions
                  </CardTitle>
                  <p className="text-sm text-gray-600">Smart recommendations based on room analysis</p>
                </CardHeader>
                <CardContent>
                  {aiSuggestions.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <Sparkles className="h-12 w-12 mx-auto mb-3 opacity-50" />
                      <p>Upload a room image and add furniture to get AI suggestions</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {aiSuggestions.map((suggestion) => (
                        <div 
                          key={suggestion.id}
                          className={`p-4 rounded-lg border-2 transition-all hover:shadow-md ${
                            suggestion.type === 'color' ? 'border-purple-200 bg-purple-50' :
                            suggestion.type === 'placement' ? 'border-blue-200 bg-blue-50' :
                            suggestion.type === 'style' ? 'border-amber-200 bg-amber-50' :
                            'border-green-200 bg-green-50'
                          }`}
                        >
                          <div className="flex items-start gap-3">
                            <div className={`p-2 rounded-full ${
                              suggestion.type === 'color' ? 'bg-purple-200' :
                              suggestion.type === 'placement' ? 'bg-blue-200' :
                              suggestion.type === 'style' ? 'bg-amber-200' :
                              'bg-green-200'
                            }`}>
                              {suggestion.icon === 'palette' && <Palette className="h-5 w-5 text-purple-700" />}
                              {suggestion.icon === 'move' && <Move className="h-5 w-5 text-blue-700" />}
                              {suggestion.icon === 'sparkles' && <Sparkles className="h-5 w-5 text-amber-700" />}
                              {suggestion.icon === 'thumbsup' && <ThumbsUp className="h-5 w-5 text-green-700" />}
                              {suggestion.icon === 'star' && <Star className="h-5 w-5 text-yellow-700" />}
                              {suggestion.icon === 'zap' && <Zap className="h-5 w-5 text-orange-700" />}
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center justify-between">
                                <h4 className="font-semibold text-gray-800">{suggestion.title}</h4>
                                <Badge variant="secondary" className="text-xs">
                                  {Math.round(suggestion.confidence * 100)}% confidence
                                </Badge>
                              </div>
                              <p className="text-sm text-gray-600 mt-1">{suggestion.description}</p>
                              {suggestion.action && (
                                <Button 
                                  size="sm" 
                                  variant="outline" 
                                  className="mt-2"
                                  onClick={suggestion.action}
                                >
                                  Apply Suggestion
                                </Button>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Color Matching Guide */}
              {roomAnalysis && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Palette className="h-5 w-5 text-indigo-600" />
                      Color Matching Guide
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <p className="text-sm font-medium text-gray-700 mb-2">Extracted Room Colors</p>
                        <div className="flex gap-2">
                          {roomAnalysis.extractedColors.slice(0, 5).map((color, i) => (
                            <div key={i} className="text-center">
                              <div 
                                className="w-12 h-12 rounded-lg border-2 border-white shadow-md"
                                style={{ backgroundColor: color }}
                              />
                              <span className="text-xs text-gray-500 mt-1 block">{getColorName(color)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      <div>
                        <p className="text-sm font-medium text-gray-700 mb-2">Complementary Suggestions</p>
                        <div className="flex gap-2">
                          {roomAnalysis.suggestedColors.slice(0, 4).map((color, i) => (
                            <div key={i} className="text-center">
                              <div 
                                className="w-12 h-12 rounded-lg border-2 border-white shadow-md cursor-pointer hover:scale-110 transition-transform"
                                style={{ backgroundColor: color }}
                                onClick={() => {
                                  if (selectedFurniture) {
                                    updateSelectedFurniture({ color });
                                    setFurnitureColor(color);
                                  }
                                }}
                              />
                              <span className="text-xs text-gray-500 mt-1 block">{getColorName(color)}</span>
                            </div>
                          ))}
                        </div>
                        <p className="text-xs text-gray-400 mt-2">Click a color to apply to selected furniture</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          {/* Gallery Tab */}
          <TabsContent value="gallery" className="flex-1 p-4 overflow-y-auto min-h-0">
            <div className="space-y-6">
              {/* Save Current Configuration */}
              {roomImage && furniture.length > 0 && (
                <Card className="border-2 border-dashed border-purple-300 bg-purple-50/50">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Save className="h-5 w-5 text-purple-600" />
                      Save Current Configuration
                    </CardTitle>
                    <p className="text-sm text-gray-600">Save your 3D room setup to access it later</p>
                  </CardHeader>
                  <CardContent>
                    <div className="flex gap-3">
                      <Input
                        placeholder="Give your configuration a name..."
                        value={configName}
                        onChange={(e) => setConfigName(e.target.value)}
                        className="flex-1"
                      />
                      <Button 
                        onClick={saveRoomConfig}
                        disabled={savingConfig || !configName.trim()}
                        className="gap-2 bg-purple-600 hover:bg-purple-700"
                      >
                        {savingConfig ? (
                          <>
                            <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                            Saving...
                          </>
                        ) : (
                          <>
                            <Save className="h-4 w-4" />
                            Save to Gallery
                          </>
                        )}
                      </Button>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      This will save: room dimensions, colors, {furniture.length} furniture items, and lighting settings
                    </p>
                  </CardContent>
                </Card>
              )}

              {/* Saved Configurations */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FolderOpen className="h-5 w-5 text-blue-600" />
                    My Saved Configurations
                    {savedConfigs.length > 0 && (
                      <Badge variant="secondary">{savedConfigs.length} saved</Badge>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {loadingGallery ? (
                    <div className="flex items-center justify-center py-12">
                      <div className="animate-spin h-8 w-8 border-4 border-purple-600 border-t-transparent rounded-full" />
                    </div>
                  ) : savedConfigs.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                      <FolderOpen className="h-16 w-16 mx-auto mb-4 opacity-30" />
                      <p className="text-lg font-medium">No saved configurations yet</p>
                      <p className="text-sm">Save your first 3D room setup to see it here</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {savedConfigs.map((config) => (
                        <div 
                          key={config.id}
                          className="border rounded-lg overflow-hidden hover:shadow-lg transition-all group"
                        >
                          {/* Thumbnail/Preview */}
                          <div className="h-32 bg-gradient-to-br from-purple-100 to-blue-100 relative">
                            {config.thumbnail ? (
                              <img 
                                src={config.thumbnail} 
                                alt={config.name}
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center">
                                <Box className="h-12 w-12 text-purple-300" />
                              </div>
                            )}
                            <div className="absolute top-2 right-2">
                              <Badge className="bg-black/60 text-white text-xs">
                                {config.furniture.length} items
                              </Badge>
                            </div>
                          </div>
                          
                          {/* Info */}
                          <div className="p-3">
                            <h4 className="font-semibold text-gray-800 truncate">{config.name}</h4>
                            <p className="text-xs text-gray-500 truncate">{config.listingTitle}</p>
                            <div className="flex items-center justify-between mt-2">
                              <span className="text-xs text-gray-400">
                                {new Date(config.createdAt).toLocaleDateString()}
                              </span>
                              {config.price && (
                                <span className="text-xs font-medium text-green-600">
                                  PKR {config.price.toLocaleString()}
                                </span>
                              )}
                            </div>
                            
                            {/* Actions */}
                            <div className="flex gap-2 mt-3">
                              <Button 
                                size="sm" 
                                variant="outline"
                                className="flex-1 text-xs"
                                onClick={() => loadSavedConfig(config)}
                              >
                                <Eye className="h-3 w-3 mr-1" />
                                Load
                              </Button>
                              <Button 
                                size="sm" 
                                variant="outline"
                                className="text-red-600 hover:bg-red-50"
                                onClick={() => {
                                  if (confirm('Delete this configuration?')) {
                                    deleteSavedConfig(config.id);
                                  }
                                }}
                              >
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Room Analysis Summary */}
              {roomAnalysis && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Info className="h-5 w-5 text-gray-600" />
                      Current Room Analysis
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-2xl font-bold text-gray-800">{roomAnalysis.estimatedSize}</p>
                        <p className="text-xs text-gray-500">Room Size</p>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-2xl font-bold text-gray-800 capitalize">{roomAnalysis.style}</p>
                        <p className="text-xs text-gray-500">Style</p>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-2xl font-bold text-gray-800 capitalize">{roomAnalysis.ambiance}</p>
                        <p className="text-xs text-gray-500">Ambiance</p>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-2xl font-bold text-gray-800">{roomAnalysis.brightness}%</p>
                        <p className="text-xs text-gray-500">Brightness</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="flex-1 p-4 overflow-y-auto min-h-0">
            <div className="grid gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Room Colors - Realistic Control</CardTitle>
                  <p className="text-sm text-gray-500">Adjust RGB values for precise color matching</p>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Floor Color */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label className="font-semibold">Floor Color</Label>
                      <div 
                        className="w-16 h-8 rounded border-2 border-gray-300" 
                        style={{ backgroundColor: roomColors.floor }}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-3">
                        <Label className="w-12 text-xs">Red</Label>
                        <Slider 
                          value={[parseInt(roomColors.floor.substring(1, 3), 16)]}
                          onValueChange={(val) => {
                            const r = val[0].toString(16).padStart(2, '0');
                            const g = roomColors.floor.substring(3, 5);
                            const b = roomColors.floor.substring(5, 7);
                            setRoomColors({...roomColors, floor: `#${r}${g}${b}`});
                          }}
                          min={0}
                          max={255}
                          step={1}
                          className="flex-1"
                        />
                        <span className="w-8 text-xs text-gray-600">{parseInt(roomColors.floor.substring(1, 3), 16)}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <Label className="w-12 text-xs">Green</Label>
                        <Slider 
                          value={[parseInt(roomColors.floor.substring(3, 5), 16)]}
                          onValueChange={(val) => {
                            const r = roomColors.floor.substring(1, 3);
                            const g = val[0].toString(16).padStart(2, '0');
                            const b = roomColors.floor.substring(5, 7);
                            setRoomColors({...roomColors, floor: `#${r}${g}${b}`});
                          }}
                          min={0}
                          max={255}
                          step={1}
                          className="flex-1"
                        />
                        <span className="w-8 text-xs text-gray-600">{parseInt(roomColors.floor.substring(3, 5), 16)}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <Label className="w-12 text-xs">Blue</Label>
                        <Slider 
                          value={[parseInt(roomColors.floor.substring(5, 7), 16)]}
                          onValueChange={(val) => {
                            const r = roomColors.floor.substring(1, 3);
                            const g = roomColors.floor.substring(3, 5);
                            const b = val[0].toString(16).padStart(2, '0');
                            setRoomColors({...roomColors, floor: `#${r}${g}${b}`});
                          }}
                          min={0}
                          max={255}
                          step={1}
                          className="flex-1"
                        />
                        <span className="w-8 text-xs text-gray-600">{parseInt(roomColors.floor.substring(5, 7), 16)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Walls Color */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label className="font-semibold">Walls Color</Label>
                      <div 
                        className="w-16 h-8 rounded border-2 border-gray-300" 
                        style={{ backgroundColor: roomColors.walls }}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-3">
                        <Label className="w-12 text-xs">Red</Label>
                        <Slider 
                          value={[parseInt(roomColors.walls.substring(1, 3), 16)]}
                          onValueChange={(val) => {
                            const r = val[0].toString(16).padStart(2, '0');
                            const g = roomColors.walls.substring(3, 5);
                            const b = roomColors.walls.substring(5, 7);
                            setRoomColors({...roomColors, walls: `#${r}${g}${b}`});
                          }}
                          min={0}
                          max={255}
                          step={1}
                          className="flex-1"
                        />
                        <span className="w-8 text-xs text-gray-600">{parseInt(roomColors.walls.substring(1, 3), 16)}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <Label className="w-12 text-xs">Green</Label>
                        <Slider 
                          value={[parseInt(roomColors.walls.substring(3, 5), 16)]}
                          onValueChange={(val) => {
                            const r = roomColors.walls.substring(1, 3);
                            const g = val[0].toString(16).padStart(2, '0');
                            const b = roomColors.walls.substring(5, 7);
                            setRoomColors({...roomColors, walls: `#${r}${g}${b}`});
                          }}
                          min={0}
                          max={255}
                          step={1}
                          className="flex-1"
                        />
                        <span className="w-8 text-xs text-gray-600">{parseInt(roomColors.walls.substring(3, 5), 16)}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <Label className="w-12 text-xs">Blue</Label>
                        <Slider 
                          value={[parseInt(roomColors.walls.substring(5, 7), 16)]}
                          onValueChange={(val) => {
                            const r = roomColors.walls.substring(1, 3);
                            const g = roomColors.walls.substring(3, 5);
                            const b = val[0].toString(16).padStart(2, '0');
                            setRoomColors({...roomColors, walls: `#${r}${g}${b}`});
                          }}
                          min={0}
                          max={255}
                          step={1}
                          className="flex-1"
                        />
                        <span className="w-8 text-xs text-gray-600">{parseInt(roomColors.walls.substring(5, 7), 16)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Ceiling Color */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label className="font-semibold">Ceiling Color</Label>
                      <div 
                        className="w-16 h-8 rounded border-2 border-gray-300" 
                        style={{ backgroundColor: roomColors.ceiling }}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-3">
                        <Label className="w-12 text-xs">Red</Label>
                        <Slider 
                          value={[parseInt(roomColors.ceiling.substring(1, 3), 16)]}
                          onValueChange={(val) => {
                            const r = val[0].toString(16).padStart(2, '0');
                            const g = roomColors.ceiling.substring(3, 5);
                            const b = roomColors.ceiling.substring(5, 7);
                            setRoomColors({...roomColors, ceiling: `#${r}${g}${b}`});
                          }}
                          min={0}
                          max={255}
                          step={1}
                          className="flex-1"
                        />
                        <span className="w-8 text-xs text-gray-600">{parseInt(roomColors.ceiling.substring(1, 3), 16)}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <Label className="w-12 text-xs">Green</Label>
                        <Slider 
                          value={[parseInt(roomColors.ceiling.substring(3, 5), 16)]}
                          onValueChange={(val) => {
                            const r = roomColors.ceiling.substring(1, 3);
                            const g = val[0].toString(16).padStart(2, '0');
                            const b = roomColors.ceiling.substring(5, 7);
                            setRoomColors({...roomColors, ceiling: `#${r}${g}${b}`});
                          }}
                          min={0}
                          max={255}
                          step={1}
                          className="flex-1"
                        />
                        <span className="w-8 text-xs text-gray-600">{parseInt(roomColors.ceiling.substring(3, 5), 16)}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <Label className="w-12 text-xs">Blue</Label>
                        <Slider 
                          value={[parseInt(roomColors.ceiling.substring(5, 7), 16)]}
                          onValueChange={(val) => {
                            const r = roomColors.ceiling.substring(1, 3);
                            const g = roomColors.ceiling.substring(3, 5);
                            const b = val[0].toString(16).padStart(2, '0');
                            setRoomColors({...roomColors, ceiling: `#${r}${g}${b}`});
                          }}
                          min={0}
                          max={255}
                          step={1}
                          className="flex-1"
                        />
                        <span className="w-8 text-xs text-gray-600">{parseInt(roomColors.ceiling.substring(5, 7), 16)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Quick Presets */}
                  <div className="space-y-2 pt-4 border-t">
                    <Label className="font-semibold">Quick Presets</Label>
                    <div className="grid grid-cols-2 gap-2">
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => setRoomColors({
                          floor: '#8B7355',
                          walls: '#F5F5DC',
                          ceiling: '#FFFFFF',
                          accent: '#4A90E2'
                        })}
                      >
                        Warm Wood
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => setRoomColors({
                          floor: '#C0C0C0',
                          walls: '#FFFFFF',
                          ceiling: '#F8F8F8',
                          accent: '#000000'
                        })}
                      >
                        Modern White
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => setRoomColors({
                          floor: '#654321',
                          walls: '#8B7355',
                          ceiling: '#F5DEB3',
                          accent: '#DAA520'
                        })}
                      >
                        Classic Oak
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => setRoomColors({
                          floor: '#2F4F4F',
                          walls: '#708090',
                          ceiling: '#D3D3D3',
                          accent: '#4682B4'
                        })}
                      >
                        Industrial
                      </Button>
                    </div>
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
