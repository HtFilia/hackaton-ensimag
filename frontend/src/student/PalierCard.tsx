import { useState, useEffect, useRef } from "react";
import type { LevelResult, Snapshot, BookSnapshot } from "./types";

// ── Contenu pédagogique par palier ───────────────────────────────────────────

const PALIER_NAMES: Record<number, string> = {
  1: "Ordres Limite",
  2: "Ordres Marché",
  3: "Annulation / Modif.",
  4: "IOC & FOK",
  5: "Iceberg",
  6: "Enchère Clôture",
};

const FIELDS: Record<number, string[]> = {
  1: ["order.id", "order.side", "order.price", "order.quantity", "order.asset"],
  2: ['order.order_type  →  "limit" | "market"'],
  3: ['order.action  →  "NEW" | "CANCEL" | "AMEND"'],
  4: ['order.time_in_force  →  "GTC" | "IOC" | "FOK"'],
  5: ["order.visible_quantity  →  Optional[float]"],
  6: ['order.order_type  →  "loc" | "moc"', 'order.action  →  "CLOSE"'],
};

const HINTS: Record<number, string[]> = {
  1: [
    "Commencez par `mbook = deepcopy(initial_book)` — ne jamais modifier l'état initial directement.",
    "BUY matche contre les asks (triés croissants) si `ask.price <= buy.price`. SELL contre les bids (décroissants) si `bid.price >= sell.price`.",
    "Pour insérer un bid : avancez tant que `bids[i].price >= order.price`, puis insérez. Pour un ask, tant que `asks[i].price <= order.price`.",
  ],
  2: [
    "Un MARKET ignore le prix lors du matching — supprimez la condition `best.price <= order.price`.",
    "Seule différence avec P1 : si `order.order_type == OrderType.MARKET`, ne JAMAIS réinsérer dans le carnet même avec une quantité restante.",
    "Un MARKET sur un carnet vide est simplement annulé, sans erreur.",
  ],
  3: [
    "AMEND = (1) retirer l'ordre original du carnet avec `pop()`, (2) `amended = copy(orig)`, (3) changer uniquement `price` et `quantity`, (4) réinsérer. `copy()` préserve `side`, `order_type`, `asset`, etc.",
    "Pour CANCEL et AMEND, `order.id` est l'identifiant de l'ordre CIBLE (pas celui de l'ordre entrant lui-même).",
    "CANCEL ou AMEND sur un ID inexistant → ignorer silencieusement. Pas d'exception.",
  ],
  4: [
    "FOK : avant de toucher au carnet, comptez la liquidité disponible aux prix éligibles. Si total < quantity → rejeter l'ordre entier, rien n'est exécuté.",
    "IOC : exécutez normalement avec `_match()`, mais ne remettez JAMAIS le reste dans le carnet, même pour un LIMIT.",
    "Pour la vérification FOK sur un LIMIT : ne comptez que les niveaux dont `o.price <= buy.price` (ou `>= sell.price`). Ne comptez pas les niveaux hors-prix.",
  ],
  5: [
    "La quantité TOTALE (`order.quantity`) est disponible au matching, pas seulement la tranche visible. `visible_quantity` est juste la taille de tranche affichée.",
    "Après chaque échange partiel : `best.visible_quantity = min(best.visible_quantity, best.quantity)`. Cela recalcule la tranche si elle dépasse le total restant.",
    "L'iceberg reste à sa POSITION dans le carnet après rechargement — pas de `pop + reinsert`. La priorité temporelle est conservée.",
  ],
  6: [
    "Maintenez `auction_queue: Dict[str, List[Order]]` séparé du carnet principal. Les ordres LOC et MOC vont UNIQUEMENT dans cette file, jamais dans le carnet.",
    "Pour trouver P* : pour chaque prix candidat LOC, calculez `min(buy_vol(P), sell_vol(P))`. Les MOC comptent à N'IMPORTE quel prix. Prenez le P qui maximise ce min.",
    "Après l'enchère : `queue.clear()` — TOUS les ordres LOC/MOC sont annulés, même ceux partiellement exécutés.",
    "CANCEL/AMEND cherchent d'abord dans le carnet continu, puis dans `auction_queue`. Vérifiez les deux endroits.",
  ],
};

