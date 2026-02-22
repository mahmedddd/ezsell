/**
 * useARSupport — detects WebXR / ARCore / ARKit capability at runtime.
 *
 * Returns a stable object so callers can conditionally render the AR button,
 * show a "your device doesn't support AR" message, or choose between
 * WebXR Scene Viewer (Android) vs QuickLook (iOS).
 */
import { useState, useEffect } from 'react';

export type ARMode = 'webxr' | 'scene-viewer' | 'quick-look' | 'none';

export interface ARCapabilities {
  /** Whether ANY form of AR is available */
  isSupported: boolean;
  /** Best available AR mode for this device/browser */
  mode: ARMode;
  /** Ordered list of modes the device supports */
  supportedModes: ARMode[];
  /** True if the device has an IMU (needed for WebXR) */
  hasMotionSensor: boolean;
  /** True when running in a native iOS Safari / WKWebView */
  isIOS: boolean;
  /** True when running in Chrome on Android */
  isAndroid: boolean;
  /** True when running on a desktop browser */
  isDesktop: boolean;
  /** True if the browser supports the getUserMedia (camera) */
  hasCamera: boolean;
  /** Checked — set to false only while detection is still in flight */
  isChecked: boolean;
  /** Raw WebXR AR session supported flag (async check) */
  webXRARSupported: boolean;
}

const DEFAULT_CAPS: ARCapabilities = {
  isSupported: false,
  mode: 'none',
  supportedModes: [],
  hasMotionSensor: false,
  isIOS: false,
  isAndroid: false,
  isDesktop: false,
  hasCamera: false,
  isChecked: false,
  webXRARSupported: false,
};

/** Sniffs UA string — not perfect, but sufficient for AR gating */
function sniffDevice() {
  const ua = navigator.userAgent;
  const isIOS =
    /iPad|iPhone|iPod/.test(ua) ||
    (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  const isAndroid = /Android/.test(ua);
  const isDesktop = !isIOS && !isAndroid;
  return { isIOS, isAndroid, isDesktop };
}

async function checkWebXRARSupport(): Promise<boolean> {
  try {
    if (!('xr' in navigator)) return false;
    const xr = (navigator as any).xr;
    if (!xr?.isSessionSupported) return false;
    return await xr.isSessionSupported('immersive-ar');
  } catch {
    return false;
  }
}

async function checkCameraAccess(): Promise<boolean> {
  try {
    if (!navigator.mediaDevices?.getUserMedia) return false;
    // Don't actually request permission here — just check API availability
    const devices = await navigator.mediaDevices.enumerateDevices();
    return devices.some((d) => d.kind === 'videoinput');
  } catch {
    return false;
  }
}

function checkMotionSensor(): boolean {
  return 'DeviceMotionEvent' in window || 'DeviceOrientationEvent' in window;
}

export function useARSupport(): ARCapabilities {
  const [caps, setCaps] = useState<ARCapabilities>(DEFAULT_CAPS);

  useEffect(() => {
    let cancelled = false;

    async function detect() {
      const { isIOS, isAndroid, isDesktop } = sniffDevice();
      const [webXRARSupported, hasCamera] = await Promise.all([
        checkWebXRARSupport(),
        checkCameraAccess(),
      ]);
      const hasMotionSensor = checkMotionSensor();

      if (cancelled) return;

      // Build supported mode list (priority order used by <model-viewer ar-modes>)
      const supportedModes: ARMode[] = [];

      if (webXRARSupported) supportedModes.push('webxr');
      if (isAndroid) supportedModes.push('scene-viewer');
      if (isIOS) supportedModes.push('quick-look');

      const mode: ARMode = supportedModes[0] ?? 'none';
      const isSupported = supportedModes.length > 0;

      setCaps({
        isSupported,
        mode,
        supportedModes,
        hasMotionSensor,
        isIOS,
        isAndroid,
        isDesktop,
        hasCamera,
        isChecked: true,
        webXRARSupported,
      });
    }

    detect();
    return () => {
      cancelled = true;
    };
  }, []);

  return caps;
}
