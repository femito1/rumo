"use strict";

const BRL = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function money(v) {
  if (v === null || v === undefined) return "";
  return BRL.format(v);
}

function badge(source) {
  const map = { api: ["badge-api", "API"], formula: ["badge-formula", "FÓRMULA"], manual: ["badge-manual", "MANUAL"] };
  const [cls, label] = map[source] || map.manual;
  return `<span class="badge ${cls}">${label}</span>`;
}

function cell(c) {
  if (!c || c.value === null || c.value === undefined) {
    return `<span class="empty-cell">— ${badge(c ? c.source : "manual")}</span>`;
  }
  return `<span class="num">${money(c.value)} ${badge(c.source)}</span>`;
}

let DATA = null;
let activeTab = "meta";

async function load() {
  const res = await fetch("data.json", { cache: "no-store" });
  DATA = await res.json();
  renderShell();
  renderTab(activeTab);
}

function renderShell() {
  const m = DATA.meta;
  document.getElementById("period-title").textContent = `Fechamento — ${m.period_label}`;
  document.getElementById("period-sub").textContent =
    `Competência ${m.period} · coluna ${m.column_letter} da planilha · espelho 1:1 do workbook MBC`;
  const gen = new Date(m.generated_at);
  document.getElementById("generated").textContent = `Gerado em ${gen.toLocaleString("pt-BR")}`;

  const k = DATA.kpis;
  document.getElementById("kpis").innerHTML = `
    <div class="kpi highlight">
      <div class="kpi-label">Receita de honorários</div>
      <div class="kpi-value money">${money(k.receita_honorarios)}</div>
      <div class="kpi-foot">${badge("api")} Recebimento Bruto · ${k.recebimento_rows} lançamentos</div>
    </div>
    <div class="kpi highlight">
      <div class="kpi-label">Faturamento Realizado</div>
      <div class="kpi-value money">${money(k.faturamento_realizado)}</div>
      <div class="kpi-foot">${badge("api")} Faturamento Bruto · ${k.faturamento_rows} lançamentos</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Faturas emitidas</div>
      <div class="kpi-value">${k.faturas_emitidas}</div>
      <div class="kpi-foot">${badge("api")} no mês</div>
    </div>`;

  renderDerived();

  const cov = DATA.coverage;
  const pct = (n) => ((n / cov.total) * 100).toFixed(1) + "%";
  document.getElementById("coverage").innerHTML = `
    <h3>Cobertura da automação — aba Base_Resultado (${cov.total} linhas)</h3>
    <div class="cov-bar">
      <div class="seg-api" style="width:${pct(cov.automated)}" title="API"></div>
      <div class="seg-formula" style="width:${pct(cov.formula)}" title="Fórmula"></div>
      <div class="seg-manual" style="width:${pct(cov.manual)}" title="Manual"></div>
    </div>
    <div class="cov-stats">
      <span><b style="color:var(--api)">${cov.automated}</b> via API</span>
      <span><b style="color:var(--formula)">${cov.formula}</b> fórmula</span>
      <span><b style="color:var(--manual)">${cov.manual}</b> manual (TOTVS Backoffice)</span>
    </div>`;

  const nav = document.getElementById("nav");
  nav.innerHTML = "";
  for (const id of DATA.tab_order) {
    const tab = DATA.tabs[id];
    const isApi = tab.kind === "rich" || tab.has_api || tab.note_source === "api";
    const dot = tab.kind === "rich" ? "dot-api" : isApi ? "dot-api" : "";
    const b = document.createElement("button");
    b.className = id === activeTab ? "active" : "";
    b.innerHTML = `<span class="dot ${dot}" ${dot ? "" : 'style="background:transparent"'}></span>${tab.name}`;
    b.onclick = () => { activeTab = id; renderShell(); renderTab(id); };
    nav.appendChild(b);
  }
}

function renderDerived() {
  let host = document.getElementById("derived");
  if (!host) {
    host = document.createElement("section");
    host.id = "derived";
    host.className = "coverage";
    document.getElementById("coverage").insertAdjacentElement("afterend", host);
  }
  const d = DATA.derived;
  if (!d) { host.innerHTML = ""; return; }
  const imp = d.impostos_estimados || {};
  const pct = (x) => (x * 100).toFixed(2).replace(".", ",") + "%";
  const rows = [
    ["IRPJ", d.tax_rates.irpj, imp.irpj],
    ["CSLL", d.tax_rates.csll, imp.csll],
    ["PIS", d.tax_rates.pis, imp.pis],
    ["COFINS", d.tax_rates.cofins, imp.cofins],
  ].map(([n, r, v]) => `<tr><td>${n}</td><td class="num dim">${pct(r)}</td><td class="num">${money(v)}</td></tr>`).join("");
  host.innerHTML = `
    <h3>Derivados — calculado ao vivo ${badge("formula")}</h3>
    <p class="muted small" style="margin:-4px 0 12px">${d.note}</p>
    <div style="display:flex; gap:32px; flex-wrap:wrap; align-items:flex-start">
      <table style="width:auto; min-width:300px">
        <thead><tr><th>Imposto</th><th class="num">Alíquota</th><th class="num">Estimativa (Fat × alíq.)</th></tr></thead>
        <tbody>${rows}
          <tr class="row-total"><td>Total impostos</td><td></td><td class="num">${money(d.impostos_estimados_total)}</td></tr>
        </tbody>
      </table>
      <div>
        <div class="kpi-label">Resultado bruto sobre faturamento</div>
        <div class="kpi-value money">${money(d.resultado_bruto_sobre_faturamento)}</div>
        <div class="kpi-foot muted">Faturamento ${money(d.faturamento_bruto)} − impostos estimados</div>
      </div>
    </div>`;
}

