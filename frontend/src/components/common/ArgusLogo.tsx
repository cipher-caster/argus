interface ArgusLogoProps {
  size?: number;
  className?: string;
}

export function ArgusLogo({ size = 32, className }: ArgusLogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 36 36"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Background */}
      <rect width="36" height="36" rx="9" fill="#6366f1" />

      {/* Outer eye almond */}
      <path
        d="M4 18 C8 10 28 10 32 18 C28 26 8 26 4 18Z"
        fill="rgba(255,255,255,0.08)"
        stroke="rgba(255,255,255,0.9)"
        strokeWidth="1.2"
        strokeLinejoin="round"
      />

      {/* Iris outer ring */}
      <circle cx="18" cy="18" r="6" fill="rgba(255,255,255,0.12)" stroke="rgba(255,255,255,0.5)" strokeWidth="1" />

      {/* Iris inner ring */}
      <circle cx="18" cy="18" r="3.5" fill="rgba(255,255,255,0.2)" stroke="rgba(255,255,255,0.7)" strokeWidth="1" />

      {/* Pupil */}
      <circle cx="18" cy="18" r="2" fill="white" />

      {/* Specular highlight */}
      <circle cx="19.8" cy="16.2" r="0.8" fill="rgba(255,255,255,0.6)" />
    </svg>
  );
}
