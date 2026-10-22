/* ============================================================
   CANNONDALE BIKE INTELLIGENCE — Aplicação frontend (páginas)
   ============================================================ */
const API = "";
const BR = { style: "currency", currency: "BRL", minimumFractionDigits: 0, maximumFractionDigits: 0 };
const fmtMoney = (v) => (v == null ? "–" : Number(v).toLocaleString("pt-BR", BR));
const fmtInt = (v) => (v == null ? "–" : Number(v).toLocaleString("pt-BR"));
const fmtDate = (d) => {
  if (!d) return "–";
  const s = String(d);
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) {
    const [a, m, dia] = s.split("-");
    return `${dia}/${m}/${a}`;
  }
  return s;
};
const statusPill = (s) => {
  if (!s) return '<span class="status-pill">–</span>';
  const cls = "status-" + String(s).replace(/\s+/g, "-").toLowerCase();
  return `<span class="status-pill ${cls}">${s}</span>`;
};

const charts = {};
const CORES = {
  verde: "#10b981", verdeClaro: "#34d399", azul: "#0ea5e9",
  roxo: "#a78bfa", laranja: "#f59e0b", vermelho: "#ef4444",
  rosa: "#f472b6", limao: "#a3e635", ciano: "#22d3ee",
};

Chart.defaults.color = "#a1a1aa";
Chart.defaults.font.family = '"Inter", sans-serif';
Chart.defaults.font.size = 11;
Chart.defaults.borderColor = "#2a2a2a";
Chart.defaults.plugins.legend = { display: false };

function destroyChart(key) {
  if (charts[key]) { charts[key].destroy(); charts[key] = null; }
}

function tooltipPremium(ctx) {
  const { tooltip } = Chart.tooltip;
  const { body, labelColors, labelTextColors, title, beforeBody, afterBody } = ctx;
  const alignWithPixel = (p) => Math.round(p) - 0.5;
  const x = alignWithPixel(ctx.x);
  const y = alignWithPixel(ctx.y);
  const xPadding = 8;
  const yPadding = 8;
  const radius = 8;
  const height = beforeBody.length + body.length + afterBody.length + (title ? title.length : 0);
  const width = 160;

  const bgColor = "#171717";
  const borderColor = "#3a3a3a";
  const shadowColor = "rgba(0,0,0,0.5)";

  ctx.fillStyle = shadowColor;
  ctx.fillRect(x + 2, y + 2, width, height * 16 + yPadding * 2);

  ctx.fillStyle = bgColor;
  ctx.strokeStyle = borderColor;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.roundRect(x, y, width, height * 16 + yPadding * 2, radius).fill();
  ctx.stroke();

  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  ctx.fillStyle = "#71717a";
  ctx.font = Chart.defaults.font.family + " 10px";
  let ty = y + yPadding + 4;

  title.forEach((t) => {
    ctx.fillStyle = "#e7e7e7";
    ctx.font = Chart.defaults.font.family + " bold 12px";
    ctx.fillText(t, x + xPadding, ty);
    ty += 16;
  });

  beforeBody.forEach((b) => {
    ctx.fillStyle = "#a1a1aa";
    ctx.font = Chart.defaults.font.family + " 11px";
    ctx.fillText(b, x + xPadding, ty);
    ty += 16;
  });

  body.forEach((b, i) => {
    const colors = labelColors[i];
    ctx.fillStyle = colors.backgroundColor;
    ctx.fillRect(x + xPadding, ty + 2, 10, 10);
    ctx.fillStyle = labelTextColors[i];
    ctx.font = Chart.defaults.font.family + " 12px";
    ctx.fillText(b.lines?.[0] || b, x + xPadding + 16, ty);
    ty += 16;
  });

  afterBody.forEach((b) => {
    ctx.fillStyle = "#a1a1aa";
    ctx.font = Chart.defaults.font.family + " 11px";
    ctx.fillText(b, x + xPadding, ty);
    ty += 16;
  });
}

