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

import { useState, useRef, useEffect, useCallback } from 'react';
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
import { arAssetsService } from '@/lib/api';

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

// ─── Helpers ──────────────────────────────────────────────────────────────────

function cmLabel(dims: FurnitureDimensions) {
  return `${dims.w} × ${dims.l} × ${dims.h} cm`;
}

function mLabel(dims: FurnitureDimensions) {
  return `${(dims.w / 100).toFixed(2)}m × ${(dims.l / 100).toFixed(2)}m × ${(dims.h / 100).toFixed(2)}m`;
}

function detectARModesAttr(supportedModes: string[]): string {
  return supportedModes.join(' ');
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
  const [glbUrl, setGlbUrl] = useState<string | null>(null);
  const [usdzUrl, setUsdzUrl] = useState<string | null>(null);
  const [arStatus, setArStatus] = useState<string>('');
  const [detectedObjects, setDetectedObjects] = useState<string[]>([]);
  const [tfLoading, setTfLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'ar' | 'info'>('ar');

  const modelViewerRef = useRef<any>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const prevGlbUrl = useRef<string | undefined>(undefined);
  // Prevents COCO-SSD from re-running every time tfLoading state changes (which
  // would recreate the useCallback and re-fire the useEffect in an infinite loop).
  const detectionAttemptedRef = useRef(false);

  // AI image-to-3D generation state
  type AIStage = 'idle' | 'requesting' | 'processing' | 'complete' | 'failed';
  const [aiStage, setAiStage] = useState<AIStage>('idle');
  const [aiProgress, setAiProgress] = useState(0);
  const [aiTaskId, setAiTaskId] = useState<string | null>(null);

  // Only render for furniture
  if (category?.toLowerCase() !== 'furniture') return null;

  // ── Resolve furniture metadata ─────────────────────────────────────────────
  const fType: FurnitureType = resolveFurnitureType(furnitureType, listingTitle, listingDescription);
  // Normalise furniture_subtype underscores so '3_door' → '3 door' matches dimension regex
  const subtypeText = (furnitureSubtype ?? '').replace(/_/g, ' ');
  const dims: FurnitureDimensions =
    dimensionsCm ?? arAssets?.dimensions_cm ?? resolveSmartDimensions(fType, listingTitle, `${listingDescription ?? ''} ${subtypeText}`);

  // ── Build (or fetch) the GLB ───────────────────────────────────────────────
  const prepareModel = useCallback(async () => {
    if (glbUrl) return; // already built

    setStep('building_model');

    // Simulate progress ticks while async work runs
    let prog = 0;
    const interval = setInterval(() => {
      prog = Math.min(prog + 12, 88);
      setBuildProgress(prog);
    }, 180);

    try {
      // 1. Use server-side GLB if available
      if (arAssets?.model_glb_url) {
        setGlbUrl(arAssets.model_glb_url);
        if (arAssets.model_usdz_url) setUsdzUrl(arAssets.model_usdz_url);
      } else {
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
        const url = await generateFurnitureGLB(fType, dims, prevGlbUrl.current, {
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
        prevGlbUrl.current = url;
        setGlbUrl(url);
      }

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
  }, [arAssets, fType, dims, glbUrl, furnitureSubtype, listingTitle, listingDescription, furnitureMaterial, toast]);

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
      if (prevGlbUrl.current) {
        URL.revokeObjectURL(prevGlbUrl.current);
        prevGlbUrl.current = undefined;
      }
      setGlbUrl(null);
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
      if (status === 'session-started') setStep('scanning');
      if (status === 'object-placed') setStep('placed');
      if (status === 'not-presenting') setStep('model_ready');
      if (status === 'failed') {
        setStep('error');
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
    if (detectionAttemptedRef.current || detectedObjects.length > 0) return;
    if (!caps.hasCamera) return;
    detectionAttemptedRef.current = true;  // mark immediately before any await

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

  // Cleanup object URL on unmount
  useEffect(() => {
    return () => {
      if (prevGlbUrl.current) URL.revokeObjectURL(prevGlbUrl.current);
    };
  }, []);

  // ── AI Image-to-3D generation ──────────────────────────────────────────────
  const startAIGeneration = useCallback(async () => {
    if (!furnitureImageUrl) {
      toast({ title: 'No product image', description: 'This listing has no photo to convert to 3D.', variant: 'destructive' });
      return;
    }
    try {
      setAiStage('requesting');
      // Pass ALL listing images so Tripo3D can use multi-angle reconstruction.
      // allImageUrls contains the full set: front, side, back, top etc.
      const photos = (allImageUrls && allImageUrls.length > 0) ? allImageUrls : [furnitureImageUrl];
      const result = await arAssetsService.generate3D(listingId, furnitureImageUrl, photos);
      setAiTaskId(result.task_id);
      setAiStage('processing');
      setAiProgress(0);
      const isMultiview = (result as any).mode === 'multiview';
      const imgCount = (result as any).image_count ?? photos.length;
      if (isMultiview) {
        toast({
          title: `✨ AI 3D Generation Started (${imgCount} angles)`,
          description: 'Multi-angle reconstruction in progress — front, side & back photos used for higher accuracy. Takes ~2 minutes.',
        });
      } else {
        // Only one image — prompt the user to add more angle photos
        toast({
          title: '📸 AI 3D Started — Add More Angles for Best Results',
          description: 'Only 1 photo found. Upload front, side, and back photos to the listing for a much more accurate 3D model.',
        });
      }
    } catch (err: any) {
      setAiStage('idle');
      const msg: string = err?.response?.data?.detail ?? 'AI 3D service not available. Check that TRIPO_API_KEY is set in backend/.env';
      toast({ title: 'Could not start AI generation', description: msg, variant: 'destructive' });
    }
  }, [furnitureImageUrl, allImageUrls, listingId, toast]);

  // Polling — runs every 3 s while AI task is in progress
  useEffect(() => {
    if (aiStage !== 'processing' || !aiTaskId) return;
    const poll = async () => {
      try {
        const res = await arAssetsService.poll3DStatus(listingId, aiTaskId);
        setAiProgress(res.progress ?? 0);
        if (res.status === 'complete' && res.glb_url) {
          if (prevGlbUrl.current) { URL.revokeObjectURL(prevGlbUrl.current); prevGlbUrl.current = undefined; }
          setGlbUrl(res.glb_url);
          setAiStage('complete');
          setStep('model_ready');
          toast({ title: '🎉 True 3D Model Ready!', description: 'AI-generated from the actual product photo — real design, real colours.' });
        } else if (res.status === 'failed') {
          setAiStage('failed');
          toast({ title: 'AI Generation Failed', description: res.error ?? 'Unknown error. Try again.', variant: 'destructive' });
        }
      } catch { /* network hiccup — keep polling */ }
    };
    const id = setInterval(poll, 3000);
    return () => clearInterval(id);
  }, [aiStage, aiTaskId, listingId, toast]);

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
                      onClick={() => { setStep('idle'); setGlbUrl(null); prepareModel(); }}
                      className="bg-[#143109] hover:bg-[#1e4d10]"
                    >
                      Retry
                    </Button>
                  </div>
                )}

                {/* Model viewer */}
                {(step === 'model_ready' || step === 'scanning' || step === 'placed') && glbUrl && (
                  <div className="flex flex-col h-full">

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
                        src={glbUrl}
                        ios-src={usdzUrl ?? undefined}
                        alt={listingTitle}
                        ar
                        ar-modes={arModesAttr || 'webxr scene-viewer quick-look'}
                        ar-placement="floor"
                        camera-controls
                        touch-action="pan-y"
                        shadow-intensity="1.6"
                        shadow-softness="0.9"
                        environment-image="neutral"
                        exposure="0.95"
                        auto-rotate
                        auto-rotate-delay="3000"
                        rotation-per-second="15deg"
                        interaction-prompt="auto"
                        loading="eager"
                        style={{
                          width: '100%',
                          height: '100%',
                          minHeight: '38vh',
                          '--poster-color': 'transparent',
                          background: 'transparent',
                        } as React.CSSProperties}
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

                        {/* Loading slot */}
                        <div slot="progress-bar" style={{ display: 'none' }} />
                      </model-viewer>

                      {/* Detected objects overlay */}
                      {detectedObjects.length > 0 && (
                        <div className="absolute bottom-3 left-3 z-10 flex flex-wrap gap-1 max-w-[70%]">
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

                      {/* Scanning instructions */}
                      {step === 'scanning' && (
                        <div className="flex items-center gap-3 p-3 bg-green-50 rounded-2xl border border-green-200">
                          <Scan className="h-5 w-5 text-green-600 shrink-0 animate-pulse" />
                          <div>
                            <p className="text-xs font-semibold text-green-800">Scanning floor</p>
                            <p className="text-[11px] text-green-600">
                              Move your phone slowly across the floor until the reticle appears, then tap.
                            </p>
                          </div>
                        </div>
                      )}

                      {/* Placed success */}
                      {step === 'placed' && (
                        <div className="flex items-center gap-3 p-3 bg-[#143109]/8 rounded-2xl border border-[#143109]/20">
                          <CheckCircle2 className="h-5 w-5 text-[#143109] shrink-0" />
                          <div>
                            <p className="text-xs font-semibold text-[#143109]">Furniture placed!</p>
                            <p className="text-[11px] text-gray-600">
                              Drag to reposition · Twist to rotate · Scale locked to real dimensions
                            </p>
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

                      {/* Gesture hints */}
                      {step === 'model_ready' && !caps.isDesktop && (
                        <GestureHints />
                      )}

                      {/* ── AI 3D generation strip ──────────────────────── */}
                      {step === 'model_ready' && !arAssets?.model_glb_url && aiStage === 'idle' && furnitureImageUrl && (
                        <button
                          onClick={startAIGeneration}
                          className="
                            w-full flex items-center justify-center gap-2
                            bg-gradient-to-r from-purple-600 to-indigo-600
                            hover:from-purple-700 hover:to-indigo-700
                            active:scale-[0.98] text-white font-semibold text-sm
                            py-3.5 rounded-2xl shadow-lg transition-all duration-200
                          "
                        >
                          <Sparkles className="h-4 w-4" />
                          Generate True 3D from Product Photo
                          <span className="text-xs opacity-60 ml-1">(AI · ~2 min)</span>
                        </button>
                      )}

                      {/* AI generating — progress bar */}
                      {(aiStage === 'requesting' || aiStage === 'processing') && (
                        <div className="flex flex-col gap-2 p-3.5 bg-purple-50 rounded-2xl border border-purple-200">
                          <div className="flex items-center gap-2">
                            <Loader2 className="h-4 w-4 text-purple-600 animate-spin shrink-0" />
                            <p className="text-xs font-semibold text-purple-800">
                              {aiStage === 'requesting'
                                ? 'Starting AI generation…'
                                : `Converting photo to 3D model… ${aiProgress}%`}
                            </p>
                          </div>
                          {aiStage === 'processing' && (
                            <Progress value={aiProgress} className="h-1.5" />
                          )}
                          <p className="text-[11px] text-purple-500">
                            AI is building a true 3D mesh with the real design, shape &amp; colours of this product
                          </p>
                        </div>
                      )}

                      {/* AI complete badge */}
                      {aiStage === 'complete' && (
                        <div className="flex items-center gap-2 p-3 bg-purple-50 rounded-2xl border border-purple-200">
                          <Sparkles className="h-4 w-4 text-purple-600 shrink-0" />
                          <p className="text-xs font-semibold text-purple-800">True 3D model loaded — generated from the product photo</p>
                        </div>
                      )}

                      {/* AI failed — retry */}
                      {aiStage === 'failed' && (
                        <button
                          onClick={() => { setAiStage('idle'); setAiTaskId(null); }}
                          className="w-full flex items-center justify-center gap-2 text-xs text-purple-700 font-semibold py-2.5 rounded-xl border border-purple-200 hover:bg-purple-50 transition-colors"
                        >
                          <Sparkles className="h-3.5 w-3.5" />
                          Retry AI 3D Generation
                        </button>
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

                {/* ── Multi-angle photo accuracy card ──────────────────────── */}
                <div className={`p-4 rounded-2xl border space-y-2 ${(allImageUrls && allImageUrls.length >= 3)
                    ? 'bg-green-50 border-green-200'
                    : (allImageUrls && allImageUrls.length >= 2)
                      ? 'bg-blue-50 border-blue-200'
                      : 'bg-amber-50 border-amber-200'
                  }`}>
                  <p className={`text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 ${(allImageUrls && allImageUrls.length >= 3) ? 'text-green-700' :
                      (allImageUrls && allImageUrls.length >= 2) ? 'text-blue-700' : 'text-amber-700'
                    }`}>
                    <Camera className="h-3.5 w-3.5" />
                    3D Accuracy — {(allImageUrls?.length ?? 1)} photo{(allImageUrls?.length ?? 1) !== 1 ? 's' : ''} provided
                  </p>
                  {allImageUrls && allImageUrls.length >= 3 ? (
                    <p className="text-xs text-green-800">
                      ✅ <strong>Excellent!</strong> {allImageUrls.length} angle photos will be used for multi-view 3D reconstruction — the model will closely match the actual product.
                    </p>
                  ) : allImageUrls && allImageUrls.length >= 2 ? (
                    <p className="text-xs text-blue-800">
                      📸 <strong>Good</strong> — 2 photos found. Add a <strong>back</strong> or <strong>top</strong> photo to the listing for even better 3D accuracy.
                    </p>
                  ) : (
                    <div className="space-y-1.5">
                      <p className="text-xs text-amber-800 font-medium">
                        ⚠️ Only 1 photo — AI 3D accuracy is limited to a single view.
                      </p>
                      <p className="text-xs text-amber-700">
                        For the most accurate 3D model, ask the seller to add photos from these angles:
                      </p>
                      <div className="grid grid-cols-2 gap-1 mt-1">
                        {['📷 Front (straight on)', '📷 Side (left or right)', '📷 Back', '📷 Top / overhead'].map(angle => (
                          <span key={angle} className="text-[10px] bg-amber-100 text-amber-800 font-medium px-2 py-1 rounded-lg">{angle}</span>
                        ))}
                      </div>
                      <p className="text-[10px] text-amber-600 mt-1">
                        💡 4 angles = ~100% reconstruction accuracy with Tripo3D multi-view AI
                      </p>
                    </div>
                  )}
                </div>

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
                    {arAssets?.model_glb_url || aiStage === 'complete'
                      ? 'AI-generated true 3D from product photo · Real design, shape & colours'
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
        </SheetContent>
      </Sheet>
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
