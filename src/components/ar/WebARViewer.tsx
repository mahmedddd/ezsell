/**
 * WebARViewer — Production AR viewer for furniture listings
 * ──────────────────────────────────────────────────────────
 * • Uses Google <model-viewer> for native AR:
 *     Android → WebXR / Scene Viewer (ARCore)
 *     iOS     → AR QuickLook (ARKit)
 * • Falls back to a 3-D orbit viewer when AR is not available
 * • Generates a real-scale procedural GLB when no model URL is stored
 * • Detects room objects with TF.js COCO-SSD (before AR launch)
 * • Fully mobile-responsive; designed as a bottom-sheet on phones
 */

import '@google/model-viewer';

import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/components/ui/use-toast';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';
import {
  Camera, Smartphone, Scan, ChevronRight, X, Loader2,
  Ruler, Move, RotateCw, ZoomIn, Info, CheckCircle2,
  AlertTriangle, Sparkles, Box, Eye, QrCode, ExternalLink,
  Vibrate, Zap, LayoutGrid, ArrowDownCircle, MousePointer2
} from 'lucide-react';

import { useARSupport } from '@/hooks/useARSupport';
import {
  generateFurnitureGLB,
  resolveFurnitureType,
  resolveSmartDimensions,
  extractColorProfile,
  extractColorProfileMulti,
  extractProductCanvas,
  FURNITURE_DEFAULTS,
  type FurnitureDimensions,
  type FurnitureType,
  type ColorProfile,
} from '@/components/ar/FurnitureGLBGenerator';
import { arAssetsService, API_BASE_URL } from '../../lib/api.ts';

// ─── TypeScript Declarations for <model-viewer> ───────────────────────────────
declare global {
  namespace JSX {
    interface IntrinsicElements {
      'model-viewer': any;
    }
  }
}

// Extend React's HTMLAttributes to allow the 'slot' attribute on all elements
declare module 'react' {
  interface HTMLAttributes<T> extends AriaAttributes, DOMAttributes<T> {
    slot?: string;
  }
}

// ─── Types ────────────────────────────────────────────────────────────────────

interface ARAssets {
  model_glb_url?: string | null;
  model_usdz_url?: string | null;
  dimensions_cm?: FurnitureDimensions | null;
  polygon_count?: number | null;
}

export interface WebARViewerProps {
  listingId: number;
  listingTitle: string;
  category: string;
  price?: number;
  /** listing.furniture_type DB field — most reliable type hint */
  furnitureType?: string | null;
  /**
   * listing.furniture_subtype — stores size/variant chosen at listing time.
   * e.g. "3_door", "4_door", "sliding", "queen", "king".
   * Used to correctly set door count / bed size without parsing free-text.
   */
  furnitureSubtype?: string | null;
  /** listing.material DB field — e.g. "wood", "metal", "leather", "fabric" */
  furnitureMaterial?: string | null;
  /** listing.description — used as fallback for type detection */
  listingDescription?: string | null;
  furnitureImageUrl?: string | null;
  /** All listing image URLs — used for multi-image colour analysis (more accurate than single image) */
  allImageUrls?: string[];
  arAssets?: ARAssets | null;
  /** override dimensions from listing detail page */
  dimensionsCm?: FurnitureDimensions | null;
}

type ARStep =
  | 'idle'
  | 'building_model'
  | 'model_ready'
  | 'scanning'          // user moving phone to detect floor
  | 'placed'            // furniture anchored
  | 'error';

type ScanPhase = 'tilting' | 'sweeping' | 'ready_to_place';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function cmLabel(dims: FurnitureDimensions) {
  return `${dims.w} × ${dims.l} × ${dims.h} cm`;
}

type AIStage = 'idle' | 'detecting' | 'generating' | 'polling' | 'downloading' | 'success' | 'error';

function mLabel(dims: FurnitureDimensions) {
  return `${(dims.w / 100).toFixed(2)}m × ${(dims.l / 100).toFixed(2)}m × ${(dims.h / 100).toFixed(2)}m`;
}

function detectARModesAttr(supportedModes: string[]): string {
  return supportedModes.join(' ');
}

function getFullUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  if (url.startsWith('http') || url.startsWith('blob:') || url.startsWith('data:')) return url;
  
  // For mobile devices, we MUST prefix relative paths with the backend IP
  // otherwise the browser tries to hit the phone's localhost.
  const base = typeof window !== 'undefined' ? (window as any).BACKEND_URL || API_BASE_URL : API_BASE_URL;
  const cleanBase = base.endsWith('/') ? base.slice(0, -1) : base;
  const cleanUrl = url.startsWith('/') ? url : `/${url}`;
  
  return `${cleanBase}${cleanUrl}`;
}

// ─── Sub-components ───────────────────────────────────────────────────────────

/** Loading skeleton while GLB is being built */
function ModelBuildingIndicator({ progress }: { progress: number }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 gap-4">
      <div className="relative">
        <div className="w-20 h-20 rounded-full border-4 border-[#143109]/20 animate-pulse bg-[#143109]/5 flex items-center justify-center">
          <Box className="h-9 w-9 text-[#143109]" />
        </div>
        <Loader2 className="absolute -top-1 -right-1 h-6 w-6 text-[#143109] animate-spin" />
      </div>
      <div className="text-center">
        <p className="font-semibold text-gray-900">Building 3D Model…</p>
        <p className="text-sm text-gray-500 mt-1">Generating real-scale geometry</p>
      </div>
      <Progress value={progress} className="w-48 h-2" />
    </div>
  );
}

/** Gesture hint row shown at the bottom of the AR sheet */
function GestureHints() {
  const hints = [
    { icon: <Move className="h-4 w-4" />, label: '1-finger drag', action: 'Move' },
    { icon: <RotateCw className="h-4 w-4" />, label: '2-finger twist', action: 'Rotate' },
    { icon: <ZoomIn className="h-4 w-4" />, label: 'Pinch to zoom', action: 'Scale locked 1:1' },
  ];
  return (
    <div className="grid grid-cols-3 gap-2 mt-3">
      {hints.map((h) => (
        <div key={h.action} className="flex flex-col items-center gap-1 p-2 bg-gray-50 rounded-xl">
          <div className="text-[#143109]">{h.icon}</div>
          <p className="text-[10px] font-medium text-gray-700 text-center leading-tight">{h.action}</p>
          <p className="text-[9px] text-gray-400 text-center leading-tight">{h.label}</p>
        </div>
      ))}
    </div>
  );
}