const app = {
  state: { pagina: "visao-geral", produtos: [], lojas: [], filtroVendasCat: "" },

  init() {
    this.bindNav();
    this.bindFilters();
    this.go("visao-geral");
  },

  bindNav() {
    document.querySelectorAll(".item").forEach((el) => {
      el.addEventListener("click", (e) => {
        e.preventDefault();
        this.go(el.dataset.page);
      });
    });
    document.getElementById("nav-toggle").addEventListener("click", () => {
      document.getElementById("sidebar").classList.toggle("open");
    });
  },

  go(pagina) {
    this.state.pagina = pagina;

    // menu ativo
    document.querySelectorAll(".item").forEach((el) => el.classList.remove("active"));
    const ativo = document.querySelector(`.item[data-page="${pagina}"]`);
    if (ativo) ativo.classList.add("active");

    // esconder todas as páginas e mostrar a selecionada
    document.querySelectorAll("section.page").forEach((s) => (s.style.display = "none"));
    const alvo = document.getElementById("page-" + pagina);
    if (alvo) alvo.style.display = "block";

    document.getElementById("sidebar").classList.remove("open");

    // títulos do cabeçalho
    const titulos = {
      "visao-geral": ["Visão Geral", "Centro de inteligência operacional"],
      comercial: ["Comercial", "Faturamento, lojas e transações"],
      produtos: ["Produtos", "Catálogo oficial de bicicletas"],
      estoque: ["Estoque", "Distribuição e disponibilidade"],
      lojas: ["Lojas", "Rede comercial e desempenho"],
      transporte: ["Transporte", "Fluxos operacionais e cargas"],
      analises: ["Relatórios", "Visão consolidada dos registros"],
    };
    const [t, s] = titulos[pagina] || ["", ""];
    document.getElementById("page-title").textContent = t;
    document.getElementById("page-lead").textContent = s;

    this.scrollTop();

    // carregar dados da página
    if (pagina === "visao-geral") this.carregarVisaoGeral();
    else if (pagina === "comercial") this.carregarComercial();
    else if (pagina === "produtos") this.carregarProdutos();
    else if (pagina === "estoque") this.carregarEstoque();
    else if (pagina === "lojas") this.carregarLojas();
    else if (pagina === "transporte") this.carregarLogistica();
    else if (pagina === "analises") this.carregarAnalises();
  },

  scrollTop() {
    document.querySelector(".main").scrollTo({ top: 0, behavior: "smooth" });
  },

  bindFilters() {
    document.getElementById("f-vendas-meses").addEventListener("change", () => this.carregarComercial());
    document.getElementById("f-vendas-cat").addEventListener("change", () => this.carregarComercial());
    document.getElementById("f-prod-busca").addEventListener("input", (e) => {
      clearTimeout(this._buscaT);
      this._buscaT = setTimeout(() => this.carregarProdutos(), 250);
    });
    document.getElementById("f-prod-cat").addEventListener("change", () => this.carregarProdutos());
    document.getElementById("f-prod-plat").addEventListener("change", () => this.carregarProdutos());
    document.getElementById("f-estoque-loja").addEventListener("change", () => this.carregarEstoque());
    document.getElementById("f-estoque-status").addEventListener("change", () => this.carregarEstoque());
    document.getElementById("f-loja-busca").addEventListener("input", (e) => {
      clearTimeout(this._lojaT);
      this._lojaT = setTimeout(() => this.carregarLojas(), 250);
    });
    document.getElementById("f-loja-tipo").addEventListener("change", () => this.carregarLojas());
    document.getElementById("f-loja-regiao").addEventListener("change", () => this.carregarLojas());
    document.getElementById("f-log-modal").addEventListener("change", () => this.carregarLogistica());
    document.getElementById("f-log-status").addEventListener("change", () => this.carregarLogistica());
  },

  limparFiltrosProdutos() {
    document.getElementById("f-prod-busca").value = "";
    document.getElementById("f-prod-cat").value = "";
    document.getElementById("f-prod-plat").value = "";
    this.carregarProdutos();
  },

  async fetch(endpoint, params = {}) {
    const qs = new URLSearchParams(params).toString();
    const res = await fetch(`${API}${endpoint}${qs ? "?" + qs : ""}`);
    if (!res.ok) throw new Error(`Erro ${res.status} em ${endpoint}`);
    return res.json();
  },

  /* ===================== VISÃO GERAL ===================== */
  async carregarVisaoGeral() {
    try {
      const k = await this.fetch("/api/kpis/overview");
      document.getElementById("footer-data").textContent = fmtDate(k.ultima_atualizacao);
      document.getElementById("hero-data").textContent = fmtDate(k.ultima_atualizacao);
      document.getElementById("hero-produtos").textContent = fmtInt(k.total_produtos);

      document.getElementById("kpi-faturamento").textContent = fmtMoney(k.faturamento_90d);
      document.getElementById("kpi-unidades").textContent = fmtInt(k.unidades_vendidas_90d);
      document.getElementById("kpi-estoque").textContent = fmtInt(k.estoque_total_unidades);
      document.getElementById("kpi-valor-estoque").textContent = fmtMoney(k.valor_estoque);
      document.getElementById("kpi-lojas").textContent = fmtInt(k.total_lojas);
      document.getElementById("kpi-otif").textContent = (k.otif_pct != null ? k.otif_pct : "–") + "%";

      const [vendasMes, vendasCat, estoqueResumo] = await Promise.all([
        this.fetch("/api/vendas/mensal", { meses: 6 }),
        this.fetch("/api/vendas/categoria"),
        this.fetch("/api/estoque/resumo"),
      ]);

      this.chartLinha("g-faturamento", vendasMes.map((r) => r.mes), vendasMes.map((r) => Number(r.receita)), CORES.verde);
      this.chartBarra("g-categoria", vendasCat.map((r) => r.categoria), vendasCat.map((r) => Number(r.faturamento)), CORES.azul);
      this.chartBarra("g-estoque-cat", estoqueResumo.por_categoria.map((r) => r.categoria), estoqueResumo.por_categoria.map((r) => Number(r.unidades)), CORES.verdeClaro);
      this.chartRosca("g-est-status", estoqueResumo.por_status.map((r) => r.status || "Indefinido"), estoqueResumo.por_status.map((r) => Number(r.skus)));

      const lojas = await this.fetch("/api/vendas/loja");
      const tb = document.querySelector("#t-lojas-hero tbody");
      tb.innerHTML = "";
      lojas.slice(0, 8).forEach((r) => {
        tb.innerHTML += `<tr>
          <td><b>${r.nome_loja}</b></td>
          <td>${r.cidade || "–"}</td>
          <td>${fmtMoney(r.faturamento)}</td>
          <td>${fmtInt(r.pedidos)}</td>
        </tr>`;
      });

      this.mostrarBikeDestaque();
    } catch (e) {
      console.warn("Visão geral:", e);
    }
  },

  async mostrarBikeDestaque() {
    try {
      const produtos = await this.fetch("/api/produtos");
      const comImg = produtos.filter((p) => p.imagem || p.arquivo_local);
      if (!comImg.length) return;
      const p = comImg[0];
      const img = document.getElementById("hero-bike-img");
      const fb = document.getElementById("hero-bike-fallback");
      const src = this.imagemUrl(p);
      if (src) {
        img.src = src;
        img.style.display = "block";
        fb.style.display = "none";
      } else {
        img.style.display = "none";
        fb.style.display = "flex";
      }
    } catch (e) {
      console.warn("Bike destaque:", e);
    }
  },

  imagemUrl(p) {
    const web = (p.arquivo_local || "").replace(/^Imagens[\/\\]/, "");
    if (web) return `/imagens/${web}`;
    return p.imagem || "";
  },

  /* ===================== COMERCIAL ===================== */
  async carregarComercial() {
    try {
      const meses = document.getElementById("f-vendas-meses").value;
      const cat = document.getElementById("f-vendas-cat").value;
      this.state.filtroVendasCat = cat;
      const [kpis, mensal, porLoja, categorias, recente] = await Promise.all([
        this.fetch("/api/kpis/overview"),
        this.fetch("/api/vendas/mensal", { meses }),
        this.fetch("/api/vendas/loja"),
        this.fetch("/api/vendas/categoria"),
        this.fetch("/api/vendas/detalhe", { limit: 40 }),
      ]);

      const sel = document.getElementById("f-vendas-cat");
      if (sel.options.length === 1) {
        categorias.forEach((c) => sel.add(new Option(c.categoria, c.categoria)));
      }

      const totalFat = mensal.reduce((a, r) => a + Number(r.receita || 0), 0);
      const totalUnid = mensal.reduce((a, r) => a + Number(r.unidades || 0), 0);
      const totalPed = mensal.reduce((a, r) => a + Number(r.pedidos || 0), 0);
      const ticket = totalPed ? totalFat / totalPed : 0;
      document.getElementById("cv-faturamento").textContent = fmtMoney(totalFat);
      document.getElementById("cv-unidades").textContent = fmtInt(totalUnid);
      document.getElementById("cv-pedidos").textContent = fmtInt(totalPed);
      document.getElementById("cv-ticket").textContent = fmtMoney(ticket);

      this.chartLinha("g-vendas-mensal", mensal.map((r) => r.mes), mensal.map((r) => Number(r.receita)), CORES.verde);
      this.chartBarra("g-vendas-loja", porLoja.map((r) => r.nome_loja), porLoja.map((r) => Number(r.faturamento)), CORES.azul);

      const tb = document.querySelector("#t-vendas tbody");
      tb.innerHTML = "";
      recente.forEach((r) => {
        tb.innerHTML += `<tr>
          <td>${fmtDate(r.data_venda)}</td>
          <td><b>${r.modelo}</b></td>
          <td>${r.categoria}</td>
          <td>${fmtInt(r.quantidade)}</td>
          <td>${fmtMoney(r.valor_bruto)}</td>
          <td>${fmtMoney(r.valor_liquido)}</td>
          <td>${r.nome_loja}</td>
          <td>${r.cidade || "–"}</td>
          <td>${r.forma_pagamento || "–"}</td>
          ${statusPill(r.status_venda)}
        </tr>`;
      });
    } catch (e) {
      console.warn("Comercial:", e);
    }
  },

  /* ===================== PRODUTOS ===================== */
  async carregarProdutos() {
    try {
      const params = {};
      const busca = document.getElementById("f-prod-busca").value;
      const cat = document.getElementById("f-prod-cat").value;
      const plat = document.getElementById("f-prod-plat").value;
      if (busca) params.busca = busca;
      if (cat) params.categoria = cat;
      const produtos = await this.fetch("/api/produtos", params);
      this.state.produtos = produtos;

      const catsSel = document.getElementById("f-prod-cat");
      const platSel = document.getElementById("f-prod-plat");
      if (catsSel.options.length === 1) {
        const categorias = await this.fetch("/api/categorias");
        categorias.forEach((c) => catsSel.add(new Option(c.categoria, c.categoria)));
        const plataformas = [...new Set(produtos.map((p) => p.plataforma).filter(Boolean))].sort();
        plataformas.forEach((p) => platSel.add(new Option(p, p)));
      }

      const catEl = document.getElementById("catalogo");
      const vazio = document.getElementById("vazio-prod");
      document.getElementById("contador-prod").textContent = `${produtos.length} produtos`;
      catEl.innerHTML = "";
      if (produtos.length === 0) { vazio.style.display = "block"; return; }
      vazio.style.display = "none";

      produtos.forEach((p) => {
        const src = this.imagemUrl(p);
        const preco = p.preco != null ? fmtMoney(p.preco) : "Consultar";
        const disp = p.tipo_dado === "OFICIAL" ? "Catálogo oficial" : "Dados simulados";
        catEl.innerHTML += `
          <div class="prod-card" onclick="app.abrirProduto('${p.id_produto.replace(/'/g, "\\'")}')">
            <div class="prod-imagem-box">
              <img class="prod-img" src="${src}" alt="${p.modelo}" onerror="this.style.display='none'; this.parentElement.querySelector('.prod-fallback').style.display='flex';">
              <div class="prod-fallback">Sem imagem</div>
              <div class="prod-tag">${p.categoria}</div>
            </div>
            <div class="prod-body">
              <div class="prod-cat">${p.categoria} • ${p.subcategoria || ""}</div>
              <h3>${p.modelo}</h3>
              <div class="prod-sku">${p.id_produto}</div>
              <div class="prod-preco">${preco}</div>
              <div class="prod-disp">${disp}</div>
              <div class="prod-espec">${p.especificacoes || "Especificações não disponíveis."}</div>
              <div class="prod-acoes">
                <button class="btn btn-ghost" onclick="event.stopPropagation(); app.abrirProduto('${p.id_produto.replace(/'/g, "\\'")}')">Ver detalhes</button>
              </div>
            </div>
          </div>`;
      });
    } catch (e) {
      console.warn("Produtos:", e);
      document.getElementById("catalogo").innerHTML = "";
      document.getElementById("vazio-prod").style.display = "block";
    }
  },

  async abrirProduto(id) {
    try {
      const det = await this.fetch(`/api/produto/${id}`);
      const p = det.produto;
      document.getElementById("pd-modelo").textContent = p.modelo;
      document.getElementById("pd-cat").textContent = `${p.categoria} • ${p.subcategoria || ""}`;
      document.getElementById("pd-sku").textContent = `${p.id_produto}  •  ${p.plataforma || ""}`;
      document.getElementById("pd-preco").textContent = p.preco_site != null ? fmtMoney(p.preco_site) : "Consultar";
      document.getElementById("pd-tipo").textContent = p.tipo_dado === "OFICIAL" ? "Oficial" : "Simulado";
      document.getElementById("pd-disp").textContent = p.tipo_dado === "OFICIAL" ? "Disponível" : "Consultar";
      document.getElementById("pd-espec").textContent = p.especificacoes || "Não há especificações detalhadas.";
      document.getElementById("pd-categoria-tag").textContent = p.categoria;
      const link = document.getElementById("pd-link");
      link.href = p.url_produto || "#";
      if (!p.url_produto) link.style.display = "none";

      const img = document.getElementById("pd-imagem");
      const fb = document.getElementById("pd-fallback");
      const imgs = det.imagens || [];
      const primeiro = imgs[0];
      const src = primeiro ? this.imagemUrl({ arquivo_local: primeiro.arquivo_local, imagem: primeiro.url_imagem }) : "";
      if (src) {
        img.src = src;
        img.style.display = "block";
        fb.style.display = "none";
      } else {
        img.style.display = "none";
        fb.style.display = "flex";
      }

      const est = det.estoque || {};
      const v = det.vendas || {};
      document.getElementById("pd-estoque").textContent = fmtInt(est.total);
      document.getElementById("pd-vendas").textContent = fmtInt(v.unidades);
      document.getElementById("pd-fat").textContent = fmtMoney(v.faturamento);

      document.getElementById("modal-produto").style.display = "flex";
    } catch (e) {
      console.warn("Produto:", e);
      alert("Não foi possível carregar os detalhes do produto.");
    }
  },

  fecharProduto() {
    document.getElementById("modal-produto").style.display = "none";
  },

  /* ===================== ESTOQUE ===================== */
  async carregarEstoque() {
    try {
      const res = await this.fetch("/api/estoque/resumo");
      document.getElementById("estoque-data").textContent = fmtDate(res.data);
      const porLoja = res.por_loja;
      const porCat = res.por_categoria;
      const porStatus = res.por_status;
      const baixo = res.baixo_estoque;

      const total = porLoja.reduce((a, r) => a + Number(r.unidades || 0), 0);
      const skus = porLoja.reduce((a, r) => a + Number(r.skus || 0), 0);
      const crit = porStatus.find((r) => (r.status || "").toLowerCase() === "critico");
      const att = porStatus.find((r) => (r.status || "").toLowerCase() === "atencao");
      document.getElementById("e-total").textContent = fmtInt(total);
      document.getElementById("e-skus").textContent = fmtInt(skus);
      document.getElementById("e-criticos").textContent = fmtInt(crit ? crit.skus : 0);
      document.getElementById("e-atencao").textContent = fmtInt(att ? att.skus : 0);

      this.chartRosca("g-est-status2", porStatus.map((r) => r.status || "Indefinido"), porStatus.map((r) => Number(r.skus || 0)));
      this.chartBarra("g-est-loja", porLoja.map((r) => r.nome_loja), porLoja.map((r) => Number(r.unidades || 0)), CORES.verde);

      const selL = document.getElementById("f-estoque-loja");
      if (selL.options.length === 1) {
        porLoja.forEach((r) => selL.add(new Option(r.nome_loja, r.nome_loja)));
      }

      const tb = document.querySelector("#t-baixo tbody");
      tb.innerHTML = "";
      baixo.forEach((r) => {
        tb.innerHTML += `<tr>
          <td><b>${r.modelo}</b></td>
          <td>${r.categoria}</td>
          <td>${r.nome_loja}</td>
          <td>${fmtInt(r.estoque_atual)}</td>
          <td>${fmtInt(r.estoque_minimo)}</td>
          ${statusPill("Crítico")}
        </tr>`;
      });
    } catch (e) {
      console.warn("Estoque:", e);
    }
  },

  /* ===================== LOJAS ===================== */
  async carregarLojas() {
    try {
      const lojas = await this.fetch("/api/lojas");
      this.state.lojas = lojas;
      const busca = document.getElementById("f-loja-busca").value.toLowerCase();
      const tipo = document.getElementById("f-loja-tipo").value;
      const regiao = document.getElementById("f-loja-regiao").value;
      let filtradas = lojas.filter((l) => {
        const txt = `${l.nome_loja} ${l.cidade || ""} ${l.estado_provincia || ""}`.toLowerCase();
        return (!busca || txt.includes(busca)) && (!tipo || l.tipo_loja === tipo) && (!regiao || l.regiao === regiao);
      });

      const st = document.getElementById("f-loja-tipo");
      const rg = document.getElementById("f-loja-regiao");
      if (st.options.length === 1) {
        [...new Set(lojas.map((l) => l.tipo_loja).filter(Boolean)).sort()].forEach((t) => st.add(new Option(t, t)));
        [...new Set(lojas.map((l) => l.regiao).filter(Boolean)).sort()].forEach((r) => rg.add(new Option(r, r)));
      }

      document.getElementById("contador-lojas").textContent = `${filtradas.length} lojas`;
      const tb = document.querySelector("#t-lojas-lista tbody");
      tb.innerHTML = "";
      filtradas.forEach((l) => {
        tb.innerHTML += `<tr>
          <td><b>${l.nome_loja}</b></td>
          <td>${l.tipo_loja || "–"}</td>
          <td>${l.cidade || "–"}${l.estado_provincia ? " / " + l.estado_provincia : ""}</td>
          <td>${l.pais || "–"}</td>
          <td>${l.regiao || "–"}</td>
          <td>${l.perfil_desempenho || "–"}</td>
          ${statusPill(l.status_loja)}
          <td>${l.fonte || "–"}</td>
        </tr>`;
      });

      const aggRegiao = {};
      lojas.forEach((l) => { aggRegiao[l.regiao || "Indefinido"] = (aggRegiao[l.regiao || "Indefinido"] || 0) + 1; });
      const aggTipo = {};
      lojas.forEach((l) => { aggTipo[l.tipo_loja || "Indefinido"] = (aggTipo[l.tipo_loja || "Indefinido"] || 0) + 1; });
      this.chartRosca("g-lojas-regiao", Object.keys(aggRegiao), Object.values(aggRegiao));
      this.chartRosca("g-lojas-tipo", Object.keys(aggTipo), Object.values(aggTipo));
    } catch (e) {
      console.warn("Lojas:", e);
    }
  },

  /* ===================== TRANSPORTE ===================== */
  async carregarLogistica() {
    try {
      const [res, mov] = await Promise.all([this.fetch("/api/logistica/resumo"), this.fetch("/api/logistica/movimentos")]);
      const modalSel = document.getElementById("f-log-modal").value;
      const statusSel = document.getElementById("f-log-status").value;
      let filtrados = mov;
      if (modalSel) filtrados = filtrados.filter((m) => m.modal === modalSel);
      if (statusSel) filtrados = filtrados.filter((m) => m.status_logistica === statusSel);

      const custoTotal = filtrados.reduce((a, m) => a + Number(m.custo_frete || 0), 0);
      document.getElementById("log-movimentos").textContent = fmtInt(filtrados.length);
      document.getElementById("log-otif").textContent = res.otif_pct != null ? res.otif_pct + "%" : "–";
      document.getElementById("log-atraso").textContent = (res.atraso_medio != null ? res.atraso_medio.toFixed(1) : "–") + " dias";
      document.getElementById("log-custo").textContent = fmtMoney(custoTotal);

      this.chartRosca("g-log-modal", res.por_modal.map((r) => r.modal), res.por_modal.map((r) => Number(r.movimentos || 0)));
      this.chartRosca("g-log-status", res.por_status.map((r) => r.status || "Indefinido"), res.por_status.map((r) => Number(r.movimentos || 0)));

      const tb = document.querySelector("#t-logistica tbody");
      tb.innerHTML = "";
      filtrados.forEach((m) => {
        tb.innerHTML += `<tr>
          <td>${fmtDate(m.data_envio)}</td>
          <td>${fmtDate(m.data_prevista)}</td>
          <td>${fmtDate(m.data_entrega)}</td>
          <td>${m.modelo}</td>
          <td>${m.categoria}</td>
          <td>${fmtInt(m.quantidade)}</td>
          <td>${m.nome_loja}</td>
          <td>${m.cidade_origem || "–"}</td>
          <td>${m.cidade_destino || "–"}</td>
          <td>${m.modal}</td>
          <td>${m.transportadora || "–"}</td>
          ${statusPill(m.status_logistica)}
          <td>${fmtMoney(m.custo_frete)}</td>
        </tr>`;
      });
    } catch (e) {
      console.warn("Logística:", e);
    }
  },

  /* ===================== ANÁLISES ===================== */
  async carregarAnalises() {
    try {
      const [vendas, estoque, log] = await Promise.all([
        this.fetch("/api/vendas/detalhe", { limit: 500 }),
        this.fetch("/api/estoque/resumo"),
        this.fetch("/api/logistica/resumo"),
      ]);
      document.getElementById("an-periodo").textContent = "2024-01 a 2026-10";
      document.getElementById("an-produtos").textContent = fmtInt(56);
      document.getElementById("an-estoque").textContent = fmtInt(estoque.por_loja.reduce((a, r) => a + Number(r.skus || 0), 0));
      document.getElementById("an-logistica").textContent = fmtInt(log.total);

      const porMes = {};
      vendas.forEach((v) => {
        const d = String(v.data_venda).substring(0, 7);
        porMes[d] = (porMes[d] || 0) + Number(v.valor_liquido || 0);
      });
      const labels = Object.keys(porMes).sort();
      this.chartLinha("g-an-vendas", labels, labels.map((l) => porMes[l]), CORES.verde);
      this.chartBarra("g-an-estoque", estoque.por_categoria.map((r) => r.categoria), estoque.por_categoria.map((r) => Number(r.unidades || 0)), CORES.azul);

      const tb = document.querySelector("#t-analise tbody");
      tb.innerHTML = "";
      vendas.slice(0, 60).forEach((v) => {
        tb.innerHTML += `<tr>
          <td>${fmtDate(v.data_venda)}</td>
          <td>${v.modelo}</td>
          <td>${v.categoria}</td>
          <td>${v.nome_loja}</td>
          <td>${fmtInt(v.quantidade)}</td>
          <td>${fmtMoney(v.valor_liquido)}</td>
          <td>${v.canal_venda || "–"}</td>
          ${statusPill(v.status_venda)}
        </tr>`;
      });
    } catch (e) {
      console.warn("Análises:", e);
    }
  },

  /* ===================== GRÁFICOS ===================== */
  chartLinha(id, labels, data, color) {
    destroyChart(id);
    const ctx = document.getElementById(id).getContext("2d");
    charts[id] = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: "Valor (R$)",
          data,
          borderColor: color,
          backgroundColor: "rgba(16,185,129,0.06)",
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6,
          pointBackgroundColor: color,
          pointBorderColor: "#ffffff",
          pointBorderWidth: 2,
          borderWidth: 2.5,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        interaction: { mode: "nearest", intersect: false },
        plugins: { tooltip: { enabled: false, external: tooltipPremium } },
        scales: {
          x: { grid: { display: false, drawBorder: false }, ticks: { color: "#71717a", font: { size: 10 } } },
          y: { grid: { color: "#2a2a2a", drawBorder: false }, ticks: { color: "#71717a", font: { size: 10 }, callback: (v) => v >= 1e6 ? (v / 1e6).toFixed(1) + "M" : v >= 1e3 ? (v / 1e3).toFixed(1) + "k" : v } },
        },
        animation: { duration: 800, easing: "easeOutQuart" },
      },
    });
  },

  chartBarra(id, labels, data, color) {
    destroyChart(id);
    const ctx = document.getElementById(id).getContext("2d");
    charts[id] = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label: "Valor",
          data,
          backgroundColor: color,
          borderRadius: 6,
          barPercentage: 0.65,
          categoryPercentage: 0.8,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { tooltip: { enabled: false, external: tooltipPremium } },
        scales: {
          x: { grid: { display: false, drawBorder: false }, ticks: { color: "#71717a", font: { size: 10 } } },
          y: { grid: { color: "#2a2a2a", drawBorder: false }, ticks: { color: "#71717a", font: { size: 10 }, callback: (v) => v >= 1e3 ? (v / 1e3).toFixed(1) + "k" : v } },
        },
        animation: { duration: 800, easing: "easeOutQuart" },
      },
    });
  },

  chartRosca(id, labels, data) {
    destroyChart(id);
    const ctx = document.getElementById(id).getContext("2d");
    const cores = Object.values(CORES);
    charts[id] = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: cores.slice(0, labels.length),
          borderWidth: 0,
          hoverOffset: 24,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        cutout: "78%",
        plugins: {
          legend: { position: "bottom", labels: { padding: 20, font: { size: 11 }, color: "#8f8f91", boxWidth: 10 } },
          tooltip: { enabled: false, external: tooltipPremium },
        },
        animation: { duration: 800, easing: "easeOutQuart" },
      },
    });
  },
};

document.addEventListener("DOMContentLoaded", () => app.init());