const PITFALLS: Record<number, string> = {
  1: "Piège : la condition de match est `ask.price <= buy.price` (pas `<`). Un prix égal est exécutable.",
  2: "Piège : pensez à traiter aussi le cas où `order.order_type == OrderType.MARKET` dans la condition de match (pas de vérification de prix).",
  3: "Piège : lors d'un AMEND, si `req.price` ou `req.quantity` vaut 0 ou None, gardez la valeur de l'original.",
  4: "Piège : pour FOK, la vérification de volume doit être sensible au prix pour les LIMIT — ne comptez pas les niveaux hors-prix.",
  5: "Piège : ne pas confondre `order.quantity` (total restant) et `order.visible_quantity` (taille de tranche). Le matching se base sur `quantity`.",
  6: "Piège : le carnet LIMIT continu n'est PAS affecté par l'enchère de clôture. Seule la `auction_queue` est vidée.",
};

// ── Indices contextuels basés sur le message d'erreur ────────────────────────

function getContextualHint(level: number, message: string): string | null {
  const m = message.toLowerCase();
  if (m.includes("timed out") || m.includes("timeout"))
    return "Boucle infinie probable — vérifiez la condition de sortie de votre while.";
  if (m.includes("attributeerror") && m.includes("nonetype"))
    return "Accès à un attribut sur None. Le carnet est peut-être vide — vérifiez avant de matcher.";
  if (m.includes("attributeerror"))
    return "Erreur d'attribut. Vérifiez les noms : order.price, order.quantity, order.side…";
  if (m.includes("typeerror") && m.includes("'<'"))
    return "Comparaison de types incompatibles — comparez-vous un float avec un string ou None ?";
  if (m.includes("typeerror"))
    return "Erreur de type — vérifiez que vous ne mélangez pas float/int/None dans vos calculs.";
  if (m.includes("recursionerror"))
    return "Récursion infinie. Évitez les appels récursifs ou augmentez la garde de terminaison.";
  if (m.includes("process_orders not found"))
    return "La fonction process_orders() est introuvable. Vérifiez le nom exact et l'indentation.";
  if (m.includes("must return multibook"))
    return "Votre fonction doit retourner le MultiBook — pensez à `return mbook` en fin de fonction.";
  if (m.includes("must return orderbook"))
    return "Ce palier attend un OrderBook, pas un MultiBook.";
  if (m.includes("final book mismatch")) {
    const levelHints: Record<number, string> = {
      1: "Le carnet final ne correspond pas. Vérifiez la condition `ask.price <= buy.price` et la réinsertion des restes.",
      2: "Vérifiez que les ordres MARKET ne sont JAMAIS réinsérés dans le carnet, même partiellement remplis.",
      3: "Pour CANCEL/AMEND, cherchez l'ordre par `order.id` dans le bon carnet d'actif.",
      4: "Pour FOK : comptez toute la liquidité avant d'exécuter. Pour IOC : ne jamais réinsérer le reste.",
      5: "Rechargement iceberg : `visible_quantity = min(visible_quantity, quantity)` après chaque trade.",
      6: "Les ordres LOC/MOC doivent aller dans `auction_queue`, pas dans le carnet continu.",
    };
    return levelHints[level] ?? null;
  }
  return null;
}

// ── Visualiseur diff carnet ────────────────────────────────────────────────────

function isMultiAsset(s: Snapshot): s is Record<string, BookSnapshot> {
  return s !== null && typeof s === "object" && !("bids" in s);
}

