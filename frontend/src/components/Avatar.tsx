const AVATAR_BG = [
  "#fca5a5", "#fdba74", "#fcd34d", "#86efac",
  "#7dd3fc", "#c4b5fd", "#f9a8d4", "#99f6e4",
];
const AVATAR_FG = [
  "#7f1d1d", "#7c2d12", "#713f12", "#14532d",
  "#0c4a6e", "#4c1d95", "#831843", "#134e4a",
];

function avatarIndex(avatarId: string): number {
  const match = /avatar-(\d+)/.exec(avatarId);
  const n = match ? parseInt(match[1], 10) : 1;
  return Math.abs(n - 1) % AVATAR_BG.length;
}

interface AvatarProps {
  avatarId: string;
  size?: number;
  className?: string;
}

export default function Avatar({ avatarId, size = 32, className }: AvatarProps) {
  const i = avatarIndex(avatarId);
  const bg = AVATAR_BG[i];
  const fg = AVATAR_FG[i];
  const eye = i % 4;
  const mouth = Math.floor(i / 2) % 4;
  return (
    <svg
      viewBox="0 0 48 48"
      width={size}
      height={size}
      className={className}
      role="img"
      aria-label="Learner avatar"
    >
      <circle cx="24" cy="24" r="22" fill={bg} />
      {i % 2 === 1 && (
        <circle cx="24" cy="4" r="3" fill={fg} />
      )}
      {eye === 0 && (
        <>
          <circle cx="17" cy="20" r="3" fill={fg} />
          <circle cx="31" cy="20" r="3" fill={fg} />
        </>
      )}
      {eye === 1 && (
        <>
          <path d="M13 20 q4 -5 8 0" stroke={fg} strokeWidth="2.5" fill="none" strokeLinecap="round" />
          <path d="M27 20 q4 -5 8 0" stroke={fg} strokeWidth="2.5" fill="none" strokeLinecap="round" />
        </>
      )}
      {eye === 2 && (
        <>
          <circle cx="17" cy="20" r="3.6" fill={fg} />
          <circle cx="18" cy="19" r="1.2" fill={bg} />
          <circle cx="31" cy="20" r="3.6" fill={fg} />
          <circle cx="32" cy="19" r="1.2" fill={bg} />
        </>
      )}
      {eye === 3 && (
        <>
          <rect x="13" y="17" width="8" height="6" rx="3" fill={fg} />
          <rect x="27" y="17" width="8" height="6" rx="3" fill={fg} />
        </>
      )}
      {mouth === 0 && (
        <path d="M16 31 q8 8 16 0" stroke={fg} strokeWidth="2.5" fill="none" strokeLinecap="round" />
      )}
      {mouth === 1 && (
        <path d="M18 30 h12" stroke={fg} strokeWidth="2.5" strokeLinecap="round" />
      )}
      {mouth === 2 && (
        <path d="M15 30 q9 12 18 0 Z" fill={fg} />
      )}
      {mouth === 3 && (
        <circle cx="24" cy="32" r="4" fill="none" stroke={fg} strokeWidth="2.5" />
      )}
    </svg>
  );
}
