import Avatar from "./Avatar";
import { cn } from "@/lib/utils";

export const AVATAR_IDS = Array.from({ length: 8 }, (_, i) => `avatar-${i + 1}`);

interface AvatarPickerProps {
  value: string;
  onChange: (avatarId: string) => void;
  disabled?: boolean;
  columns?: 4 | 8;
}

export default function AvatarPicker({ value, onChange, disabled, columns = 8 }: AvatarPickerProps) {
  return (
    <div className={cn("grid gap-1.5", columns === 4 ? "grid-cols-4" : "grid-cols-8")} role="radiogroup" aria-label="Choose an avatar">
      {AVATAR_IDS.map((id) => (
        <button
          key={id}
          type="button"
          role="radio"
          aria-checked={value === id}
          aria-label={`Avatar ${id}`}
          disabled={disabled}
          onClick={() => onChange(id)}
          className={cn(
            "rounded-full p-0.5 transition-all",
            value === id
              ? "ring-2 ring-primary ring-offset-2"
              : "opacity-70 hover:opacity-100 hover:ring-1 hover:ring-primary/40",
            disabled && "opacity-40",
          )}
        >
          <Avatar avatarId={id} size={36} />
        </button>
      ))}
    </div>
  );
}
