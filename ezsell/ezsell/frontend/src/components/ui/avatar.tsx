import React from 'react';

interface AvatarProps {
  seed: string;
  size?: number;
  className?: string;
}

const Avatar: React.FC<AvatarProps> = ({ seed, size = 40, className = "" }) => {
  // Simple hash function to generate deterministic values from the seed
  const getHash = (str: string) => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    return Math.abs(hash);
  };

  const hash = getHash(seed || "default");

  // Generate colors based on the hash
  const hue1 = hash % 360;
  const hue2 = (hash * 137) % 360;
  const saturation = 65 + (hash % 15);
  const lightness = 45 + (hash % 10);

  const color1 = `hsl(${hue1}, ${saturation}%, ${lightness}%)`;
  const color2 = `hsl(${hue2}, ${saturation}%, ${lightness}%)`;

  // Generate a pattern type based on the hash
  const patterns = [
    // Circles
    <circle cx="20" cy="20" r="15" fill="white" fillOpacity="0.2" />,
    // Rectangles
    <rect x="10" y="10" width="20" height="20" rx="4" fill="white" fillOpacity="0.1" transform={`rotate(${hash % 90} 20 20)`} />,
    // Triangles-ish
    <path d="M20 5 L35 30 L5 30 Z" fill="white" fillOpacity="0.15" transform={`rotate(${hash % 180} 20 20)`} />,
    // Dots
    <g opacity="0.2">
      <circle cx="10" cy="10" r="2" fill="white" />
      <circle cx="30" cy="10" r="2" fill="white" />
      <circle cx="10" cy="30" r="2" fill="white" />
      <circle cx="30" cy="30" r="2" fill="white" />
    </g>
  ];

  const pattern = patterns[hash % patterns.length];

  return (
    <div
      className={`relative overflow-hidden shrink-0 transition-transform hover:scale-105 active:scale-95 ${className}`}
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
        <path
          d={`M${hash % 40} 0 Q20 20 ${40 - (hash % 40)} 40`}
          stroke="white"
          strokeOpacity="0.1"
          strokeWidth="2"
          fill="none"
        />
      </svg>
      {/* Gloss overlay for premium feel */}
      <div className="absolute inset-0 bg-gradient-to-tr from-white/10 to-transparent pointer-events-none" />
    </div>
  );
};

export default Avatar;
