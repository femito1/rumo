// frontend/src/features/closing/PresentationPanel.tsx
import { formatBRL, formatBRLShort, formatPercent, formatPercentSigned } from "../../lib/format";
import type {
  Presentation,
  PresAttainment,
  PresLine,
  PresMatrixRow,
} from "../../lib/types";

/**
 * Client-facing presentation deck — an in-app, dynamic mirror of Rumo's monthly
 * PPTX (reference/workbook/MBC Resultado Jan a Mai 2026.pdf), slide by slide.
 * Built entirely from the server-assembled ``presentation`` payload. A CLIENT
 * sees only this; an ADMIN can preview + export it to PDF.
 *
 * ``id="presentation-root"`` is the PDF export target; ``data-pdf-page`` marks
 * each slide as a page break for the exporter (see index.css @media print).
 */
export function PresentationPanel({ data }: { data: Presentation }) {
  return (
    <div className="deck" id="presentation-root">
      <SlideCapa data={data} />
      <SlideIndice />
      <SlideInstitucionalMes data={data} />
      <SlideMeta data={data} />
      <SlideAnalise data={data} />
      {data.areas.map((_, i) => (
        <SlideArea key={data.areas[i].key} data={data} idx={i} />
      ))}
      <SlideReserva data={data} />
    </div>
  );
}

/* ── shared bits ─────────────────────────────────────────────────────────── */

function Slide({ title, sub, children }: { title?: string; sub?: string; children: React.ReactNode }) {
  return (
    <section className="slide" data-pdf-page>
      {title ? (
        <header className="slide-head">
          <span className="slide-mark" aria-hidden="true" />
          <div>
            <h2>{title}</h2>
            {sub ? <p className="slide-sub">{sub}</p> : null}
          </div>
          <span className="slide-brand">RUMO</span>
        </header>
      ) : null}
      {children}
      <footer className="slide-foot">
        <span>Marchini Botelho Caselta · Relatório de Resultados</span>
      </footer>
    </section>
  );
}

/** A KPI card in the slide style: label, big value, orçado/meta footnote. */
function StatCard({ label, value, foot, sign }: { label: string; value: string; foot?: string; sign?: number | null }) {
  const tone = sign == null ? "" : sign < 0 ? " val-neg" : " val-pos";
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className={`stat-value num${tone}`}>{value}</div>
      {foot ? <div className="stat-foot">{foot}</div> : null}
    </div>
  );
}

function money(v: number | null) {
  return v == null ? "—" : formatBRL(v);
}
function short(v: number | null) {
  return v == null ? "—" : formatBRLShort(v);
}
function signClass(v: number | null): string {
  if (v == null || v === 0) return "";
  return v < 0 ? "val-neg" : "val-pos";
}

/* ── slide 1: capa ───────────────────────────────────────────────────────── */

function SlideCapa({ data }: { data: Presentation }) {
  return (
    <section className="slide slide-capa" data-pdf-page>
      <div className="capa-brands">
        <span className="capa-rumo">RUMO</span>
        <span className="capa-div" />
        <span className="capa-client">{data.titulo}</span>
      </div>
      <div className="capa-title">
        <span className="capa-eyebrow">MARCHINI BOTELHO CASELTA</span>
        <h1>Relatório de Resultados</h1>
        <p className="capa-period">Janeiro – {data.periodo_mes} {data.ano}</p>
      </div>
      <div className="capa-band">
        Resultado Mensal de {data.periodo_mes}&nbsp;&nbsp;|&nbsp;&nbsp;YTD Jan–{data.periodo_mes}
        &nbsp;&nbsp;|&nbsp;&nbsp;Orçado vs. Realizado
      </div>
      <p className="capa-by">Elaborado por Rumo Gestão de Negócios</p>
    </section>
  );
}

/* ── slide 2: índice ─────────────────────────────────────────────────────── */

const INDICE: { n: string; t: string; d: string }[] = [
  { n: "01", t: "Resultado Institucional – Mês", d: "Visão mensal com custos e reserva de bônus" },
  { n: "02", t: "Institucional – YTD vs. Meta", d: "Receita acumulada vs. meta com atingimento mensal" },
  { n: "03", t: "Análise YTD – Orçado vs. Realizado", d: "Todas as linhas com Variação R$ e Var% sinalizados" },
  { n: "04", t: "Contencioso – Mês e YTD + DRE", d: "Resultado mensal, metas e DRE com variações" },
  { n: "05", t: "Econômico – Mês e YTD + DRE", d: "Resultado mensal, metas e DRE com variações" },
  { n: "06", t: "Arbitragem & Compliance – Mês e YTD + DRE", d: "Resultado mensal, metas e DRE com variações" },
  { n: "07", t: "Reserva de Bônus | Resumo", d: "Consolidado YTD e visão por área" },
];

