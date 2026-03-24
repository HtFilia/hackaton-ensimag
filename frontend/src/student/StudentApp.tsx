import { useState, useEffect } from "react";
import { useStudentResults, useHackathonConfig } from "./useStudentResults";
import { Countdown } from "./Countdown";
import { PalierCard } from "./PalierCard";
import { Confetti } from "./Confetti";

const PALIERS = [1, 2, 3, 4, 5, 6];

function timeAgo(date: Date): string {
  const s = Math.floor((Date.now() - date.getTime()) / 1000);
  if (s < 5) return "à l'instant";
  if (s < 60) return `il y a ${s}s`;
  return `il y a ${Math.floor(s / 60)}min`;
}

export function StudentApp() {
  const { data, lastFetch, notFound } = useStudentResults();
  const config = useHackathonConfig();
  const [tick, setTick] = useState(0);
  const [showConfetti, setShowConfetti] = useState(false);

  // Force re-render pour mettre à jour "il y a Xs"
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, []);

  void tick;

  const passedCount = PALIERS.filter(
    (n) => data?.levels[`level${n}`]?.status === "passed"
  ).length;

  const allPassed = passedCount === 6;
  const progressPct = (passedCount / 6) * 100;

  // Déclencher confetti une seule fois quand tout est validé
  useEffect(() => {
    if (allPassed) {
      setShowConfetti(true);
      const timer = setTimeout(() => setShowConfetti(false), 6000);
      return () => clearTimeout(timer);
    }
  }, [allPassed]);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#0d1117",
        color: "#e0e0e0",
        fontFamily: "'Segoe UI', system-ui, -apple-system, sans-serif",
        padding: "20px 28px",
      }}
    >
      {showConfetti && <Confetti />}

      {/* ── En-tête ─────────────────────────────────────────────────────── */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 20,
          borderBottom: "1px solid #21262d",
          paddingBottom: 16,
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 800 }}>
            ⚡ {config?.title ?? "Flash Trading Challenge"}
          </h1>
          <p style={{ margin: "4px 0 0", color: "#555", fontSize: 14 }}>
            {config?.subtitle ?? "Dashboard Étudiant"}
            {data?.team ? (
              <>
                {" "}&mdash; Équipe{" "}
                <strong style={{ color: "#c4b5fd" }}>{data.team}</strong>
              </>
            ) : (
              <span style={{ color: "#f87171" }}>
                {" "}&mdash; Lancez <code>make register</code>
              </span>
            )}
          </p>
        </div>
        <Countdown
          endTime={config?.end_time ?? null}
          visibleByDefault={config?.timer_visible_by_default ?? true}
        />
      </div>

      {/* ── Barre de progression ─────────────────────────────────────────── */}
      <div style={{ marginBottom: 20 }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 6,
          }}
        >
          <span style={{ fontSize: 14, color: "#888" }}>
            Progression :{" "}
            <strong style={{ color: allPassed ? "#4ade80" : "#e0e0e0" }}>
              {passedCount}/6 paliers réussis
              {allPassed && " — Félicitations ! 🎉"}
            </strong>
          </span>
          <span style={{ fontSize: 12, color: "#444" }}>
            {lastFetch ? timeAgo(lastFetch) : "En attente…"}{" "}
            &bull; actualisation toutes les 3s
          </span>
        </div>
        <div
          style={{
            height: 10,
            background: "#21262d",
            borderRadius: 5,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: "100%",
              width: `${progressPct}%`,
              background: allPassed
                ? "#22c55e"
                : progressPct > 0
                ? "linear-gradient(90deg, #3b82f6, #8b5cf6)"
                : "transparent",
              borderRadius: 5,
              transition: "width 0.6s ease",
            }}
          />
        </div>
      </div>

      {/* ── Avertissement si pas de résultats ───────────────────────────── */}
      {notFound && (
        <div
          style={{
            background: "#1a1200",
            border: "1px solid #d97706",
            borderRadius: 8,
            padding: "14px 18px",
            marginBottom: 20,
            fontSize: 14,
            lineHeight: 1.6,
          }}
        >
          <strong>⚠ Aucun résultat trouvé.</strong> Ce dashboard est lancé par :
          <br />
          <code
            style={{
              background: "#0d1117",
              border: "1px solid #333",
              padding: "4px 10px",
              borderRadius: 4,
              marginTop: 8,
              display: "inline-block",
              color: "#7dd3fc",
              fontSize: 13,
            }}
          >
            make web
          </code>
          <br />
          <span style={{ color: "#888", fontSize: 12 }}>
            Les résultats se mettent à jour automatiquement toutes les 5 secondes.
          </span>
        </div>
      )}

      {/* ── Grille des paliers ───────────────────────────────────────────── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 14,
          marginBottom: 28,
        }}
      >
        {PALIERS.map((n) => (
          <PalierCard
            key={n}
            level={n}
            result={data?.levels[`level${n}`]}
            firstPassTime={data?.first_pass_times?.[`level${n}`]}
          />
        ))}
      </div>

      {/* ── Panneau Aide rapide ──────────────────────────────────────────── */}
      <QuickHelp />

      {/* ── Pied de page ────────────────────────────────────────────────── */}
      <div
        style={{
          marginTop: 24,
          fontSize: 12,
          color: "#333",
          textAlign: "center",
          borderTop: "1px solid #161b22",
          paddingTop: 12,
        }}
      >
        <code style={{ color: "#444" }}>make test</code>
        {" — résultats dans le terminal  ·  "}
        <code style={{ color: "#444" }}>make web</code>
        {" — dashboard live avec mise à jour toutes les 5s"}
      </div>
    </div>
  );
}

