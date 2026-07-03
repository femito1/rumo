// frontend/src/features/closing/WorkspacePage.tsx
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiFetch } from "../../lib/api";
import { useClosing } from "./useClosing";
import { MonthPicker } from "./MonthPicker";
import { DayRangeFilter } from "./DayRangeFilter";
import { ExportMenu } from "./ExportMenu";
import { KpiCard } from "../../components/KpiCard";
import { Skeleton } from "../../components/Skeleton";
import { Loader } from "../../components/Loader";
import { TabView } from "./TabView";
import { BudgetEditor } from "./BudgetEditor";
import { ManualActualsEditor } from "./ManualActualsEditor";
import { daysInMonth } from "../../lib/format";
import { exportAllSheets, exportSingleSheet } from "../../lib/exportClosing";

export function WorkspacePage() {
  const { id = "" } = useParams();
  const [months, setMonths] = useState<string[]>([]);
  const [month, setMonth] = useState<string>("");
  const [from, setFrom] = useState<number | null>(null);
  const [to, setTo] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<string>("");

  useEffect(() => {
    apiFetch<{ available_months: string[] }>(`/api/clients/${id}`).then((c) => {
      setMonths(c.available_months);
      setMonth(c.available_months[0] ?? "");
    });
  }, [id]);

  const { data, error, loading } = useClosing(id, month, from, to);
  if (data && !activeTab && data.tab_order[0]) {
    // Default to the first tab once data loads; render-phase update avoids
    // a setState-in-effect cascade and applies before paint.
    setActiveTab(data.tab_order[0]);
  }

  if (!month) return <div className="workspace"><Skeleton rows={6} /></div>;

  return (
    <div className="workspace">
      <header className="workspace-top">
        <div className="workspace-heading">
          <span className="workspace-eyebrow">Fechamento mensal</span>
          <h1>{data?.client.name ?? ""}</h1>
        </div>
        <div className="workspace-toolbar">
          <MonthPicker value={month} availableMonths={months} onChange={(m) => { setMonth(m); setFrom(null); setTo(null); }} />
          <div className="toolbar-actions">
            <DayRangeFilter from={from} to={to} maxDay={daysInMonth(month)} busy={loading} onApply={(f, t) => { setFrom(f); setTo(t); }} onClear={() => { setFrom(null); setTo(null); }} />
            <BudgetEditor clientId={id} ano={Number(month.slice(0, 4))} />
            <ManualActualsEditor clientId={id} anoMes={month} />
            <div className="toolbar-divider" aria-hidden="true" />
            <ExportMenu
              disabled={!data || loading}
              pageEnabled={!!activeTab}
              onExportAll={() => data && exportAllSheets(data)}
              onExportPage={() => data && activeTab && exportSingleSheet(data, activeTab)}
            />
          </div>
        </div>
      </header>

      {error ? <div className="error-state" role="alert">{error}</div> : null}
      {loading || !data ? (
        <Loader />
      ) : (
        <>
          {!data.day_range.is_full_month ? <div className="filter-chip">Filtrado por dia · KPIs referem-se ao mês completo</div> : null}

          <section className="kpis kpis-hero">
            <KpiCard label="Receita de honorários" value={data.kpis.receita_honorarios ?? null} hero />
            <KpiCard label="Faturamento realizado" value={data.kpis.faturamento_realizado ?? null} hero />
            <KpiCard label="Resultado líquido" value={data.kpis.resultado_liquido ?? null} hero signed />
            <KpiCard label="Margem líquida" value={data.kpis.margem_liquida ?? null} hero signed format="percent" />
          </section>

          <section className="kpis kpis-secondary">
            <KpiCard label="Resultado bruto" value={data.kpis.resultado_bruto ?? null} signed />
            <KpiCard label="Margem bruta" value={data.kpis.margem_bruta ?? null} signed format="percent" />
            <KpiCard label="Reserva de bônus" value={data.kpis.reserva_bonus ?? null} />
            <KpiCard label="Faturas emitidas" value={data.kpis.faturas_emitidas ?? null} format="number" />
          </section>

          <nav className="tab-rail">
            {data.tab_order.map((t) => (
              <button key={t} className={t === activeTab ? "active" : ""} onClick={() => setActiveTab(t)}>
                {(data.tabs[t] as { name?: string })?.name ?? t}
              </button>
            ))}
          </nav>
          <section className="tab-content"><TabView tab={data.tabs[activeTab]} /></section>
        </>
      )}
    </div>
  );
}
