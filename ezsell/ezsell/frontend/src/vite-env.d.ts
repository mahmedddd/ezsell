/// <reference types="vite/client" />

// ── Google model-viewer custom element ──────────────────────────────────────
// Ensures <model-viewer> is recognized in TSX without errors.
import type { ModelViewerElement } from '@google/model-viewer';

declare global {
  namespace JSX {
    interface IntrinsicElements {
      'model-viewer': Partial<ModelViewerElement> &
        React.DOMAttributes<ModelViewerElement> & {
          // Frequently-used attributes not yet in the shipped TS interface
          ref?: React.Ref<ModelViewerElement | null>;
          style?: React.CSSProperties;
          class?: string;
          slot?: string;
          children?: React.ReactNode;
        };
    }
  }
}
