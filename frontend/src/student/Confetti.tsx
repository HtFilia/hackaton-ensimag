import { useMemo } from "react";

const COLORS = [
  "#fbbf24", "#f87171", "#34d399", "#60a5fa",
  "#a78bfa", "#f472b6", "#2dd4bf", "#fb923c",
];

interface Piece {
  id: number;
  left: string;
  delay: string;
  duration: string;
  color: string;
  size: string;
  isCircle: boolean;
}

export function Confetti() {
  const pieces = useMemo<Piece[]>(
    () =>
      Array.from({ length: 80 }, (_, i) => ({
        id: i,
        left: `${(i * 1.27) % 100}%`,
        delay: `${(i * 0.07) % 4}s`,
        duration: `${2.5 + (i % 7) * 0.3}s`,
        color: COLORS[i % COLORS.length],
        size: `${6 + (i % 5) * 2}px`,
        isCircle: i % 3 !== 0,
      })),
    []
  );

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
        zIndex: 999,
        overflow: "hidden",
      }}
    >
      <style>{`
        @keyframes confetti-fall {
          0%   { transform: translateY(-30px) rotate(0deg);   opacity: 1; }
          80%  { opacity: 1; }
          100% { transform: translateY(105vh) rotate(540deg); opacity: 0; }
        }
      `}</style>
      {pieces.map((p) => (
        <div
          key={p.id}
          style={{
            position: "absolute",
            top: 0,
            left: p.left,
            width: p.size,
            height: p.size,
            backgroundColor: p.color,
            borderRadius: p.isCircle ? "50%" : "2px",
            animation: `confetti-fall ${p.duration} ${p.delay} ease-in forwards`,
          }}
        />
      ))}
    </div>
  );
}