/** Compatibility badge shown near the AR button */
function CompatibilityBadge({ caps }: { caps: ReturnType<typeof useARSupport> }) {
  if (!caps.isChecked) return null;

  if (caps.isSupported && caps.mode === 'webxr') {
    return (
      <Badge className="bg-green-100 text-green-800 border-green-200 text-xs">
        <CheckCircle2 className="h-3 w-3 mr-1" />
        ARCore Ready
      </Badge>
    );
  }
  if (caps.isSupported && caps.mode === 'quick-look') {
    return (
      <Badge className="bg-blue-100 text-blue-800 border-blue-200 text-xs">
        <CheckCircle2 className="h-3 w-3 mr-1" />
        AR QuickLook Ready
      </Badge>
    );
  }
  if (caps.isSupported && caps.mode === 'scene-viewer') {
    return (
      <Badge className="bg-indigo-100 text-indigo-800 border-indigo-200 text-xs">
        <CheckCircle2 className="h-3 w-3 mr-1" />
        Scene Viewer Ready
      </Badge>
    );
  }
  if (caps.isDesktop) {
    return (
      <Badge variant="outline" className="text-xs text-amber-700 border-amber-300 bg-amber-50">
        <QrCode className="h-3 w-3 mr-1" />
        Use phone for AR
      </Badge>
    );
  }
  return (
    <Badge variant="outline" className="text-xs text-red-700 border-red-300 bg-red-50">
      <AlertTriangle className="h-3 w-3 mr-1" />
      AR not supported
    </Badge>
  );
}

/** Dimension pill shown in the model viewer header */
function DimensionPill({ dims }: { dims: FurnitureDimensions }) {
  return (
    <div className="flex items-center gap-1.5 bg-white/90 backdrop-blur px-3 py-1.5 rounded-full shadow-sm border border-gray-100">
      <Ruler className="h-3.5 w-3.5 text-[#143109]" />
      <span className="text-xs font-semibold text-gray-800">{cmLabel(dims)}</span>
    </div>
  );
}

/** Desktop QR prompt — guides user to open on phone */
function DesktopQRHint({ url }: { url: string }) {
  return (
    <div className="flex flex-col items-center gap-3 p-6 bg-gradient-to-br from-amber-50 to-orange-50 rounded-2xl border border-amber-200">
      <QrCode className="h-10 w-10 text-amber-600" />
      <div className="text-center">
        <p className="font-semibold text-gray-900">Scan on your phone</p>
        <p className="text-sm text-gray-600 mt-1">
          AR requires a phone with ARCore or ARKit. Open this page on your
          mobile browser, then tap the button again.
        </p>
      </div>
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-2 text-sm text-amber-700 font-medium"
      >
        <ExternalLink className="h-4 w-4" />
        Open product page
      </a>
    </div>
  );
}

/** Animated Scanning Overlay inside the AR viewport */
function ScanningOverlay({ phase, hint }: { phase: ScanPhase; hint: string }) {
  return (
    <div className="absolute inset-0 z-20 flex flex-col items-center justify-center pointer-events-none px-6">
      <div className="relative mb-10">
        <div className="w-40 h-40 rounded-full border-2 border-white/10 animate-ping absolute inset-0" />
        <div className="w-40 h-40 rounded-full border-2 border-white/30 border-t-[#AAAE7F] animate-spin" />
        <div className="absolute inset-0 flex items-center justify-center">
          {phase === 'tilting' && <ArrowDownCircle className="h-12 w-12 text-white/80 animate-bounce" />}
          {phase === 'sweeping' && <Scan className="h-12 w-12 text-white/80 animate-pulse" />}
          {phase === 'ready_to_place' && <MousePointer2 className="h-12 w-12 text-[#AAAE7F] animate-bounce" />}
        </div>
      </div>

      <div className="bg-black/40 backdrop-blur-sm px-6 py-4 rounded-[24px] border border-white/5 text-center max-w-sm animate-in fade-in slide-in-from-bottom-4">
        <p className="text-white font-medium text-base mb-1.5">{hint}</p>
        <div className="flex justify-center gap-1.5 mt-2.5">
          <div className={`h-1 w-6 rounded-full transition-all duration-300 ${phase === 'tilting' ? 'bg-[#AAAE7F] w-10' : 'bg-white/20'}`} />
          <div className={`h-1 w-6 rounded-full transition-all duration-300 ${phase === 'sweeping' ? 'bg-[#AAAE7F] w-10' : 'bg-white/20'}`} />
          <div className={`h-1 w-6 rounded-full transition-all duration-300 ${phase === 'ready_to_place' ? 'bg-[#AAAE7F] w-10' : 'bg-white/20'}`} />
        </div>
      </div>
    </div>
  );
}