function MiniBook({ label, book }: { label: string; book: BookSnapshot | null | undefined }) {
  const bids = book?.bids ?? [];
  const asks = book?.asks ?? [];

  return (
    <div style={{ flex: 1 }}>
      <div style={{ color: "#555", fontSize: 10, marginBottom: 4, textTransform: "uppercase", letterSpacing: 0.5 }}>
        {label}
      </div>
      {bids.length === 0 && asks.length === 0 ? (
        <div style={{ color: "#333", fontStyle: "italic", fontSize: 11 }}>vide</div>
      ) : (
        <div style={{ fontFamily: "monospace", fontSize: 11, lineHeight: 1.6 }}>
          {[...asks].reverse().map((a, i) => (
            <div key={`a${i}`} style={{ color: "#f87171" }}>
              A {a.price} × {a.quantity}
            </div>
          ))}
          {bids.length > 0 && asks.length > 0 && (
            <div style={{ borderTop: "1px solid #333", margin: "2px 0" }} />
          )}
          {bids.map((b, i) => (
            <div key={`b${i}`} style={{ color: "#4ade80" }}>
              B {b.price} × {b.quantity}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function BookDiff({ expected, got }: { expected: Snapshot; got: Snapshot }) {
  if (expected === null && got === null) return null;

  if (isMultiAsset(expected) || isMultiAsset(got)) {
    const assets = new Set([
      ...Object.keys((expected as Record<string, BookSnapshot>) ?? {}),
      ...Object.keys((got as Record<string, BookSnapshot>) ?? {}),
    ]);
    const sortedAssets = [...assets].sort();
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {sortedAssets.map((asset) => (
          <div key={asset}>
            <div style={{ color: "#7dd3fc", fontSize: 10, textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>
              {asset}
            </div>
            <div style={{ display: "flex", gap: 16 }}>
              <MiniBook
                label="Attendu"
                book={(expected as Record<string, BookSnapshot>)?.[asset]}
              />
              <MiniBook
                label="Obtenu"
                book={(got as Record<string, BookSnapshot>)?.[asset]}
              />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div style={{ display: "flex", gap: 16 }}>
      <MiniBook label="Attendu" book={expected as BookSnapshot} />
      <MiniBook label="Obtenu" book={got as BookSnapshot} />
    </div>
  );
}

// ── Couleurs par statut ───────────────────────────────────────────────────────

const STATUS_STYLE: Record<string, { bg: string; border: string; text: string; label: string }> = {
  passed: { bg: "#0d2a0d", border: "#22c55e", text: "#4ade80", label: "✓ RÉUSSI" },
  failed: { bg: "#2a0d0d", border: "#ef4444", text: "#f87171", label: "✗ ÉCHEC" },
  not_tested: { bg: "#161622", border: "#2d2d44", text: "#6b7280", label: "— À TESTER" },
  error: { bg: "#2a1e0d", border: "#f59e0b", text: "#fbbf24", label: "⚠ ERREUR" },
};

// ── Composant ─────────────────────────────────────────────────────────────────

interface Props {
  level: number;
  result: LevelResult | undefined;
  firstPassTime?: string; // ISO string
}

export function PalierCard({ level, result, firstPassTime }: Props) {
  const [showHints, setShowHints] = useState(false);
  const prevStatus = useRef<string | null>(null);
  const [popAnim, setPopAnim] = useState(false);

  const status = result?.status ?? "not_tested";
  const style = STATUS_STYLE[status] ?? STATUS_STYLE.not_tested;

  useEffect(() => {
    if (prevStatus.current !== null && prevStatus.current !== "passed" && status === "passed") {
      setPopAnim(true);
      setTimeout(() => setPopAnim(false), 400);
    }
    prevStatus.current = status;
  }, [status]);

  const failedFixtures = result?.fixtures.filter((f) => !f.passed) ?? [];

  // Formatage heure de première validation
  const validatedAt = firstPassTime ? firstPassTime.slice(11, 19) : null;

  return (
    <div
      style={{
        background: style.bg,
        border: `2px solid ${style.border}`,
        borderRadius: 12,
        padding: "18px 20px",
        display: "flex",
        flexDirection: "column",
        gap: 10,
        animation: popAnim ? "pop 0.4s ease" : "none",
        transition: "border-color 0.4s ease, background 0.4s ease",
      }}
    >
      {/* Titre, statut et chrono */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ fontSize: 11, color: "#555", textTransform: "uppercase", letterSpacing: 1 }}>
            Palier {level}
          </div>
          <div style={{ fontSize: 16, fontWeight: 700, marginTop: 2 }}>
            {PALIER_NAMES[level]}
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ color: style.text, fontWeight: 700, fontSize: 14 }}>
            {style.label}
          </div>
          {validatedAt && (
            <div
              style={{ fontSize: 11, color: "#4ade80", marginTop: 3, fontFamily: "monospace" }}
              title="Heure de première validation"
            >
              ✓ {validatedAt}
            </div>
          )}
          {!validatedAt && result && result.duration_ms > 0 && (
            <div style={{ fontSize: 11, color: "#555", marginTop: 2 }}>
              {result.duration_ms}ms
            </div>
          )}
        </div>
      </div>

      {/* Fixtures échouées */}
      {failedFixtures.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {failedFixtures.map((f, i) => {
            const contextHint = getContextualHint(level, f.message);
            const hasDiff = (f.expected !== null || f.got !== null) && f.message.includes("mismatch");
            return (
              <div
                key={i}
                style={{
                  background: "#1a0a0a",
                  borderRadius: 6,
                  padding: "8px 10px",
                  fontSize: 12,
                  fontFamily: "monospace",
                }}
              >
                <div style={{ color: "#f87171" }}>✗ {f.fixture}</div>
                {f.message && f.message !== "FAIL" && !f.message.includes("Final book mismatch") && (
                  <div
                    style={{
                      color: "#fbbf24",
                      marginTop: 4,
                      whiteSpace: "pre-wrap",
                      wordBreak: "break-all",
                      lineHeight: 1.4,
                      maxHeight: 80,
                      overflow: "hidden",
                    }}
                    title={f.message}
                  >
                    {f.message.length > 220 ? f.message.slice(0, 220) + "…" : f.message}
                  </div>
                )}
                {/* Contextual error hint */}
                {contextHint && (
                  <div
                    style={{
                      color: "#a78bfa",
                      marginTop: 6,
                      fontSize: 12,
                      fontFamily: "sans-serif",
                      lineHeight: 1.5,
                      borderLeft: "2px solid #7c3aed",
                      paddingLeft: 8,
                    }}
                  >
                    💡 {contextHint}
                  </div>
                )}
                {/* Book diff */}
                {hasDiff && (
                  <div
                    style={{
                      marginTop: 8,
                      padding: "8px 10px",
                      background: "#0d1117",
                      borderRadius: 4,
                      border: "1px solid #1a1f2b",
                    }}
                  >
                    <BookDiff expected={f.expected} got={f.got} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Bouton indices */}
      <button
        onClick={() => setShowHints((v) => !v)}
        style={{
          background: "none",
          border: "1px solid #2d2d44",
          borderRadius: 6,
          color: "#6b7280",
          cursor: "pointer",
          padding: "5px 10px",
          fontSize: 12,
          textAlign: "left",
          transition: "border-color 0.15s, color 0.15s",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = "#555";
          e.currentTarget.style.color = "#aaa";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = "#2d2d44";
          e.currentTarget.style.color = "#6b7280";
        }}
      >
        {showHints ? "▲ Masquer les indices" : "▼ Voir les indices"}
      </button>

      {/* Contenu des indices */}
      {showHints && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div
            style={{
              background: "#0d1117",
              borderRadius: 6,
              padding: "8px 12px",
              fontFamily: "monospace",
              fontSize: 12,
              color: "#7dd3fc",
              border: "1px solid #1e3a5f",
            }}
          >
            <div style={{ color: "#555", marginBottom: 4, fontFamily: "sans-serif" }}>
              Champs utiles :
            </div>
            {(FIELDS[level] ?? []).map((f, i) => (
              <div key={i}>• {f}</div>
            ))}
          </div>

          {(HINTS[level] ?? []).map((hint, i) => (
            <div
              key={i}
              style={{
                background: "#110d1f",
                borderRadius: 6,
                padding: "8px 12px",
                fontSize: 13,
                color: "#c4b5fd",
                borderLeft: "3px solid #7c3aed",
                lineHeight: 1.5,
              }}
            >
              💡 {hint}
            </div>
          ))}

          {PITFALLS[level] && (
            <div
              style={{
                background: "#1a1200",
                borderRadius: 6,
                padding: "8px 12px",
                fontSize: 13,
                color: "#fde68a",
                borderLeft: "3px solid #d97706",
                lineHeight: 1.5,
              }}
            >
              ⚠ {PITFALLS[level]}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
