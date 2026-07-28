// frontend/src/features/closing/PresentationPanel.tsx
import { KpiCard } from "../../components/KpiCard";
import { formatBRL, formatPercent } from "../../lib/format";
import type { Presentation } from "../../lib/types";

/**
 * Client-facing presentation panel — an in-app mirror of Rumo's monthly PPTX.
 * Built entirely from the server-assembled ``presentation`` payload (no detail
 * tabs). A CLIENT sees only this; an ADMIN can preview + export it to PDF.
 *
 * The root carries ``id="presentation-root"`` so the PDF export can target it,
 * and ``data-pdf-page`` marks each slide as a page break for the exporter.
 */
export function PresentationPanel({ data }: { data: Presentation }) {
  const h = data.headline;
  return (
    <div className="presentation" id="presentation-root">
      <section className="pres-slide" data-pdf-page>
        <header className="pres-head">
          <span className="pres-eyebrow">Resultado Institucional</span>
          <h2>{data.titulo}</h2>
          <span className="pres-period">{data.periodo}</span>
        </header>
        <div className="kpis kpis-hero">
          <KpiCard label="Faturamento" value={h.faturamento} hero />
          <KpiCard label="Receita líquida" value={h.recebimento} hero />
          <KpiCard label="Resultado bruto" value={h.resultado_bruto} hero signed />
          <KpiCard label="Resultado líquido" value={h.resultado_liquido} hero signed />
        </div>
        <div className="kpis kpis-secondary">
          <KpiCard label="Margem bruta" value={h.margem_bruta} signed format="percent" />
          <KpiCard label="Margem líquida" value={h.margem_liquida} signed format="percent" />
          <KpiCard label="Reserva de bônus" value={h.reserva_bonus} signed />
        </div>
      </section>

      <section className="pres-slide" data-pdf-page>
        <header className="pres-head">
          <span className="pres-eyebrow">Resultado por área</span>
          <h2>Áreas — {data.periodo}</h2>
        </header>
        <div className="pres-area-cards">
          {data.areas.map((a) => (
            <div key={a.key} className="pres-area-card">
              <h3>{a.label}</h3>
              <dl>
                <div><dt>Receita</dt><dd className="num">{formatBRL(a.receita)}</dd></div>
                <div><dt>Res. bruto</dt><dd className={`num ${sign(a.resultado_bruto)}`}>{formatBRL(a.resultado_bruto)}</dd></div>
                <div><dt>Res. líquido</dt><dd className={`num ${sign(a.resultado_liquido)}`}>{formatBRL(a.resultado_liquido)}</dd></div>
                <div><dt>Reserva bônus</dt><dd className={`num ${sign(a.reserva_bonus)}`}>{formatBRL(a.reserva_bonus)}</dd></div>
                <div><dt>Atingimento</dt><dd className="num">{formatPercent(a.atingimento)}</dd></div>
              </dl>
            </div>
          ))}
        </div>
      </section>

      <section className="pres-slide" data-pdf-page>
        <header className="pres-head">
          <span className="pres-eyebrow">Recebimento mensal</span>
          <h2>Evolução no ano</h2>
          {data.meta_anual != null ? (
            <span className="pres-period">Meta anual {formatBRL(data.meta_anual)}</span>
          ) : null}
        </header>
        <table className="grid-table pres-table">
          <thead>
            <tr><th>Mês</th><th className="num">Recebimento</th></tr>
          </thead>
          <tbody>
            {data.recebimento_mensal.map((m, i) => (
              <tr key={i}>
                <td>{m.mes}</td>
                <td className="num">{formatBRL(m.recebimento)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function sign(v: number | null): string {
  if (v == null) return "";
  return v < 0 ? "kpi-neg" : "kpi-pos";
}