function SlideIndice() {
  return (
    <Slide title="Índice da Apresentação">
      <div className="indice-grid">
        {INDICE.map((it) => (
          <div key={it.n} className="indice-item">
            <span className="indice-n">{it.n}</span>
            <div>
              <div className="indice-t">{it.t}</div>
              <div className="indice-d">{it.d}</div>
            </div>
          </div>
        ))}
      </div>
    </Slide>
  );
}

/* ── slide 3: institucional mês ──────────────────────────────────────────── */

function SlideInstitucionalMes({ data }: { data: Presentation }) {
  const h = data.headline;
  const det = data.institucional_detalhe;
  const isPct = (key: string) => key.startsWith("margem");
  return (
    <Slide title={`Resultado Institucional – ${data.periodo_mes} ${data.ano}`}>
      <div className="stat-row">
        <StatCard label="Faturamento" value={money(h.faturamento)} foot="notas emitidas" />
        <StatCard label="Receita Líquida" value={money(h.recebimento)} foot="recebido" />
        <StatCard label="Resultado Bruto" value={money(h.resultado_bruto)} sign={h.resultado_bruto} foot={h.margem_bruta != null ? `Margem ${formatPercent(h.margem_bruta)}` : undefined} />
        <StatCard label="Resultado Líquido" value={money(h.resultado_liquido)} sign={h.resultado_liquido} foot={h.margem_liquida != null ? `Mg. Líq. ${formatPercent(h.margem_liquida)}` : undefined} />
      </div>
      <h3 className="slide-caption">Detalhe Mensal – Resultado Institucional</h3>
      <table className="deck-table">
        <thead>
          <tr>
            <th>Indicador</th>
            {det.meses.map((m) => <th key={m} className="num">{m}</th>)}
            <th className="num">YTD</th>
          </tr>
        </thead>
        <tbody>
          {det.linhas.map((row) => (
            <tr key={row.key}>
              <td>{row.label}</td>
              {det.month_indices.map((mi) => {
                const v = row.months[String(mi)] ?? row.months[mi as unknown as string] ?? null;
                return (
                  <td key={mi} className={`num ${isPct(row.key) ? "" : signClass(v)}`}>
                    {v == null ? "—" : isPct(row.key) ? formatPercent(v) : short(v)}
                  </td>
                );
              })}
              <td className={`num col-ytd ${isPct(row.key) ? "" : signClass(row.ytd)}`}>
                {row.ytd == null ? "—" : isPct(row.key) ? formatPercent(row.ytd) : short(row.ytd)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Slide>
  );
}

/* ── slide 4: YTD vs Meta ────────────────────────────────────────────────── */

function SlideMeta({ data }: { data: Presentation }) {
  const m = data.meta;
  return (
    <Slide title={`Resultado Institucional – YTD Jan–${data.periodo_mes} vs. Meta`}>
      <div className="stat-row">
        <StatCard label="Receita YTD" value={money(m.receita_ytd)} sign={m.receita_ytd} foot={m.anual != null ? `Meta: ${formatBRL(m.anual)}` : undefined} />
        <StatCard label="Resultado Bruto YTD" value={money(m.resultado_bruto_ytd)} sign={m.resultado_bruto_ytd} />
        <StatCard label="Resultado Líquido YTD" value={money(m.resultado_liquido_ytd)} sign={m.resultado_liquido_ytd} />
        <StatCard label="Margem Líquida YTD" value={m.margem_liquida_ytd == null ? "—" : formatPercent(m.margem_liquida_ytd)} sign={m.margem_liquida_ytd} />
      </div>
      <h3 className="slide-caption">Atingimento da Meta – Receita (mês a mês)</h3>
      <AttainmentBars rows={m.atingimento} />
    </Slide>
  );
}

/** Horizontal attainment bars (PDF p.4/6/8/10): pct-filled bar + gap label. */
function AttainmentBars({ rows }: { rows: PresAttainment[] }) {
  return (
    <div className="att-list">
      {rows.map((r) => {
        const pct = r.pct ?? 0;
        const width = Math.max(0, Math.min(1, pct)) * 100;
        const over = pct >= 1;
        return (
          <div key={r.abbr} className="att-row">
            <span className="att-mes">{r.mes ?? r.abbr}</span>
            <span className="att-pct">{r.pct == null ? "—" : formatPercent(r.pct)}</span>
            <span className="att-track">
              <span className={`att-fill${over ? " att-fill-over" : ""}`} style={{ width: `${width}%` }} />
            </span>
            <span className={`att-gap ${signClass(r.gap)}`}>
              {r.gap == null ? "" : `Gap: ${formatBRLShort(r.gap)}`}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/* ── slide 5: análise YTD ────────────────────────────────────────────────── */

function StatusDot({ status }: { status: PresLine["status"] }) {
  if (!status) return null;
  return <span className={`dot dot-${status}`} aria-label={status} />;
}

function ComparisonTable({ lines }: { lines: PresLine[] }) {
  return (
    <table className="deck-table deck-table-analysis">
      <thead>
        <tr>
          <th>Descrição</th>
          <th className="num">Orçado YTD</th>
          <th className="num">Realizado YTD</th>
          <th className="num">Variação R$</th>
          <th className="num">Var%</th>
          <th />
        </tr>
      </thead>
      <tbody>
        {lines.map((l) => {
          const isResult = l.key === "resultado_bruto" || l.key === "resultado_liquido" || l.key === "recebimento";
          return (
            <tr key={l.key} className={isResult ? "deck-row-strong" : ""}>
              <td>{l.label}</td>
              <td className="num">{short(l.orcado)}</td>
              <td className={`num ${signClass(l.realizado)}`}>{short(l.realizado)}</td>
              <td className={`num ${signClass(l.delta)}`}>{l.delta == null ? "—" : (l.delta > 0 ? "+" : "") + formatBRLShort(l.delta)}</td>
              <td className={`num ${signClass(l.pct)}`}>{l.pct == null ? "—" : formatPercentSigned(l.pct)}</td>
              <td className="dot-cell"><StatusDot status={l.status} /></td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function SlideAnalise({ data }: { data: Presentation }) {
  return (
    <Slide title={`Análise YTD Jan–${data.periodo_mes} ${data.ano} — Orçado vs. Realizado`}>
      <ComparisonTable lines={data.analise_ytd} />
      <Legend />
    </Slide>
  );
}

function Legend() {
  return (
    <div className="deck-legend">
      <span><span className="dot dot-critico" /> Desvio crítico</span>
      <span><span className="dot dot-atencao" /> Atenção</span>
      <span><span className="dot dot-ok" /> Economia / acima da meta</span>
    </div>
  );
}

/* ── slides 6-8: por área ────────────────────────────────────────────────── */

function SlideArea({ data, idx }: { data: Presentation; idx: number }) {
  const a = data.areas[idx];
  return (
    <Slide title={`${a.label} – ${data.periodo_mes} ${data.ano} e YTD`}>
      <div className="area-split">
        <div>
          <h3 className="slide-caption">{data.periodo_mes} {data.ano}</h3>
          <div className="stat-row stat-row-3">
            <StatCard label="Receita" value={money(a.mes.receita)} sign={a.mes.receita} foot={a.mes.meta_receita != null ? `Meta: ${formatBRL(a.mes.meta_receita)}` : undefined} />
            <StatCard label="Res. Bruto" value={money(a.mes.resultado_bruto)} sign={a.mes.resultado_bruto} />
            <StatCard label="Res. Líquido" value={money(a.mes.resultado_liquido)} sign={a.mes.resultado_liquido} />
          </div>
          <h3 className="slide-caption">Atingimento da Meta – Receita</h3>
          <AttainmentBars rows={a.atingimento} />
        </div>
        <div>
          <h3 className="slide-caption">DRE YTD Jan–{data.periodo_mes}</h3>
          <ComparisonTable lines={a.dre} />
        </div>
      </div>
    </Slide>
  );
}

/* ── final slide: reserva de bônus matrix ────────────────────────────────── */

function SlideReserva({ data }: { data: Presentation }) {
  const r = data.reserva;
  return (
    <Slide title={`Reserva de Bônus – Consolidado YTD Jan–${data.periodo_mes} ${data.ano}`}
           sub="Constituída mensalmente sobre o resultado líquido de cada área. Positivo = acúmulo; Negativo = consumo.">
      <table className="deck-table">
        <thead>
          <tr>
            <th>Área</th>
            {r.meses.map((m) => <th key={m} className="num">{m}</th>)}
            <th className="num">YTD Acumulado</th>
          </tr>
        </thead>
        <tbody>
          {r.linhas.map((row: PresMatrixRow) => (
            <tr key={row.key}>
              <td>{row.label}</td>
              {r.meses.map((_, i) => {
                const v = valueForMonth(row, data.institucional_detalhe.month_indices[i]);
                return <td key={i} className={`num ${signClass(v)}`}>{v == null ? "—" : short(v)}</td>;
              })}
              <td className={`num col-ytd ${signClass(row.ytd)}`}>{short(row.ytd)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Slide>
  );
}

function valueForMonth(row: PresMatrixRow, monthIndex: number): number | null {
  return row.months[String(monthIndex)] ?? row.months[monthIndex as unknown as string] ?? null;
}
