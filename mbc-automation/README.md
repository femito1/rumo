# MBC — Automação do Fechamento Mensal (v0)

Automação do fechamento mensal do escritório MBC. Reproduz, o mais próximo de
**1:1** possível, a planilha `Copy of Fechamento MBC 02.2026.xlsx`, puxando o
**lado da receita** ao vivo da API Juritis LegalDesk. Mês alvo do v0:
**Maio de 2026** (`AnoMes = 2026-05`) — o último mês fechado.

> Contexto e validação completos em `../docs/AUTOMATION_BUILD_GUIDE.md` e
> `../docs/AUTOMATION_FINDINGS_PTBR.md`.

## Cobertura — todas as 15 abas são espelhadas (1:1)

O dashboard renderiza **as 15 abas** do workbook. As 4 abas com dado de receita
trazem valores **ao vivo da API** para o mês alvo (renderização "rica"); as
demais 11 são espelhadas como **grade de referência 1:1** (layout + valores do
workbook), com cada célula marcada por origem.

| Aba | Renderização | Origem |
| --- | --- | --- |
| `Meta` (Recebimento + Faturamento) | rica · ✅ API ao vivo | Recebimento/Faturamento Bruto |
| `Base_Resultado` (linha 4 ao vivo) | rica · ✅ API + ⛔ manual + ⚙️ fórmula | Recebimento Bruto + TOTVS Backoffice |
| `Resumo Recebidas` | rica · ✅ API ao vivo | `RateioFaturaProfissionalViews` |
| `Faturas Centro Custo` | rica · ✅ API ao vivo | `FaturaViews` + `RateioFaturaCasoViews` |
| `Areas Sintetico atualizado` | grade · receita ✅ API / quebra ⚙️ | detalhamento por área |
| `DRE 2026` | grade · ⚙️ fórmula | depende de Orçamento (sem API) |
| `Orçamento 2026` | grade · ⛔ manual | montado à mão (API só tem 2025) |
| `Institucional` / `Institucional ano` | grade · ⚙️ fórmula | consolidado |
| `Contencioso` / `Econômico` / `Arbitragem` | grade · ⚙️ fórmula | Orçado × Realizado por área |
| `Rateio Mensal` | grade · ⚙️ fórmula | rateio por área (Fase 2) |
| `Fluxo consolidado` | grade · ⚙️ fórmula | fluxo por área/mês |
| `Amortização` | grade · ⛔ manual | cronograma fixo (parcelas) |

Badges nas células: **API** (verde, valor ao vivo) · **FÓRM** (azul, célula de
fórmula, mostra o valor avaliado do workbook) · **MANUAL** (cinza, TOTVS sem
API) · **REF** (cinza, valor literal de referência do workbook — Jan/Fev).

Números de Maio/2026 conferidos contra a API ao vivo:

- Receita de honorários: **R$ 415.927,84** (98 lançamentos)
- Faturamento Realizado: **R$ 719.988,05** (97 lançamentos)
- Faturas emitidas: **53**

## Arquitetura

```
mbc-automation/
├── backend/                 # Python: puxa a API e gera o data.json
│   ├── mbc_automation/
│   │   ├── config.py            # credenciais via env (nunca no browser)
│   │   ├── api_client.py        # cliente OData v3 + primitivas verificadas
│   │   ├── period.py            # helpers de competência (AnoMes, datas, coluna)
│   │   ├── builder.py           # monta o payload espelhando as 15 abas
│   │   ├── base_resultado_layout.py  # layout 1:1 da Base_Resultado (auto-gerado)
│   │   ├── tab_layouts.py       # grade 1:1 das 15 abas (auto-gerado dos TSVs)
│   │   └── cli.py               # `python -m mbc_automation.cli`
│   ├── scripts/
│   │   ├── gen_base_resultado_layout.py  # regenera o layout da Base_Resultado
│   │   ├── gen_tab_layouts.py            # regenera a grade das 15 abas
│   │   └── build_and_serve.py            # build + servidor estático
│   └── requirements.txt
├── frontend/                # Dashboard estático (HTML/CSS/JS, sem build)
│   ├── index.html
│   ├── styles.css
│   ├── app.js               # carrega data.json e renderiza as abas
│   └── data.json            # gerado pelo backend
└── data/data.json           # cópia canônica do payload gerado
```

**Padrão:** o backend chama a API (Basic auth fica no servidor) → gera um
`data.json` → o frontend só renderiza. A senha **nunca** vai para o browser.

## Como rodar

Pré-requisito: o virtualenv do repositório em `../.venv` (já tem `requests`),
ou instale `backend/requirements.txt`.

Build + servidor em um passo:

```bash
../.venv/bin/python backend/scripts/build_and_serve.py --month 2026-05
# abre em http://localhost:8765/
```

Ou separadamente:

```bash
# 1) gerar o data.json (com verificação dos totais conhecidos)
cd backend
../../.venv/bin/python -m mbc_automation.cli --month 2026-05 --out ../data/data.json --check
cp ../data/data.json ../frontend/data.json

# 2) servir o frontend
cd ../frontend
../../.venv/bin/python -m http.server 8765
```

Credenciais sobrescrevíveis por env: `MBC_API_USER`, `MBC_API_PASSWORD`,
`MBC_API_BASE`.

## Verificações de sanidade

`--check` afirma os totais conhecidos (`cli.py: SANITY_CHECKS`):

- `recebimento('2026-05')` ≈ 415.927,84
- `faturamento('2026-05')` ≈ 719.988,05
- 53 faturas distintas no mês
- históricos: jan/2026 = 279.821,07 · fev/2026 = 319.233,58

## Caminho para produção (próximos passos)

1. **Fase 2 — despesas institucionais:** as ~170 linhas manuais vivem nos
   módulos TOTVS Backoffice (Financeiro/RH/Tributário). Depende de liberação
   de credenciais. Quando vierem, plugar novos clients no `builder.py`.
2. **Persistência + histórico:** hoje o `data.json` é por-mês; evoluir para um
   pequeno serviço/DB que guarda cada fechamento.
3. **Inputs manuais na UI:** permitir digitar as linhas manuais e recalcular as
   fórmulas (margens, totais) no próprio dashboard.
4. **Export para .xlsx:** gerar de volta o workbook preservando fórmulas
   (openpyxl) para quem ainda usa o Excel.