function renderTab(id) {
  const el = document.getElementById("tab-content");
  const tab = DATA.tabs[id];
  if (tab.kind === "grid") {
    el.innerHTML = `
      <div class="tab-header">
        <h2>${tab.name} ${badge(tab.note_source)}</h2>
        <p class="muted">${tab.note || ""}</p>
      </div>
      ${renderGrid(tab)}`;
    return;
  }
  const renderers = {
    base_resultado: renderBaseResultado,
    meta: renderMeta,
    resumo_recebidas: renderResumo,
    faturas_centro_custo: renderFaturas,
  };
  el.innerHTML = `
    <div class="tab-header">
      <h2>${tab.name}</h2>
      <p class="muted">${tab.description}</p>
    </div>
    ${renderers[id](tab)}`;
}

function gridCell(c) {
  if (!c || c.t === "empty") return "";
  if (c.t === "label") return c.v || "";
  if (c.t === "formula") {
    const txt = c.n !== null && c.n !== undefined ? money(c.n) : "";
    return `<span class="num">${txt} <span class="badge badge-formula">FÓRM</span></span>`;
  }
  if (c.t === "number") {
    return `<span class="num">${money(c.n)} <span class="badge badge-manual">REF</span></span>`;
  }
  return "";
}

function renderGrid(tab) {
  const body = tab.grid.map((row) => {
    const tds = row.map((c, i) => {
      const cls = c && c.t === "label" && i === 0 ? "" : c && (c.t === "number" || c.t === "formula") ? "num" : "";
      return `<td class="${cls}">${gridCell(c)}</td>`;
    }).join("");
    return `<tr>${tds}</tr>`;
  }).join("");
  return `<p class="muted small">${tab.rows} linhas × ${tab.cols} colunas — espelho 1:1 do workbook. <span class="badge badge-manual">REF</span> = valor de referência do workbook (Jan/Fev), <span class="badge badge-formula">FÓRM</span> = célula de fórmula.</p>
    <div class="table-wrap scroll-tall"><table class="grid-table"><tbody>${body}</tbody></table></div>`;
}

function renderBaseResultado(tab) {
  const rows = tab.rows.map((r) => {
    const cls = [r.is_total ? "row-total" : "", `indent-${r.indent}`].join(" ");
    return `<tr class="${cls}">
      <td class="dim">${r.row}</td>
      <td>${r.label}</td>
      <td class="num">${cell({ value: r.value, source: r.source })}</td>
    </tr>`;
  }).join("");
  return `<div class="table-wrap scroll-tall"><table>
    <thead><tr><th style="width:48px">#</th><th>Linha</th><th class="num" style="width:240px">Valor (Maio 2026)</th></tr></thead>
    <tbody>${rows}</tbody></table></div>`;
}

function renderMeta(tab) {
  const rows = tab.rows.map((r) => `<tr>
    <td>${r.label}</td>
    <td class="num">${cell(r.recebimento)}</td>
    <td class="num">${cell(r.faturamento)}</td>
    <td class="num">${cell(r.meta)}</td>
    <td class="num">${cell(r.despesas)}</td>
  </tr>`).join("");
  return `<div class="table-wrap"><table>
    <thead><tr><th>Mês</th><th class="num">Recebimento</th><th class="num">Faturamento</th><th class="num">Meta</th><th class="num">Despesas</th></tr></thead>
    <tbody>${rows}</tbody></table></div>`;
}

function renderResumo(tab) {
  const blocks = tab.invoices.map((inv) => {
    const lawyers = inv.lawyers.map((l) => `<tr class="indent-1">
      <td></td><td>${l.sigla || ""} <span class="dim">${l.nome || ""}</span></td>
      <td class="num">${money(l.valor_trabalhado)}</td>
    </tr>`).join("");
    return `<tr class="invoice-head">
      <td>${inv.fatura}</td>
      <td>${inv.cliente || ""} <span class="dim">· ${inv.caso || ""}</span></td>
      <td class="num">${money(inv.valor_faturado)}</td>
    </tr>${lawyers}`;
  }).join("");
  return `<p class="muted small">${tab.invoice_count} faturas ${badge("api")}</p>
    <div class="table-wrap scroll-tall"><table>
    <thead><tr><th>Fatura / Advogado</th><th>Cliente · Caso</th><th class="num">Valor</th></tr></thead>
    <tbody>${blocks}</tbody></table></div>`;
}

function renderFaturas(tab) {
  const rows = tab.rows.map((f) => `<tr>
    <td>${f.numero}</td>
    <td>${f.razao_social || ""}</td>
    <td class="dim">${f.data_emissao}</td>
    <td class="num">${money(f.valor_honorarios)}</td>
    <td>${f.situacao === "C" ? '<span class="dim">Cancelada</span>' : "Regular"}</td>
    <td>${f.responsavel || ""}</td>
  </tr>`).join("");
  return `<p class="muted small">${tab.fatura_count} faturas ${badge("api")}</p>
    <div class="table-wrap scroll-tall"><table>
    <thead><tr><th>Núm.</th><th>Razão Social</th><th>Emissão</th><th class="num">Valor Hon.</th><th>Situação</th><th>Sócio</th></tr></thead>
    <tbody>${rows}</tbody></table></div>`;
}

load().catch((err) => {
  document.getElementById("tab-content").innerHTML =
    `<p style="color:#ff6b6b">Erro ao carregar data.json: ${err.message}.<br/>Gere o arquivo com o backend e sirva esta pasta via HTTP.</p>`;
});