/** Pre-Launch Checklist to ensure user has enough room */
function PreLaunchChecklist({ dims }: { dims: FurnitureDimensions }) {
  const floorNeeded = `${dims.w}cm × ${dims.l}cm`;
  return (
    <div className="bg-[#143109]/5 border border-[#143109]/10 rounded-2xl p-4 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <LayoutGrid className="h-4 w-4 text-[#143109]" />
        <span className="text-sm font-bold text-gray-900">Room Readiness</span>
      </div>
      <ul className="space-y-2">
        <li className="flex items-center gap-2 text-xs text-gray-700">
          <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />
          Need <b>{floorNeeded}</b> clear floor space
        </li>
        <li className="flex items-center gap-2 text-xs text-gray-700">
          <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />
          Good lighting helps floor detection
        </li>
        <li className="flex items-center gap-2 text-xs text-gray-700">
          <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />
          Scan slowly at a downward angle
        </li>
      </ul>
    </div>
  );
}

/** Post-Placement Interaction Coach Overlay */
function PostPlacementCoach({ onDismiss }: { onDismiss: () => void }) {
  useEffect(() => {
    const timer = setTimeout(() => onDismiss(), 5000);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  return (
    <div className="absolute bottom-24 left-1/2 -translate-x-1/2 z-30 w-[90%] animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="bg-[#143109] text-white p-4 rounded-2xl shadow-2xl flex items-center gap-4 border border-white/10">
        <div className="bg-white/20 p-2 rounded-xl">
          <Zap className="h-5 w-5 text-[#AAAE7F]" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-bold leading-tight">Interaction Ready</p>
          <p className="text-[11px] text-white/70">Drag to move · Twist to rotate · Scale fixed 1:1</p>
        </div>
        <button onClick={() => onDismiss()} className="p-1 text-white/50 hover:text-white">
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

/** Room Scale Sanity Indicator */
function RoomScaleBadge({ dims }: { dims: FurnitureDimensions }) {
  const areaCm2 = dims.w * dims.l;
  const isLarge = areaCm2 > 200 * 200; // >4m2

  return (
    <div className={`p-4 rounded-2xl border flex items-start gap-3 ${isLarge ? 'bg-amber-50 border-amber-200' : 'bg-blue-50 border-blue-200'}`}>
      <div className={`p-2 rounded-xl ${isLarge ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'}`}>
        <Box className="h-5 w-5" />
      </div>
      <div>
        <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-1">Room Scale Analysis</p>
        <p className="text-sm font-bold text-gray-900 leading-tight">
          {isLarge ? 'Large Footprint' : 'Standard Footprint'}
        </p>
        <p className="text-[11px] text-gray-600 mt-1 leading-relaxed">
          {isLarge
            ? 'This item covers a significant area. Best for open living spaces.'
            : 'Fits comfortably in most rooms and corridors.'}
        </p>
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export function WebARViewer({
  listingId,
  listingTitle,
  category,
  price,
  furnitureType,
  furnitureSubtype,
  furnitureMaterial,
  listingDescription,
  furnitureImageUrl,
  allImageUrls,
  arAssets,
  dimensionsCm,
}: WebARViewerProps) {
  const { toast } = useToast();
  const caps = useARSupport();

  const [isSheetOpen, setIsSheetOpen] = useState(false);
  const [step, setStep] = useState<ARStep>('idle');
  const [buildProgress, setBuildProgress] = useState(0);
  const [proceduralUrl, setProceduralUrl] = useState<string | null>(null);
  
  // These stay in sync with arAssets via useEffect or direct derivation
  const [tripoUrl, setTripoUrl] = useState<string | null>(getFullUrl(arAssets?.model_glb_url));
  const [usdzUrl, setUsdzUrl] = useState<string | null>(getFullUrl(arAssets?.model_usdz_url));
  const [viewMode, setViewMode] = useState<'fast' | 'advanced'>(arAssets?.model_glb_url ? 'advanced' : 'fast');

  const [arStatus, setArStatus] = useState<string>('');
  const [detectedObjects, setDetectedObjects] = useState<string[]>([]);
  const [tfLoading, setTfLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'ar' | 'info'>('ar');
  const [scanPhase, setScanPhase] = useState<ScanPhase>('tilting');
  const [scanDuration, setScanDuration] = useState(0);
  const [showCoach, setShowCoach] = useState(false);

  // AI Generation State
  const [aiStage, setAiStage] = useState<AIStage>('idle');
  const [aiProgress, setAiProgress] = useState(0);
  const [aiTaskId, setAiTaskId] = useState<string | null>(null);
  const [selectedImgIdx, setSelectedImgIdx] = useState(0);

  const modelViewerRef = useRef<any>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  // Only render for furniture
  if (category?.toLowerCase() !== 'furniture') return null;

  // ── Resolve furniture metadata (Memoized to prevent drift) ───────────────────
  const fType: FurnitureType = useMemo(() => 
    resolveFurnitureType(furnitureType, listingTitle, listingDescription),
    [furnitureType, listingTitle, listingDescription]
  );

  const subtypeText = (furnitureSubtype ?? '').replace(/_/g, ' ');

  const dims: FurnitureDimensions = useMemo(() => {
    return dimensionsCm ?? arAssets?.dimensions_cm ?? resolveSmartDimensions(fType, listingTitle, `${listingDescription ?? ''} ${subtypeText}`);
  }, [dimensionsCm, arAssets?.dimensions_cm, fType, listingTitle, listingDescription, subtypeText]);

  // ── Build (or fetch) the GLB ───────────────────────────────────────────────
  const prepareModel = useCallback(async () => {
    if (proceduralUrl) return; // already built procedural model

    setStep('building_model');

    // Simulate progress ticks while async work runs
    let prog = 0;
    const interval = setInterval(() => {
      prog = Math.min(prog + 12, 88);
      setBuildProgress(prog);
    }, 180);

    try {
      // 2. Extract full colour profile → primary fabric + accent trim + metallic + glossiness
      //    AND load the product image canvas for tiling texture — both in parallel.
      let colorProfile: ColorProfile | null = null;
      let productCanvas: HTMLCanvasElement | undefined;
      const imgUrls = (allImageUrls && allImageUrls.length > 0)
        ? allImageUrls
        : (furnitureImageUrl ? [furnitureImageUrl] : []);
      if (imgUrls.length > 0) {
        try {
          // Run colour extraction and canvas load concurrently — same image, one fetch
          const [profile, canvas] = await Promise.all([
            imgUrls.length > 1
              ? extractColorProfileMulti(imgUrls)
              : extractColorProfile(imgUrls[0]),
            extractProductCanvas(imgUrls[0]),
          ]);
          colorProfile = profile;
          productCanvas = canvas ?? undefined;
        } catch { /* ignore — fallback profile + no texture */ }
      }
      const url = await generateFurnitureGLB(fType, dims, undefined, {
        primaryColor: colorProfile?.primaryColor,
        accentColor: colorProfile?.accentColor,
        hasMetal: colorProfile?.hasMetal,
        isGold: colorProfile?.isGold,
        glossiness: colorProfile?.glossiness,
        isWarm: colorProfile?.isWarm,
        isDark: colorProfile?.isDark,
        tertiaryColor: colorProfile?.tertiaryColor,
        // Keywords from listing text drive material roughness (velvet vs leather vs fabric)
        styleHints: `${listingTitle} ${listingDescription ?? ''} ${subtypeText}${furnitureMaterial ? ' material:' + furnitureMaterial : ''}`,
        imageUrl: furnitureImageUrl ?? undefined,
        productCanvas,
      });

      // Cache bust the blob so we don't load the old floating version
      setProceduralUrl(`${url}#v=${Date.now()}`);

      // Important: Add QuickLook scale-lock parameter for iOS
      setUsdzUrl(prevUsdz => prevUsdz ? `${prevUsdz.split('#')[0]}#allowsContentScaling=0` : null);

      setBuildProgress(100);
      setStep('model_ready');
    } catch (err) {
      console.error('[WebARViewer] GLB generation failed:', err);
      setStep('error');
      toast({
        title: 'Model Error',
        description: 'Could not build 3D model. Please try again.',
        variant: 'destructive',
      });
    } finally {
      clearInterval(interval);
    }
  }, [arAssets, fType, dims, proceduralUrl, subtypeText, listingTitle, listingDescription, furnitureMaterial, furnitureImageUrl, allImageUrls, toast]);

  // ── AI Generation Logic ──────────────────────────────────────────────────
  const startAIGeneration = async (useAllImages: boolean = false) => {
    if (aiStage === 'generating' || aiStage === 'polling') return;

    setAiStage('generating');
    setAiProgress(5);

    try {
      const imgUrls = (allImageUrls && allImageUrls.length > 0) ? allImageUrls : (furnitureImageUrl ? [furnitureImageUrl] : []);
      const targetUrl = useAllImages ? undefined : imgUrls[selectedImgIdx];

      const { task_id } = await arAssetsService.generate3D(listingId, targetUrl, useAllImages);
      setAiTaskId(task_id);
      setAiStage('polling');
      setAiProgress(15);
    } catch (err) {
      console.error('[WebARViewer] AI Start failed:', err);
      setAiStage('error');
      toast({
        title: "AI Generation Failed",
        description: "Could not start AI generation. Please try again later.",
        variant: "destructive"
      });
    }
  };

  // AI Polling Effect
  useEffect(() => {
    if (aiStage !== 'polling' || !aiTaskId) return;

    let isMounted = true;
    const poll = async () => {
      try {
        const status = await arAssetsService.poll3DStatus(listingId, aiTaskId);
        if (!isMounted) return;

        if (status.status === 'SUCCEEDED') {
          // The backend already downloaded it to local_url
          if (status.local_url) {
            setAiProgress(100);
            setAiStage('success');
            setTripoUrl(status.local_url);
            setViewMode('advanced');
            setStep('model_ready');
            
            // Auto-switch to AR tab so user sees the new model immediately
            setActiveTab('ar');
            
            // Reset aiStage after a tiny delay so the UI cleans up nicely
            setTimeout(() => setAiStage('idle'), 500);

            toast({
              title: "3D Model Ready",
              description: "AI generation complete! You can now view the high-quality model.",
            });
          } else {
            setAiStage('error');
            toast({
              title: "AI Generation Failed",
              description: "Model generated but failed to download to server. Please try again.",
              variant: "destructive"
            });
          }
        } else if (status.status === 'FAILED') {
          setAiStage('error');
          toast({
            title: "AI Generation Failed",
            description: status.error || "Generation failed at Tripo AI.",
            variant: "destructive"
          });
        } else {
          // Still processing
          setAiProgress(15 + (status.progress || 0) * 0.7);
        }
      } catch (err) {
        console.error('[WebARViewer] Polling error:', err);
        setAiStage('error');
        toast({
          title: "Polling Error",
          description: "Lost connection to the generation server. Please try again.",
          variant: "destructive"
        });
        // Stop polling
        if (isMounted) clearInterval(interval);
      }
    };

    const interval = setInterval(poll, 3000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [aiStage, aiTaskId, listingId, toast]);

  // ── Reset cached GLB when the furniture type or subtype changes ────────────
  // This ensures that if the user navigates between listings (or a delayed API
  // response updates furnitureSubtype), the model is rebuilt with the correct
  // dimensions and door count rather than showing the stale cached build.
  const prevFTypeRef = useRef<string | undefined>(undefined);
  const prevSubtypeRef = useRef<string | null | undefined>(undefined);
  useEffect(() => {
    if (prevFTypeRef.current === undefined) {
      // First mount — just record the initial values
      prevFTypeRef.current = fType;
      prevSubtypeRef.current = furnitureSubtype;
      return;
    }
    if (prevFTypeRef.current !== fType || prevSubtypeRef.current !== furnitureSubtype) {
      prevFTypeRef.current = fType;
      prevSubtypeRef.current = furnitureSubtype;
      // Revoke old GLB blob URL and clear state so prepareModel rebuilds
      if (proceduralUrl && proceduralUrl.startsWith('blob:')) {
        URL.revokeObjectURL(proceduralUrl);
      }
      setProceduralUrl(null);
      setStep('idle');
    }
  }, [fType, furnitureSubtype]);

  // ── Open sheet & trigger model build ──────────────────────────────────────
  const handleOpen = () => {
    setIsSheetOpen(true);
    prepareModel();
  };


  // ── model-viewer event handlers ───────────────────────────────────────────
  useEffect(() => {
    const mv = modelViewerRef.current;
    if (!mv) return;

    const onARStatus = (e: any) => {
      const status: string = e.detail?.status ?? '';
      setArStatus(status);

      if (status === 'session-started') {
        setStep('scanning');
        setScanPhase('tilting');
        setScanDuration(0);
        triggerHaptic('success');
      }

      if (status === 'object-placed') {
        setStep('placed');
        setShowCoach(true);
        triggerHaptic('success');
      }

      if (status === 'not-presenting') {
        setStep('model_ready');
        setScanPhase('tilting');
      }

      if (status === 'failed') {
        setStep('error');
        triggerHaptic('error');
        toast({
          title: 'AR Failed',
          description: 'Could not start AR. Ensure camera access is granted.',
          variant: 'destructive',
        });
      }
    };

    const onProgress = (e: any) => {
      const p = e.detail?.totalProgress ?? 0;
      setBuildProgress(Math.round(p * 100));
    };

    mv.addEventListener('ar-status', onARStatus);
    mv.addEventListener('progress', onProgress);
    return () => {
      mv.removeEventListener('ar-status', onARStatus);
      mv.removeEventListener('progress', onProgress);
    };
  }, [modelViewerRef.current, toast]);

  // ── TF.js room-object detection (runs once camera access is obtained) ─────
  const runObjectDetection = useCallback(async () => {
    // Ref guard prevents re-running when camera permission is denied and
    // tfLoading flips false → callback is recreated → effect fires again.
    if (detectedObjects.length > 0) return;
    if (!caps.hasCamera) return;

    setTfLoading(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: 320, height: 240 },
      });

      if (!videoRef.current) return;
      videoRef.current.srcObject = stream;
      await videoRef.current.play();

      // Dynamically import TF.js + COCO-SSD only when needed
      const tf = await import('@tensorflow/tfjs');
      const cocoSsd = await import('@tensorflow-models/coco-ssd');

      const model = await cocoSsd.load({ base: 'lite_mobilenet_v2' });
      const predictions = await model.detect(videoRef.current);

      // Stop camera
      stream.getTracks().forEach((t) => t.stop());
      videoRef.current.srcObject = null;

      const labels = [...new Set(predictions.map((p: any) => p.class as string))];
      setDetectedObjects(labels);
    } catch (e) {
      // non-fatal — object detection is optional
      console.warn('[WebARViewer] COCO-SSD detection skipped:', e);
    } finally {
      setTfLoading(false);
    }
  }, [caps.hasCamera, detectedObjects.length]);  // tfLoading intentionally omitted — ref guards re-entry

  // Kick off detection once sheet is open and model is ready
  useEffect(() => {
    if (isSheetOpen && step === 'model_ready' && caps.hasCamera) {
      runObjectDetection();
    }
  }, [isSheetOpen, step, caps.hasCamera, runObjectDetection]);

  // ── Haptic Feedback Helper ────────────────────────────────────────────────
  const triggerHaptic = (type: 'light' | 'medium' | 'success' | 'warning' | 'error') => {
    if (!('vibrate' in navigator)) return;

    switch (type) {
      case 'light': navigator.vibrate(10); break;
      case 'medium': navigator.vibrate(20); break;
      case 'success': navigator.vibrate([20, 30, 40]); break;
      case 'warning': navigator.vibrate([50, 100]); break;
      case 'error': navigator.vibrate([100, 50, 100]); break;
    }
  };

  // ── Scan Phase Logic ──────────────────────────────────────────────────────
  useEffect(() => {
    if (step !== 'scanning') return;

    const interval = setInterval(() => {
      setScanDuration(prev => {
        const next = prev + 1;
        // Coaching phases
        if (next === 4 && scanPhase === 'tilting') {
          setScanPhase('sweeping');
          triggerHaptic('light');
        }
        // Check if tracking has picked up a floor (hit-test found)
        const mv = modelViewerRef.current;
        if (mv?.arTracking === 'tracking' && scanPhase !== 'ready_to_place') {
          setScanPhase('ready_to_place');
          triggerHaptic('medium');
        }
        return next;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [step, scanPhase]);

  const getScanHint = () => {
    if (scanPhase === 'tilting') return "Point camera at the floor";
    if (scanPhase === 'sweeping') return "Scan slowly side to side";
    if (scanPhase === 'ready_to_place') return "Tap the floor to place furniture";
    return "";
  };

  // ── AR launch: directly invoke model-viewer's activateAR ──────────────────
  const launchAR = () => {
    const mv = modelViewerRef.current;
    if (!mv) return;
    try {
      mv.activateAR();
    } catch {
      toast({
        title: 'AR Launch Failed',
        description: 'Your device may not support WebXR. Try updating Chrome.',
        variant: 'destructive',
      });
    }
  };

  // ── model-viewer "ar-modes" string ────────────────────────────────────────
  const arModesAttr = caps.isChecked
    ? detectARModesAttr(caps.supportedModes)
    : 'webxr scene-viewer quick-look';

  const productPageUrl =
    typeof window !== 'undefined' ? window.location.href : '';

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <>
      {/* ─── Trigger Button ─────────────────────────────────────────────── */}
      <button
        onClick={handleOpen}
        className="
          w-full flex items-center justify-between
          bg-gradient-to-r from-[#143109] to-[#1e4d10]
          hover:from-[#1e4d10] hover:to-[#2a6616]
          active:scale-[0.98]
          text-white font-semibold
          px-4 py-3.5 rounded-2xl
          shadow-lg shadow-[#143109]/20
          transition-all duration-200
          relative overflow-hidden
          group
        "
      >
        {/* Shimmer sweep */}
        <span className="absolute inset-0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 bg-gradient-to-r from-transparent via-white/10 to-transparent" />

        <span className="flex items-center gap-3 z-10">
          <span className="bg-white/15 rounded-xl p-1.5">
            <Camera className="h-5 w-5" />
          </span>
          <span className="flex flex-col items-start leading-tight">
            <span className="text-sm font-bold">View in Your Room</span>
            <span className="text-[11px] text-white/70">Live AR · Real Scale · {cmLabel(dims)}</span>
          </span>
        </span>

        <span className="flex items-center gap-2 z-10">
          <CompatibilityBadge caps={caps} />
          <ChevronRight className="h-5 w-5 opacity-70 group-hover:translate-x-1 transition-transform" />
        </span>
      </button>

      {/* ─── Bottom Sheet ────────────────────────────────────────────────── */}
      <Sheet open={isSheetOpen} onOpenChange={setIsSheetOpen}>
        <SheetContent
          side="bottom"
          className="
            h-[92dvh] rounded-t-[28px]
            px-0 pt-0 pb-0
            flex flex-col
            bg-white
            overflow-hidden
          "
        >
          {/* Handle pill */}
          <div className="flex justify-center pt-3 pb-1 shrink-0">
            <div className="w-10 h-1 rounded-full bg-gray-200" />
          </div>

          {/* Header */}
          <SheetHeader className="px-5 pb-3 border-b border-gray-100 shrink-0">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <SheetTitle className="text-base font-bold text-gray-900 leading-tight truncate">
                  {listingTitle}
                </SheetTitle>
                <SheetDescription className="text-xs text-gray-500 mt-0.5 flex items-center gap-1">
                  <Ruler className="h-3 w-3" />
                  {mLabel(dims)}
                  {price && (
                    <>
                      <span className="mx-1 text-gray-300">·</span>
                      <span className="text-[#143109] font-semibold">
                        PKR {price.toLocaleString()}
                      </span>
                    </>
                  )}
                </SheetDescription>
              </div>
              <button
                onClick={() => setIsSheetOpen(false)}
                className="p-1.5 rounded-xl hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors shrink-0"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Tab switcher */}
            <div className="flex gap-1 mt-3">
              {(['ar', 'info'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`
                    flex-1 py-1.5 rounded-xl text-xs font-semibold transition-all
                    ${activeTab === tab
                      ? 'bg-[#143109] text-white shadow-sm'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}
                  `}
                >
                  {tab === 'ar' ? '📱 AR View' : 'ℹ️ Details'}
                </button>
              ))}
            </div>
          </SheetHeader>

          {/* Scrollable body */}
          <div className="flex-1 overflow-y-auto">
            {/* ── AR Tab ──────────────────────────────────────────────────── */}
            {activeTab === 'ar' && (
              <div className="flex flex-col h-full">

                {/* Building indicator */}
                {step === 'building_model' && (
                  <div className="flex-1 flex items-center justify-center px-5">
                    <ModelBuildingIndicator progress={buildProgress} />
                  </div>
                )}

                {/* Error state */}
                {step === 'error' && (
                  <div className="flex-1 flex flex-col items-center justify-center px-8 gap-4 py-8">
                    <AlertTriangle className="h-14 w-14 text-red-400" />
                    <div className="text-center">
                      <p className="font-semibold text-gray-900">Something went wrong</p>
                      <p className="text-sm text-gray-500 mt-1">
                        Could not build the 3D model. Check your connection and try again.
                      </p>
                    </div>
                    <Button
                      onClick={() => { setStep('idle'); setProceduralUrl(null); prepareModel(); }}
                      className="bg-[#143109] hover:bg-[#1e4d10]"
                    >
                      Retry
                    </Button>
                  </div>
                )}

                {/* Model viewer */}
                {(step === 'model_ready' || step === 'scanning' || step === 'placed') && (proceduralUrl || tripoUrl) && (
                  <div className="flex flex-col h-full">

                    {/* View Mode Toggle */}
                    <div className="px-5 pt-3 pb-1 bg-gradient-to-b from-gray-50 to-gray-50/50">
                      <div className="flex bg-gray-200/50 p-1 rounded-xl items-center shadow-inner">
                        <button
                          onClick={() => setViewMode('fast')}
                          className={`flex-1 flex flex-col items-center justify-center py-1.5 rounded-lg transition-all duration-200 ${viewMode === 'fast' ? 'bg-white shadow text-[#143109]' : 'text-gray-500 hover:text-gray-700'
                            }`}
                        >
                          <span className="text-[11px] font-bold">Fast View</span>
                          <span className="text-[9px] font-medium opacity-70 leading-none">CV Generated</span>
                        </button>
                        <button
                          onClick={() => setViewMode('advanced')}
                          className={`flex-1 flex flex-col items-center justify-center py-1.5 rounded-lg transition-all duration-200 ${viewMode === 'advanced' ? 'bg-[#143109] text-white shadow' : 'text-gray-500 hover:text-gray-700'
                            }`}
                        >
                          <span className="text-[11px] font-bold flex items-center gap-1">
                            <Sparkles className="h-3 w-3" /> Advanced 3D
                          </span>
                          <span className="text-[9px] font-medium opacity-70 leading-none">Tripo AI</span>
                        </button>
                      </div>
                    </div>

                    {/* model-viewer canvas area */}
                    <div className="relative flex-1 bg-gradient-to-b from-gray-50 to-gray-100" style={{ minHeight: '38vh' }}>
                      {/* Dimension overlay */}
                      <div className="absolute top-3 left-3 z-10">
                        <DimensionPill dims={dims} />
                      </div>

                      {/* AR status badge */}
                      {arStatus === 'session-started' && (
                        <div className="absolute top-3 right-3 z-10 flex items-center gap-1.5 bg-green-500/90 text-white text-xs font-semibold px-2.5 py-1 rounded-full shadow">
                          <span className="w-2 h-2 rounded-full bg-white animate-ping" />
                          Scanning floor…
                        </div>
                      )}
                      {arStatus === 'object-placed' && (
                        <div className="absolute top-3 right-3 z-10 flex items-center gap-1.5 bg-[#143109]/90 text-white text-xs font-semibold px-2.5 py-1 rounded-full shadow">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Placed!
                        </div>
                      )}

                      {/* ── model-viewer element ── */}
                      <model-viewer
                        ref={modelViewerRef as any}
                        src={(viewMode === 'advanced' && tripoUrl) ? tripoUrl : proceduralUrl || undefined}
                        ios-src={(viewMode === 'advanced' && arAssets?.model_usdz_url) ? getFullUrl(arAssets.model_usdz_url) : usdzUrl || undefined}
                        alt={listingTitle}
                        ar
                        ar-modes="webxr scene-viewer quick-look"
                        ar-placement="floor"
                        ar-scale="fixed"
                        camera-controls
                        touch-action="pan-y"
                        shadow-intensity={2.8}
                        shadow-softness={0}
                        environment-image="neutral"
                        exposure={1.2}
                        auto-rotate
                        auto-rotate-delay={2000}
                        rotation-per-second="10deg"
                        camera-orbit="-30deg 75deg auto"
                        interaction-prompt="auto"
                        loading="eager"
                        style={{
                          width: '100%',
                          height: '100%',
                          minHeight: '38vh',
                          '--poster-color': 'transparent',
                          background: 'transparent',
                        } as any}
                      >
                        {/* Custom AR button inside model-viewer slot */}
                        <button
                          slot="ar-button"
                          className="
                            absolute bottom-4 right-4
                            flex items-center gap-2
                            bg-[#143109] hover:bg-[#1e4d10] active:scale-95
                            text-white font-semibold text-sm
                            px-4 py-2.5 rounded-2xl
                            shadow-xl shadow-black/20
                            transition-all duration-150
                            z-20
                          "
                          style={{ position: 'absolute', bottom: '16px', right: '16px', zIndex: 20 }}
                        >
                          <Camera className="h-4 w-4" />
                          View in AR
                        </button>

                        {/* AR prompt slot — shown inside the native AR session (WebXR) */}
                        <div slot="ar-prompt" style={{
                          position: 'absolute',
                          bottom: '80px',
                          left: '50%',
                          transform: 'translateX(-50%)',
                          background: 'rgba(0,0,0,0.72)',
                          backdropFilter: 'blur(8px)',
                          borderRadius: '20px',
                          padding: '12px 20px',
                          color: '#fff',
                          fontSize: '13px',
                          fontWeight: '700',
                          whiteSpace: 'nowrap',
                          letterSpacing: '0.01em',
                          border: '1px solid rgba(255,255,255,0.15)',
                          pointerEvents: 'none',
                        } as any}>
                          👇 Point at floor &amp; tap to place
                        </div>

                        {/* Loading slot */}
                        <div slot="progress-bar" style={{ display: 'none' }} />
                      </model-viewer>

                      {/* Enriched Scanning Overlay */}
                      {step === 'scanning' && (
                        <ScanningOverlay phase={scanPhase} hint={getScanHint()} />
                      )}

                      {/* Post-Placement Coach */}
                      {step === 'placed' && showCoach && (
                        <PostPlacementCoach onDismiss={() => setShowCoach(false)} />
                      )}

                      {/* Detected objects overlay */}
                      {detectedObjects.length > 0 && (
                        <div className="absolute top-14 left-3 z-10 flex flex-wrap gap-1 max-w-[70%]">
                          {detectedObjects.slice(0, 4).map((obj) => (
                            <span
                              key={obj}
                              className="text-[10px] font-medium bg-black/50 text-white px-2 py-0.5 rounded-full backdrop-blur-sm"
                            >
                              {obj}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Bottom controls */}
                    <div className="px-5 pt-4 pb-6 bg-white shrink-0 space-y-3">

                      {/* Scan Phase Warnings */}
                      {step === 'scanning' && scanDuration > 8 && (
                        <div className="flex items-center gap-3 p-3 bg-amber-50 rounded-2xl border border-amber-200 animate-in fade-in zoom-in">
                          <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0" />
                          <div>
                            <p className="text-xs font-semibold text-amber-800">Slow scanning?</p>
                            <p className="text-[10px] text-amber-700">Try more light or move closer to the floor surface.</p>
                          </div>
                        </div>
                      )}

                      {/* Scanning instructions */}
                      {step === 'scanning' && (
                        <div className="space-y-2">
                          <div className="flex items-center gap-3 p-3 bg-green-50 rounded-2xl border border-green-200">
                            <Scan className="h-5 w-5 text-green-600 shrink-0 animate-pulse" />
                            <div>
                              <p className="text-xs font-semibold text-green-800">Scanning floor surface</p>
                              <p className="text-[11px] text-green-600">
                                Move phone slowly across the floor. A glowing reticle will appear — tap it to place.
                              </p>
                            </div>
                          </div>
                          {/* Dimension scale reference card */}
                          <div className="bg-[#143109]/5 rounded-2xl border border-[#143109]/10 p-3">
                            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-2">Furniture will appear at real scale ·  Scale locked 1:1</p>
                            <div className="flex items-center justify-between">
                              <div className="text-center">
                                <p className="text-base font-bold text-[#143109]">{dims.w}<span className="text-[10px] font-normal">cm</span></p>
                                <p className="text-[9px] text-gray-400 uppercase">Width</p>
                              </div>
                              <div className="h-px flex-1 mx-2 bg-[#143109]/20 relative">
                                <div className="absolute inset-y-0 left-0 right-0 flex items-center justify-center">
                                  <Ruler className="h-3.5 w-3.5 text-[#143109]/40" />
                                </div>
                              </div>
                              <div className="text-center">
                                <p className="text-base font-bold text-[#143109]">{dims.l}<span className="text-[10px] font-normal">cm</span></p>
                                <p className="text-[9px] text-gray-400 uppercase">Depth</p>
                              </div>
                              <div className="h-px flex-1 mx-2 bg-[#143109]/20" />
                              <div className="text-center">
                                <p className="text-base font-bold text-[#143109]">{dims.h}<span className="text-[10px] font-normal">cm</span></p>
                                <p className="text-[9px] text-gray-400 uppercase">Height</p>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Placed success */}
                      {step === 'placed' && (
                        <div className="space-y-2">
                          <div className="flex items-center gap-3 p-3 rounded-2xl border bg-[#143109]/5 border-[#143109]/20">
                            <CheckCircle2 className="h-5 w-5 text-[#143109] shrink-0" />
                            <div>
                              <p className="text-xs font-semibold text-[#143109]">Placed at true scale</p>
                              <p className="text-[11px] text-gray-600">
                                Drag to move · 2-finger twist to rotate · Scale locked 1:1
                              </p>
                            </div>
                          </div>
                        </div>
                      )}



                      {/* Desktop redirect hint */}
                      {caps.isDesktop && caps.isChecked && (
                        <DesktopQRHint url={productPageUrl} />
                      )}

                      {/* AR launch button (for non-desktops) */}
                      {!caps.isDesktop && caps.isSupported && step === 'model_ready' && (
                        <button
                          onClick={launchAR}
                          className="
                            w-full flex items-center justify-center gap-3
                            bg-gradient-to-r from-[#143109] to-[#2a6616]
                            hover:from-[#1e4d10] hover:to-[#336617]
                            active:scale-[0.98]
                            text-white font-bold text-base
                            py-4 rounded-2xl
                            shadow-xl shadow-[#143109]/30
                            transition-all duration-200
                          "
                        >
                          <Camera className="h-5 w-5" />
                          Launch AR in Your Room
                          <ChevronRight className="h-5 w-5 opacity-80" />
                        </button>
                      )}

                      {/* Not supported hint */}
                      {!caps.isDesktop && !caps.isSupported && caps.isChecked && (
                        <div className="p-4 bg-amber-50 rounded-2xl border border-amber-200">
                          <p className="text-sm font-semibold text-amber-800 flex items-center gap-2">
                            <AlertTriangle className="h-4 w-4" />
                            AR not supported on this device
                          </p>
                          <p className="text-xs text-amber-700 mt-1">
                            Your browser or device doesn't support WebXR AR. Try Chrome on an
                            ARCore-compatible Android, or Safari on iPhone/iPad.
                          </p>
                        </div>
                      )}

                      {/* Pre-launch checklist */}
                      {step === 'model_ready' && (
                        <PreLaunchChecklist dims={dims} />
                      )}

                      {/* Gesture hints */}
                      {step === 'model_ready' && !caps.isDesktop && (
                        <GestureHints />
                      )}

                      {/* AI Generation UI (Advanced) */}
                      {step === 'model_ready' && (
                        <div className="mt-4 pt-4 border-t border-gray-100">
                          {aiStage === 'idle' || aiStage === 'error' ? (
                            <div className="relative overflow-hidden bg-gradient-to-br from-[#0d2007] to-[#1a4510] p-5 rounded-2xl">
                              {/* Sparkle shimmer background */}
                              <div className="absolute inset-0 opacity-10 pointer-events-none"
                                style={{ backgroundImage: 'radial-gradient(circle at 20% 40%, #AAAE7F 0%, transparent 60%), radial-gradient(circle at 80% 70%, #143109 0%, transparent 50%)' }} />

                              <div className="relative">
                                <div className="flex items-center gap-2 mb-1">
                                  <Sparkles className="h-4 w-4 text-[#AAAE7F]" />
                                  <span className="text-[11px] font-bold text-[#AAAE7F] uppercase tracking-widest">Tripo AI · Photorealistic</span>
                                </div>
                                <p className="text-white font-bold text-base mb-1">Generate True 3D Model</p>
                                <p className="text-white/60 text-[11px] mb-3 leading-relaxed">
                                  Select the clearest, uncropped image showing the full product depth.
                                </p>

                                {/* Image Selector UI */}
                                {(allImageUrls && allImageUrls.length > 0) ? (
                                  <div className="flex gap-2 overflow-x-auto pb-3 mb-1 -mx-2 px-2 snap-x" style={{ scrollbarWidth: 'none' }}>
                                    {allImageUrls.map((imgUrl, idx) => (
                                      <button
                                        key={idx}
                                        onClick={() => setSelectedImgIdx(idx)}
                                        className={`relative shrink-0 w-16 h-16 rounded-xl overflow-hidden border-2 transition-all snap-center ${selectedImgIdx === idx
                                          ? 'border-[#AAAE7F] scale-105 shadow-md shadow-[#AAAE7F]/20'
                                          : 'border-white/10 opacity-60 hover:opacity-100'
                                          }`}
                                      >
                                        <img src={getFullUrl(imgUrl) || imgUrl} alt={`Thumbnail ${idx + 1}`} className="w-full h-full object-cover" />
                                        {selectedImgIdx === idx && (
                                          <div className="absolute top-1 right-1 bg-[#AAAE7F] text-[#143109] rounded-full p-0.5 shadow">
                                            <CheckCircle2 className="w-3 h-3" />
                                          </div>
                                        )}
                                      </button>
                                    ))}
                                  </div>
                                ) : null}

                                {aiStage === 'error' && (
                                  <p className="text-red-400 text-[10px] flex items-center gap-1 mb-3">
                                    <AlertTriangle className="h-3 w-3" /> Last attempt failed — try again
                                  </p>
                                )}

                                <button
                                  onClick={() => startAIGeneration(false)}
                                  className="w-full flex items-center justify-center gap-2.5 py-3.5 px-5 rounded-xl font-bold text-sm text-[#143109] bg-[#AAAE7F] hover:bg-[#bcc08e] active:scale-[0.97] transition-all duration-150 shadow-lg shadow-black/30"
                                >
                                  <Sparkles className="h-4 w-4" />
                                  Generate from Selected Image
                                </button>
                              </div>
                            </div>
                          ) : (
                            /* ── Rich 2D→3D Conversion Loading Screen ── */
                            <div className="relative overflow-hidden bg-gradient-to-br from-[#0d2007] to-[#1a4510] rounded-2xl p-5 animate-in fade-in zoom-in duration-300">
                              {/* Rotating orbital rings */}
                              <div className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden opacity-20">
                                <div className="w-48 h-48 rounded-full border-2 border-[#AAAE7F] animate-spin" style={{ animationDuration: '8s' }} />
                                <div className="absolute w-36 h-36 rounded-full border border-white animate-spin" style={{ animationDuration: '5s', animationDirection: 'reverse' }} />
                                <div className="absolute w-20 h-20 rounded-full border border-[#AAAE7F]/60 animate-spin" style={{ animationDuration: '3s' }} />
                              </div>

                              <div className="relative">
                                {/* Header */}
                                <div className="flex items-center justify-between mb-4">
                                  <div className="flex items-center gap-2">
                                    <div className="relative">
                                      <Loader2 className="h-5 w-5 text-[#AAAE7F] animate-spin" />
                                    </div>
                                    <span className="text-white font-bold text-sm">
                                      {aiStage === 'generating' && 'Initializing AI...'}
                                      {aiStage === 'polling' && 'Building 3D Model...'}
                                      {aiStage === 'downloading' && 'Applying Textures...'}
                                      {aiStage === 'success' && '✨ Model Ready!'}
                                    </span>
                                  </div>
                                  <span className="text-[#AAAE7F] font-mono font-bold text-sm">{Math.round(aiProgress)}%</span>
                                </div>

                                {/* Progress bar */}
                                <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden mb-4">
                                  <div
                                    className="h-full bg-gradient-to-r from-[#AAAE7F] to-white rounded-full transition-all duration-500"
                                    style={{ width: `${aiProgress}%` }}
                                  />
                                </div>

                                {/* Stage steps */}
                                {(() => {
                                  const stages = [
                                    { id: 'generating', label: 'Analyzing images', icon: '🔍' },
                                    { id: 'polling', label: 'Building geometry', icon: '🧊' },
                                    { id: 'downloading', label: 'Baking textures', icon: '🎨' },
                                    { id: 'success', label: 'Finalizing model', icon: '✅' },
                                  ];
                                  const currentIdx = stages.findIndex(s => s.id === aiStage);
                                  return (
                                    <div className="space-y-2">
                                      {stages.map((s, i) => {
                                        const done = i < currentIdx;
                                        const active = i === currentIdx;
                                        return (
                                          <div key={s.id} className={`flex items-center gap-3 px-3 py-2 rounded-xl transition-all duration-300 ${active ? 'bg-white/10' : 'opacity-40'}`}>
                                            <span className="text-base leading-none">{s.icon}</span>
                                            <span className={`text-xs font-semibold ${active ? 'text-white' : done ? 'text-[#AAAE7F]' : 'text-white/40'}`}>
                                              {s.label}
                                            </span>
                                            {done && <span className="ml-auto text-[#AAAE7F] text-xs">✓</span>}
                                            {active && <Loader2 className="ml-auto h-3 w-3 text-white animate-spin" />}
                                          </div>
                                        );
                                      })}
                                    </div>
                                  );
                                })()}

                                <p className="text-white/40 text-[10px] mt-3 text-center">
                                  {aiStage === 'polling' && 'Typically 20–40 seconds · Keep this panel open'}
                                </p>
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Room detection status */}
                      {tfLoading && (
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          Detecting room objects…
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Hidden video for TF.js COCO-SSD */}
                <video
                  ref={videoRef}
                  className="hidden"
                  muted
                  playsInline
                  style={{ width: 1, height: 1 }}
                />
              </div>
            )}

            {/* ── Info Tab ────────────────────────────────────────────────── */}
            {activeTab === 'info' && (
              <div className="px-5 py-4 space-y-4">

                {/* Room scale analysis */}
                <RoomScaleBadge dims={dims} />

                {/* Dimensions card */}
                <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100 space-y-3">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
                    <Ruler className="h-3.5 w-3.5" />
                    Dimensions
                  </p>
                  <div className="grid grid-cols-3 gap-3">
                    {([
                      { label: 'Width', val: `${dims.w} cm` },
                      { label: 'Depth', val: `${dims.l} cm` },
                      { label: 'Height', val: `${dims.h} cm` },
                    ] as const).map((d) => (
                      <div key={d.label} className="text-center">
                        <p className="text-xl font-bold text-[#143109]">{d.val}</p>
                        <p className="text-[10px] text-gray-500 mt-0.5">{d.label}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* AR compatibility */}
                <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100 space-y-2">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
                    <Smartphone className="h-3.5 w-3.5" />
                    AR Compatibility
                  </p>
                  <div className="space-y-2 text-sm">
                    <InfoRow
                      label="Your device"
                      value={caps.isAndroid ? 'Android' : caps.isIOS ? 'iOS' : 'Desktop'}
                      ok={caps.isSupported}
                    />
                    <InfoRow
                      label="Best AR mode"
                      value={caps.mode === 'none' ? 'Not available' : caps.mode}
                      ok={caps.mode !== 'none'}
                    />
                    <InfoRow
                      label="Camera access"
                      value={caps.hasCamera ? 'Available' : 'Not detected'}
                      ok={caps.hasCamera}
                    />
                    <InfoRow
                      label="Motion sensors"
                      value={caps.hasMotionSensor ? 'Present' : 'Absent'}
                      ok={caps.hasMotionSensor}
                    />
                  </div>
                </div>

                {/* Detected objects */}
                {detectedObjects.length > 0 && (
                  <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100 space-y-2">
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
                      <Eye className="h-3.5 w-3.5" />
                      Room Objects Detected
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {detectedObjects.map((obj) => (
                        <span
                          key={obj}
                          className="text-xs bg-[#143109]/10 text-[#143109] font-medium px-2.5 py-1 rounded-full"
                        >
                          {obj}
                        </span>
                      ))}
                    </div>
                  </div>
                )}


                {/* How AR works */}
                <div className="p-4 bg-blue-50 rounded-2xl border border-blue-100 space-y-2">
                  <p className="text-xs font-semibold text-blue-700 uppercase tracking-wider flex items-center gap-1.5">
                    <Info className="h-3.5 w-3.5" />
                    How it works
                  </p>
                  <ol className="text-xs text-blue-800 space-y-1.5 list-decimal list-inside">
                    <li>Tap <strong>Launch AR in Your Room</strong></li>
                    <li>Grant camera permission when asked</li>
                    <li>Move your phone slowly over the <strong>floor</strong></li>
                    <li>Tap the reticle (circle) to place the furniture</li>
                    <li>Drag to move · Twist to rotate</li>
                  </ol>
                </div>

                {/* Model info */}
                <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1.5 mb-2">
                    <Box className="h-3.5 w-3.5" />
                    3D Model
                  </p>
                  <p className="text-xs text-gray-600">
                    {arAssets?.model_glb_url
                      ? 'Custom 3D model provided by seller · Real design, shape & colours'
                      : `Procedural ${fType} model · Coloured from product image · ≈30k polygons`}
                  </p>
                  {arAssets?.polygon_count && (
                    <p className="text-xs text-gray-500 mt-1">
                      Polygon count: {arAssets.polygon_count.toLocaleString()}
                    </p>
                  )}
                </div>

                <Sparkles className="mx-auto h-6 w-6 text-gray-300 my-2" />
              </div>
            )}
          </div>
        </SheetContent >
      </Sheet >
    </>
  );
}

// ─── Tiny helper ──────────────────────────────────────────────────────────────
function InfoRow({ label, value, ok }: { label: string; value: string; ok: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-gray-600">{label}</span>
      <span className={`font-medium flex items-center gap-1 ${ok ? 'text-green-700' : 'text-amber-700'}`}>
        {ok
          ? <CheckCircle2 className="h-3.5 w-3.5" />
          : <AlertTriangle className="h-3.5 w-3.5" />}
        {value}
      </span>
    </div>
  );
}
