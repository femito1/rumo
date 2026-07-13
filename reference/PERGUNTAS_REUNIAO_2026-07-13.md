# Reunião RUMO/MBC — 2026-07-13 (tarde)

## ✅ JÁ BATE AO CENTAVO com o workbook (dados AO VIVO do SISJURI, maio/2026)

- **Custo equipe por área**: Contencioso 74.141,21 · Econômico 79.436,24 ·
  Arbitragem 54.383,94 (Σ 207.961,39)
- **Custos Diretos** (equipe + comissão): 210.089,45
- **Comissão** Econômico 2.128,06 (EHF)
- **Recebimento** 415.927,84 · **Imposto** (15%) 62.389,18 · **Amortização** 8.117
- **Salários Administração** 12.344,91 (com Vale-ADM da transitória 200.010.0010)

Descoberta chave: **"Conta Transitória" é uma CLASSE de contas** (não um hub); o
sistema **desdobra** cada uma via o campo **ORIENTAÇÃO** do lançamento. Vale-ADM
(VR/VT Mensal) veio daí.

---

## ❓ O QUE NÃO ACHAMOS NO DB / DB diverge do workbook — PERGUNTAR

### 1. PROVISÃO DE INFORMÁTICA ⭐ (maior gap: R$14.024 YTD Jan–Mai)
O workbook lança valores **mensais fixos** que o razão (caixa) não tem:
- Suporte Totvs **~2.917,77/mês** (constante)
- Suporte Informática **2.040,00/mês** (constante)
- Licenças de Software: suavizado ~9.786 → 13.700 (amortizado)

No DB os pagamentos Totvs/Juritis/Azure entram "lumpy" (4.504 + 3.108 num mês,
zero noutro). **Pergunta:** vocês provisionam esses contratos por um valor mensal
fixo? Há cronograma/tabela de amortização no sistema, ou é ajuste manual? Quais os
valores mensais?

### 2. AMORTIZAÇÃO (8.117,00/mês)
É cronograma fixo (8 originações 2022 × 60 parcelas)? Muda em 2026? De onde sai?

### 3. BÔNUS EQUIPE (conta 150.000.0000)
Maio veio **zero** no DB. Confirmam que 150.* só posta em fevereiro (~1x/ano)?
Quando os sócios (Ricardo/Aurélio/Daniel/Martim) saem da 150.* p/ conta separada?

### 4. DL EXTRAS (DL excedente sócios / DL excedente MV / Repasse Cacione)
Não achamos regra no DB. De qual conta/lançamento saem, ou são informados
manualmente quando acontecem?

### 5. RECEBIMENTO "NÃO ALOCADOS"
Como tratar a linha "Não Alocados" do Demonstrativo LegalDesk — fica fora das 3
áreas e só entra no total geral?

### 6. ARREDONDAMENTO
O workbook arredonda p/ reais inteiros (415.928 vs 415.927,84 do sistema). É só
apresentação ou há ajuste real?

### 7. ⭐ RELATÓRIO PÓS-DESDOBRAMENTO (o pedido mais valioso)
Existe uma exportação do SISJURI que já mostra o resultado **por conta de despesa
em COMPETÊNCIA (pós-desdobramento/provisão)**, em vez do caixa? Seria a fonte ideal
— eliminaria os gaps 1–6 de uma vez.
