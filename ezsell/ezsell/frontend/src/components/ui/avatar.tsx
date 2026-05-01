import React from 'react';

export interface AvatarProps {
  seed: string;
  initials?: string;
  size?: number;
  className?: string;
  patternIndex?: number;
}

/**
 * Parses a special avatar_url string (e.g. "init:M" or "style:sunrise:2")
 * into props for the Avatar component.
 */
export const parseAvatarUrl = (avatarUrl: string | null | undefined, fallbackSeed: string = "default"): AvatarProps => {
  if (!avatarUrl) return { seed: fallbackSeed };

  if (avatarUrl.startsWith('init:')) {
    const char = avatarUrl.split(':')[1] || fallbackSeed[0] || '?';
    return { seed: avatarUrl, initials: char };
  }

  if (avatarUrl.startsWith('style:')) {
    const parts = avatarUrl.split(':');
    return {
      seed: parts[1] || fallbackSeed,
      patternIndex: parts[2] ? parseInt(parts[2]) : undefined
    };
  }

  // If it's a real URL, the parent component should handle it via <img>,
  // but if it falls back here, we just use it as a seed.
  return { seed: avatarUrl || fallbackSeed };
};

const Avatar: React.FC<AvatarProps> = ({ seed, initials, size = 40, className = "", patternIndex }) => {
  // Simple hash function to generate deterministic values from the seed
  const getHash = (str: string) => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    return Math.abs(hash);
  };

  const hash = getHash(seed || "default");

  // Generate colors based on the hash (or seed)
  const hue1 = (hash * 137) % 360;
  const hue2 = (hue1 + 40) % 360; // Complementary-ish gradient
  const saturation = 65 + (hash % 10);
  const lightness = 45 + (hash % 10);

  const color1 = `hsl(${hue1}, ${saturation}%, ${lightness}%)`;
  const color2 = `hsl(${hue2}, ${saturation}%, ${lightness}%)`;

  const activePatternIndex = patternIndex ?? (hash % 5);

  // Generate a pattern type based on the hash
  const patterns = [
    // 0: Circles
    <circle cx="20" cy="20" r="15" fill="white" fillOpacity="0.2" />,
    // 1: Rectangles
    <rect x="10" y="10" width="20" height="20" rx="4" fill="white" fillOpacity="0.1" transform={`rotate(${hash % 90} 20 20)`} />,
    // 2: Triangles-ish
    <path d="M20 5 L35 30 L5 30 Z" fill="white" fillOpacity="0.15" transform={`rotate(${hash % 180} 20 20)`} />,
    // 3: Dots
    <g opacity="0.2">
      <circle cx="10" cy="10" r="2" fill="white" />
      <circle cx="30" cy="10" r="2" fill="white" />
      <circle cx="10" cy="30" r="2" fill="white" />
      <circle cx="30" cy="30" r="2" fill="white" />
    </g>,
    // 4: Waves
    <path d="M0 20 Q10 10 20 20 T40 20" stroke="white" strokeOpacity="0.2" strokeWidth="2" fill="none" />
  ];

  const pattern = patterns[activePatternIndex];

  return (
    <div
      className={`relative overflow-hidden shrink-0 transition-all flex items-center justify-center ${className}`}
      style={{
        width: size,
        height: size,
        borderRadius: '35%', // Premium squircle look
        background: `linear-gradient(135deg, ${color1}, ${color2})`,
        boxShadow: `0 4px 12px ${color1}44`
      }}
    >
      <svg
        viewBox="0 0 40 40"
        fill="none"
        className="absolute inset-0 pointer-events-none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ width: '100%', height: '100%' }}
      >
        <defs>
          <linearGradient id={`grad-${hash}`} x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
            <stop stopColor={color1} />
            <stop offset="1" stopColor={color2} />
          </linearGradient>
        </defs>
        {pattern}
        {/* Abstract shapes */}
        <circle cx={10 + (hash % 20)} cy={10 + ((hash >> 4) % 20)} r={5 + (hash % 10)} fill="white" fillOpacity="0.1" />
      </svg>

      {initials ? (
        <span
          className="relative z-10 font-black text-white select-none drop-shadow-md"
          style={{ fontSize: size * 0.4 }}
        >
          {initials.toUpperCase()}
        </span>
      ) : null}

      {/* Gloss overlay for premium feel */}
      <div className="absolute inset-0 bg-gradient-to-tr from-white/20 to-transparent pointer-events-none" />
      <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-black/10 to-transparent pointer-events-none" />
    </div>
  );
};

export default Avatar;
