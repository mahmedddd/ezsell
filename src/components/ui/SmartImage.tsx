/**
 * SmartImage — Instant-feel image loader
 * ────────────────────────────────────────
 * Shows an animated shimmer skeleton while the image downloads.
 * Fades the image in smoothly once fully decoded — no pixel-by-pixel reveal,
 * no blank white gaps. Works for both eager (hero) and lazy (card thumbnail) loads.
 */

import { useState } from 'react';

interface SmartImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string;
  alt: string;
  className?: string;
  wrapperClassName?: string;
  /** 'eager' for above-fold images, 'lazy' for cards/thumbnails (default: 'lazy') */
  priority?: 'eager' | 'lazy';
}

export function SmartImage({
  src,
  alt,
  className = '',
  wrapperClassName = '',
  priority = 'lazy',
  ...rest
}: SmartImageProps) {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);

  return (
    <div className={`relative overflow-hidden ${wrapperClassName}`}>
      {/* Shimmer skeleton — always present, hidden once image loads */}
      {!loaded && !error && (
        <div
          className="absolute inset-0 bg-gradient-to-r from-gray-100 via-gray-200 to-gray-100 animate-shimmer"
          style={{
            backgroundSize: '200% 100%',
            animation: 'shimmer 1.4s ease-in-out infinite',
          }}
        />
      )}

      {/* Actual image — invisible until decoded, then fades in */}
      {!error && (
        <img
          src={src}
          alt={alt}
          loading={priority === 'eager' ? 'eager' : 'lazy'}
          fetchPriority={priority === 'eager' ? 'high' : 'auto'}
          decoding="async"
          onLoad={() => setLoaded(true)}
          onError={() => { setLoaded(true); setError(true); }}
          className={`${className} transition-opacity duration-300 ${loaded ? 'opacity-100' : 'opacity-0'}`}
          {...rest}
        />
      )}

      {/* Error fallback */}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
          <svg className="w-1/2 h-1/2 max-w-[2rem] max-h-[2rem] text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
      )}
    </div>
  );
}
