// frontend/src/features/closing/NotesPanel.tsx
import { useState } from "react";
import type { ClosingNote } from "../../lib/types";

/**
 * "Diferenças conhecidas" — the month's explained discrepancies, in PT-BR.
 *
 * The client kept asking the same handful of "why doesn't this match our
 * spreadsheet?" questions in meetings. Each answer now lives next to the closing
 * it concerns, with a mailto that pre-fills client + month + note id so a reply
 * arrives with enough context to act on.
 *
 * Collapsed by default and rendered as nothing when the month is clean: a month
 * with no known differences must not grow an empty box, and the notes must never
 * push the numbers below the fold.
 */
export function NotesPanel({ notas, mes, cliente }:
  { notas: ClosingNote[]; mes: string; cliente: string }) {
  const [aberta, setAberta] = useState<string | null>(null);
  if (!notas.length) return null;

  return (
    <section className="notas-panel" aria-label="Diferenças conhecidas">
      <header className="notas-head">
        <span className="notas-title">Diferenças conhecidas</span>
        <span className="notas-count">{notas.length}</span>
        <span className="notas-hint">
          já verificadas — clique para entender cada uma
        </span>
      </header>
      <ul className="notas-list">
        {notas.map((n) => {
          const open = aberta === n.id;
          return (
            <li key={n.id} className={`nota nota-${n.severidade}`}>
              <button
                type="button"
                className="nota-toggle"
                aria-expanded={open}
                onClick={() => setAberta(open ? null : n.id)}
              >
                <span className="nota-marker" aria-hidden="true" />
                <span className="nota-titulo">{n.titulo}</span>
                <span className="nota-chevron" aria-hidden="true">{open ? "−" : "+"}</span>
              </button>
              {open ? (
                <div className="nota-corpo">
                  <p className="nota-detalhe">{n.detalhe}</p>
                  {n.acao ? (
                    <p className="nota-acao"><strong>O que fazer:</strong> {n.acao}</p>
                  ) : null}
                  <a className="nota-contato" href={mailto(n, mes, cliente)}>
                    Falar com o time sobre esta diferença
                  </a>
                </div>
              ) : null}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

/**
 * Pre-fill the email so a question arrives answerable. The note `id` is included
 * deliberately: it is the only stable handle back to the registry entry, and it
 * survives the client paraphrasing the title.
 */
function mailto(n: ClosingNote, mes: string, cliente: string): string {
  // `contato` is "Nome — email@dominio"; take the address if one is present.
  const email = n.contato.match(/[\w.+-]+@[\w.-]+\.\w+/)?.[0] ?? "";
  const subject = `[${cliente} · ${mes}] Dúvida: ${n.titulo}`;
  const body = [
    `Cliente: ${cliente}`,
    `Competência: ${mes}`,
    `Nota: ${n.id}`,
    "",
    "Minha dúvida:",
    "",
  ].join("\n");
  return `mailto:${email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}
