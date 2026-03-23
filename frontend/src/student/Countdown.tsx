import { useState, useEffect } from "react";

interface Props {
  endTime: string | null;
  visibleByDefault: boolean;
}

function formatTime(totalSeconds: number): string {
  if (totalSeconds <= 0) return "00:00:00";
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  return [h, m, s].map((v) => String(v).padStart(2, "0")).join(":");
}

export function Countdown({ endTime, visibleByDefault }: Props) {
  const [hidden, setHidden] = useState(
    () => localStorage.getItem("flash_trading_timer_hidden") === "true"
      || !visibleByDefault
  );
  const [remaining, setRemaining] = useState<number | null>(null);
  const [currentTime, setCurrentTime] = useState("");

  // Mise à jour du temps restant chaque seconde
  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit", second: "2-digit" })
      );
      if (endTime) {
        const end = new Date(endTime).getTime();
        setRemaining(Math.max(0, Math.floor((end - Date.now()) / 1000)));
      }
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [endTime]);

  const toggle = () => {
    const next = !hidden;
    setHidden(next);
    localStorage.setItem("flash_trading_timer_hidden", String(next));
  };

  const isUrgent = remaining !== null && remaining > 0 && remaining < 600;   // < 10 min
  const isWarning = remaining !== null && remaining > 0 && remaining < 1800; // < 30 min
  const isOver = remaining !== null && remaining === 0;

  const timerColor = isOver
    ? "#6b7280"
    : isUrgent
    ? "#f87171"
    : isWarning
    ? "#fbbf24"
    : "#4ade80";

  if (hidden) {
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <span style={{ color: "#555", fontSize: 14 }}>{currentTime}</span>
        <button
          onClick={toggle}
          style={{
            background: "none",
            border: "1px solid #333",
            borderRadius: 6,
            color: "#666",
            cursor: "pointer",
            padding: "4px 12px",
            fontSize: 13,
          }}
        >
          ⏱ Afficher le chrono
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
      {endTime && (
        <div style={{ textAlign: "right" }}>
          <div
            style={{
              fontFamily: "monospace",
              fontSize: 36,
              fontWeight: 800,
              color: timerColor,
              letterSpacing: 2,
              animation: isUrgent ? "pulse 1s ease-in-out infinite" : "none",
              lineHeight: 1,
            }}
          >
            {remaining === null ? "--:--:--" : formatTime(remaining)}
          </div>
          <div style={{ fontSize: 11, color: "#555", marginTop: 2 }}>
            {isOver ? "temps écoulé" : isUrgent ? "dépêchez-vous !" : isWarning ? "bientôt la fin" : "temps restant"}
          </div>
        </div>
      )}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
        <span style={{ color: "#555", fontSize: 14, fontFamily: "monospace" }}>{currentTime}</span>
        <button
          onClick={toggle}
          style={{
            background: "none",
            border: "1px solid #333",
            borderRadius: 6,
            color: "#555",
            cursor: "pointer",
            padding: "2px 8px",
            fontSize: 11,
          }}
        >
          Masquer
        </button>
      </div>
    </div>
  );
}