// ── Panneau d'aide rapide (dépliable) ─────────────────────────────────────────

function QuickHelp() {
  const [open, setOpen] = useState(false);

  return (
    <div
      style={{
        border: "1px solid #21262d",
        borderRadius: 10,
        overflow: "hidden",
      }}
    >
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          width: "100%",
          background: "#161b22",
          border: "none",
          color: "#888",
          cursor: "pointer",
          padding: "12px 18px",
          textAlign: "left",
          fontSize: 14,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "#1c2128")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "#161b22")}
      >
        <span>📚 Aide rapide — Rappels essentiels</span>
        <span>{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div
          style={{
            background: "#0d1117",
            padding: "16px 20px",
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 16,
            fontSize: 13,
          }}
        >
          <InfoBlock title="Structure d'un Order">
            {[
              "order.id         — identifiant unique",
              "order.asset      — symbole (AAPL, TSLA…)",
              "order.side       — Side.BUY ou Side.SELL",
              "order.order_type — OrderType.LIMIT / MARKET / …",
              "order.price      — prix limite",
              "order.quantity   — quantité restante",
              "order.action     — Action.NEW / CANCEL / AMEND / CLOSE",
              "order.time_in_force — TimeInForce.GTC / IOC / FOK",
              "order.visible_quantity — tranche iceberg (None = normal)",
            ]}
          </InfoBlock>
          <InfoBlock title="Patron général (tous les paliers)">
            {[
              "from copy import deepcopy",
              "",
              "def process_orders(initial_book, orders):",
              "    mbook = deepcopy(initial_book)",
              "    for order in orders:",
              "        book = mbook.get_or_create(order.asset)",
              "        # ... traiter l'ordre ...",
              "    return mbook",
            ]}
          </InfoBlock>
          <InfoBlock title="Règles de matching">
            {[
              "BUY matche les asks si ask.price <= buy.price",
              "SELL matche les bids si bid.price >= sell.price",
              "Priorité : prix d'abord, puis ordre d'arrivée (FIFO)",
              "Bids : triés par prix décroissant",
              "Asks : triés par prix croissant",
              "Exécution partielle : le reste repose dans le carnet",
            ]}
          </InfoBlock>
          <InfoBlock title="Commandes utiles">
            {[
              "make register        → choisir son équipe (une seule fois)",
              "make test            → tests + dashboard auto (5s)",
              "make test LEVEL=3    → tester un seul palier",
              "make web             → ouvrir ce dashboard",
              "make clean           → arrêter les processus",
              "",
              "git push origin <équipe> → soumettre au classement",
              "",
              "Le dashboard se rafraîchit automatiquement toutes les 3s.",
            ]}
          </InfoBlock>
        </div>
      )}
    </div>
  );
}

function InfoBlock({ title, children }: { title: string; children: string[] }) {
  return (
    <div>
      <div style={{ fontWeight: 600, color: "#7dd3fc", marginBottom: 8, fontSize: 13 }}>
        {title}
      </div>
      <div
        style={{
          fontFamily: "monospace",
          fontSize: 12,
          color: "#8b949e",
          lineHeight: 1.7,
          background: "#0a0e14",
          borderRadius: 6,
          padding: "8px 12px",
        }}
      >
        {children.map((line, i) =>
          line === "" ? (
            <br key={i} />
          ) : (
            <div key={i}>{line}</div>
          )
        )}
      </div>
    </div>
  );
}
