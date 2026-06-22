// frontend/src/features/closing/WorkspacePage.tsx
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiFetch } from "../../lib/api";
import { useClosing } from "./useClosing";
import { MonthPicker } from "./MonthPicker";
import { DayRangeFilter } from "./DayRangeFilter";
import { KpiCard } from "../../components/KpiCard";
import { Skeleton } from "../../components/Skeleton";
import { TabView } from "./TabView";

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
        <h1>Fechamento — {data?.client.name ?? ""}</h1>
        <div className="filters">
          <MonthPicker value={month} availableMonths={months} onChange={(m) => { setMonth(m); setFrom(null); setTo(null); }} />
          <DayRangeFilter from={from} to={to} onChange={(f, t) => { setFrom(f); setTo(t); }} onClear={() => { setFrom(null); setTo(null); }} />
        </div>
      </header>

      {error ? <div className="error-state" role="alert">{error}</div> : null}
      {loading || !data ? <Skeleton rows={6} /> : (
        <>
          <section className="kpis">
            <KpiCard label="Receita de honorários" value={data.kpis.receita_honorarios ?? null} highlight />
            <KpiCard label="Faturamento Realizado" value={data.kpis.faturamento_realizado ?? null} highlight />
            <KpiCard label="Faturas emitidas" value={data.kpis.faturas_emitidas ?? null} />
          </section>
          {!data.day_range.is_full_month ? <div className="filter-chip">Filtrado por dia · KPIs referem-se ao mês completo</div> : null}
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
