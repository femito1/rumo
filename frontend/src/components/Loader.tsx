// frontend/src/components/Loader.tsx
import { useEffect, useState } from "react";

const MESSAGES = [
  "Conciliando os números sagrados…",
  "Somando recebimentos por área…",
  "Rateando o custo de equipe…",
  "Montando o Institucional…",
  "Fechando a margem líquida…",
];

/**
 * Big, centered, animated loader. Three orbiting bodies (green/blue/purple)
 * circle a breathing core while a coin-flip glints — a playful nod to a
 * financial close. Messages rotate so long fetches feel alive.
 */
export function Loader({ label }: { label?: string }) {
  const [msg, setMsg] = useState(0);
  useEffect(() => {
    if (label) return; // caller-provided label is static
    const id = setInterval(() => setMsg((m) => (m + 1) % MESSAGES.length), 1800);
    return () => clearInterval(id);
  }, [label]);

  return (
    <div className="loader" role="status" aria-live="polite" aria-busy="true">
      <div className="loader-stage">
        <div className="loader-orbit loader-orbit-1">
          <span className="loader-body" style={{ background: "var(--api)" }} />
        </div>
        <div className="loader-orbit loader-orbit-2">
          <span className="loader-body" style={{ background: "var(--formula)" }} />
        </div>
        <div className="loader-orbit loader-orbit-3">
          <span className="loader-body" style={{ background: "var(--juritis)" }} />
        </div>
        <div className="loader-core">
          <span className="loader-coin">R$</span>
        </div>
      </div>
      <p className="loader-msg">{label ?? MESSAGES[msg]}</p>
    </div>
  );
}
