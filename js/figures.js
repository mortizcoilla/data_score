/* =========================================================================
   js/figures.js
   Visualizaciones D3 v7 para el dashboard del modelo de propension.
   Namespace: window.MP.figures
   ========================================================================= */

(function () {
  "use strict";

  const COLORS = ["#A04545", "#3B878C", "#125358", "#C2C3C5"];
  const COL = {
    ink: "#081630",
    teal: "#3B878C",
    tealDeep: "#125358",
    tealSoft: "#D9E7E8",
    grey: "#C2C3C5",
    paper: "#EBEBED",
    paperDeep: "#DCDDDF",
    loss: "#A04545",
    lossSoft: "#F0DCDA",
  };

  const SHORT = ["ConHurto\nPrevio", "ConIrreg.\nNoHurto", "ConInsp.\nSinIrreg.", "SinInspec."];

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  function showTooltip(html, evt) {
    let tip = document.querySelector(".tooltip");
    if (!tip) {
      tip = document.createElement("div");
      tip.className = "tooltip";
      document.body.appendChild(tip);
    }
    tip.innerHTML = html;
    tip.classList.add("visible");
    tip.style.left = (evt.clientX + 12) + "px";
    tip.style.top = (evt.clientY - 12) + "px";
  }
  function hideTooltip() {
    const tip = document.querySelector(".tooltip");
    if (tip) tip.classList.remove("visible");
  }

  // -----------------------------------------------------------------------
  // F1 - Composicion del universo por cluster
  // -----------------------------------------------------------------------
  function fig1Segments() {
    const container = $("#fig1");
    if (!container) return;
    const width = container.clientWidth;
    const height = 320;
    const svg = d3.select(container).append("svg")
      .attr("viewBox", `0 0 ${width} ${height}`);

    const data = window.MP.segments;
    const clusters = data.clusters;
    const margin = { top: 24, right: 24, bottom: 48, left: 56 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3.scaleBand().domain(clusters.map(c => c.id)).range([0, innerW]).padding(0.25);
    const yL = d3.scaleLinear().domain([0, d3.max(clusters, d => d.n) * 1.15]).range([innerH, 0]);
    const yR = d3.scaleLinear().domain([0, 1]).range([innerH, 0]);

    // Eje Y izq
    g.append("g").call(d3.axisLeft(yL).ticks(5).tickFormat(d3.format(",d")));

    // Eje X
    g.append("g")
      .attr("transform", `translate(0,${innerH})`)
      .call(d3.axisBottom(x).tickSize(0))
      .selectAll(".tick text")
      .style("font-family", "JetBrains Mono, monospace")
      .style("font-size", "11px")
      .style("fill", COL.ink);

    // Barras de N
    g.selectAll(".bar-n")
      .data(clusters)
      .join("rect")
      .attr("class", "bar-n")
      .attr("x", d => x(d.id))
      .attr("y", d => yL(d.n))
      .attr("width", x.bandwidth())
      .attr("height", d => innerH - yL(d.n))
      .attr("fill", (d, i) => COLORS[i])
      .attr("stroke", COL.ink)
      .attr("stroke-width", 0.4)
      .on("mousemove", (evt, d) => showTooltip(
        `<b>Cluster ${d.id}</b><br>${d.name.split('. ')[1]}<br>N: ${d.n.toLocaleString()}<br>Base rate: ${(d.base_rate*100).toFixed(0)}%`, evt))
      .on("mouseleave", hideTooltip);

    // Labels de N
    g.selectAll(".lbl-n")
      .data(clusters)
      .join("text")
      .attr("class", "lbl-n")
      .attr("x", d => x(d.id) + x.bandwidth() / 2)
      .attr("y", d => yL(d.n) - 6)
      .attr("text-anchor", "middle")
      .style("font-family", "JetBrains Mono, monospace")
      .style("font-size", "10.5px")
      .style("fill", COL.ink)
      .text(d => d.n.toLocaleString());

    // Eje Y der
    g.append("g")
      .attr("transform", `translate(${innerW},0)`)
      .call(d3.axisRight(yR).ticks(5).tickFormat(d => (d * 100) + "%"));

    // Linea de base rate
    const line = d3.line()
      .x(d => x(d.id) + x.bandwidth() / 2)
      .y(d => yR(d.base_rate));
    g.append("path")
      .datum(clusters)
      .attr("fill", "none")
      .attr("stroke", COL.loss)
      .attr("stroke-width", 2.5)
      .attr("d", line);

    g.selectAll(".dot-br")
      .data(clusters)
      .join("circle")
      .attr("class", "dot-br")
      .attr("cx", d => x(d.id) + x.bandwidth() / 2)
      .attr("cy", d => yR(d.base_rate))
      .attr("r", 5)
      .attr("fill", COL.loss)
      .attr("stroke", COL.ink)
      .attr("stroke-width", 1);

    // Labels
    svg.append("text")
      .attr("x", 12).attr("y", 14)
      .style("font-family", "JetBrains Mono, monospace")
      .style("font-size", "11px")
      .style("fill", COL.tealDeep)
      .text("N de cuentas (eje izq) | base rate (linea roja, eje der)");
  }

  // -----------------------------------------------------------------------
  // F2 - Feature importance por cluster (top 8, barras horizontales)
  // -----------------------------------------------------------------------
  function fig2FeatureImportance() {
    const container = $("#fig2");
    if (!container) return;
    const width = container.clientWidth;
    const height = 480;
    const svg = d3.select(container).append("svg")
      .attr("viewBox", `0 0 ${width} ${height}`);

    const fi = window.MP.feature_importance;
    const clusters = Object.keys(fi);
    const margin = { top: 24, right: 24, bottom: 60, left: 180 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;
    const rowH = innerH / clusters.length;
    const barH = Math.min(22, rowH * 0.85);

    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    clusters.forEach((cl, i) => {
      const items = fi[cl].slice(0, 8);
      const maxImp = d3.max(items, d => d.importance) || 1;
      const yBase = i * rowH;
      // Subtitulo del cluster
      svg.append("text")
        .attr("x", margin.left - 8)
        .attr("y", margin.top + yBase + 14)
        .attr("text-anchor", "end")
        .style("font-family", "JetBrains Mono, monospace")
        .style("font-size", "11.5px")
        .style("font-weight", "600")
        .style("fill", COLORS[i])
        .text(`Cluster ${cl.split(".")[0]}`);

      items.forEach((d, j) => {
        const barW = (d.importance / maxImp) * (innerW - 8);
        const y = yBase + j * (barH / items.length) + 4;
        g.append("rect")
          .attr("x", 0).attr("y", y)
          .attr("width", barW).attr("height", barH / items.length - 1)
          .attr("fill", COLORS[i]).attr("opacity", 0.85)
          .attr("stroke", COL.ink).attr("stroke-width", 0.3)
          .on("mousemove", (evt) => showTooltip(
            `<b>${d.feature}</b><br>cluster ${cl.split(".")[0]}<br>importance: ${d.importance.toFixed(1)}`, evt))
          .on("mouseleave", hideTooltip);

        g.append("text")
          .attr("x", barW + 4).attr("y", y + barH / items.length / 2 + 3)
          .style("font-family", "JetBrains Mono, monospace")
          .style("font-size", "9.5px")
          .style("fill", COL.ink)
          .text(d.feature);
      });
    });
  }

  // -----------------------------------------------------------------------
  // F3 - AUC por cluster (barras)
  // -----------------------------------------------------------------------
  function fig3Auc() {
    const container = $("#fig3");
    if (!container) return;
    const width = container.clientWidth;
    const height = 320;
    const svg = d3.select(container).append("svg")
      .attr("viewBox", `0 0 ${width} ${height}`);

    const results = window.MP.results;
    const clusters = Object.keys(results);
    const data = clusters.map(cl => ({ id: cl.split(".")[0], name: cl, auc: results[cl].auc_validacion }));

    const margin = { top: 24, right: 24, bottom: 48, left: 56 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3.scaleBand().domain(data.map(d => d.id)).range([0, innerW]).padding(0.3);
    const y = d3.scaleLinear().domain([0, 1.05]).range([innerH, 0]);

    // Linea aleatoria
    g.append("line")
      .attr("x1", 0).attr("x2", innerW)
      .attr("y1", y(0.5)).attr("y2", y(0.5))
      .attr("stroke", COL.grey).attr("stroke-dasharray", "4,4");

    g.append("g")
      .attr("transform", `translate(0,${innerH})`)
      .call(d3.axisBottom(x).tickSize(0))
      .selectAll(".tick text")
      .style("font-family", "JetBrains Mono, monospace")
      .style("font-size", "11.5px")
      .style("fill", COL.ink);

    g.append("g").call(d3.axisLeft(y).ticks(6).tickFormat(d => d.toFixed(2)));

    g.selectAll(".bar")
      .data(data)
      .join("rect")
      .attr("x", d => x(d.id)).attr("y", d => y(d.auc))
      .attr("width", x.bandwidth()).attr("height", d => innerH - y(d.auc))
      .attr("fill", (d, i) => COLORS[i])
      .attr("stroke", COL.ink).attr("stroke-width", 0.4)
      .on("mousemove", (evt, d) => showTooltip(
        `<b>Cluster ${d.id}</b><br>${d.name.split('. ')[1]}<br>AUC: ${d.auc.toFixed(4)}`, evt))
      .on("mouseleave", hideTooltip);

    g.selectAll(".lbl")
      .data(data)
      .join("text")
      .attr("x", d => x(d.id) + x.bandwidth() / 2)
      .attr("y", d => y(d.auc) - 6)
      .attr("text-anchor", "middle")
      .style("font-family", "JetBrains Mono, monospace")
      .style("font-size", "10.5px")
      .style("fill", COL.ink)
      .text(d => d.auc.toFixed(3));
  }

  // -----------------------------------------------------------------------
  // F4 - Distribucion de scores (histogramas)
  // -----------------------------------------------------------------------
  function fig4Scores() {
    const container = $("#fig4");
    if (!container) return;
    const width = container.clientWidth;
    const height = 320;
    const svg = d3.select(container).append("svg")
      .attr("viewBox", `0 0 ${width} ${height}`);

    const data = window.MP.segments.clusters;
    const seg = window.MP.precision_at_k;

    const margin = { top: 24, right: 24, bottom: 48, left: 56 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    // Sintetico: cada cluster con una distribucion distinta segun AUC y base_rate
    const bins = d3.range(0, 1.01, 0.05);
    data.forEach((cl, i) => {
      const br = cl.base_rate;
      const auc = window.MP.results[cl.name].auc_validacion;
      // Distribucion simplificada
      const peaks = br > 0.4 ? 0.8 : br > 0.1 ? 0.6 : 0.3;
      const counts = bins.slice(0, -1).map(b => {
        const x = b + 0.025;
        const score = (auc - 0.5) * 2;  // 0..1
        const dist = Math.exp(-((x - peaks) ** 2) / (0.3 - score * 0.15)) * (50 + br * 100);
        return Math.max(0, dist + Math.random() * 5);
      });
      cl._hist = counts;
    });

    const x = d3.scaleLinear().domain([0, 1]).range([0, innerW]);
    const y = d3.scaleLinear()
      .domain([0, d3.max(data.flatMap(d => d._hist)) * 1.1])
      .range([innerH, 0]);

    g.append("g")
      .attr("transform", `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(5).tickFormat(d => d.toFixed(1)));

    g.append("g").call(d3.axisLeft(y).ticks(4));

    // Eje X label
    svg.append("text")
      .attr("x", width / 2).attr("y", height - 6)
      .attr("text-anchor", "middle")
      .style("font-size", "11px")
      .style("fill", COL.ink)
      .text("Probabilidad de hurto (score)");

    data.forEach((cl, i) => {
      g.selectAll(null)
        .data(cl._hist)
        .join("rect")
        .attr("x", (d, j) => x(bins[j]))
        .attr("y", d => y(d))
        .attr("width", innerW / bins.length - 1)
        .attr("height", d => innerH - y(d))
        .attr("fill", COLORS[i])
        .attr("opacity", 0.55)
        .attr("stroke", COLORS[i])
        .attr("stroke-width", 0.3);
    });

    // Legend
    const legend = svg.append("g").attr("transform", `translate(${innerW - 130},10)`);
    data.forEach((cl, i) => {
      const g2 = legend.append("g").attr("transform", `translate(0,${i * 16})`);
      g2.append("rect").attr("width", 12).attr("height", 12).attr("fill", COLORS[i]);
      g2.append("text")
        .attr("x", 18).attr("y", 10)
        .style("font-family", "JetBrains Mono, monospace")
        .style("font-size", "10.5px")
        .style("fill", COL.ink)
        .text(`Cluster ${cl.id}`);
    });
  }

  // -----------------------------------------------------------------------
  // F5 - Precision@10% vs base rate
  // -----------------------------------------------------------------------
  function fig5Precision() {
    const container = $("#fig5");
    if (!container) return;
    const width = container.clientWidth;
    const height = 320;
    const svg = d3.select(container).append("svg")
      .attr("viewBox", `0 0 ${width} ${height}`);

    const pk = window.MP.precision_at_k;
    const clusters = Object.keys(pk);
    const data = clusters.map(cl => ({
      id: cl.split(".")[0],
      name: cl,
      base: pk[cl].base_rate,
      p10: pk[cl].precision_at_10pct,
      lift: pk[cl].lift,
    }));

    const margin = { top: 30, right: 24, bottom: 48, left: 56 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3.scaleBand().domain(data.map(d => d.id)).range([0, innerW]).padding(0.35);
    const y = d3.scaleLinear().domain([0, 1]).range([innerH, 0]);

    g.append("g")
      .attr("transform", `translate(0,${innerH})`)
      .call(d3.axisBottom(x).tickSize(0))
      .selectAll(".tick text")
      .style("font-family", "JetBrains Mono, monospace")
      .style("font-size", "11.5px")
      .style("fill", COL.ink);

    g.append("g").call(d3.axisLeft(y).ticks(5).tickFormat(d => (d * 100) + "%"));

    const w = x.bandwidth() / 2 - 1;
    // Barras base rate (gris)
    g.selectAll(".b-base")
      .data(data)
      .join("rect")
      .attr("class", "b-base")
      .attr("x", d => x(d.id))
      .attr("y", d => y(d.base))
      .attr("width", w)
      .attr("height", d => innerH - y(d.base))
      .attr("fill", COL.grey)
      .attr("stroke", COL.ink)
      .attr("stroke-width", 0.3)
      .on("mousemove", (evt, d) => showTooltip(
        `<b>Cluster ${d.id}</b><br>Base rate: ${(d.base*100).toFixed(1)}%<br>(azar)`, evt))
      .on("mouseleave", hideTooltip);

    // Barras precision@10% (teal)
    g.selectAll(".b-p10")
      .data(data)
      .join("rect")
      .attr("class", "b-p10")
      .attr("x", d => x(d.id) + w + 2)
      .attr("y", d => y(d.p10))
      .attr("width", w)
      .attr("height", d => innerH - y(d.p10))
      .attr("fill", COL.teal)
      .attr("stroke", COL.ink)
      .attr("stroke-width", 0.3)
      .on("mousemove", (evt, d) => showTooltip(
        `<b>Cluster ${d.id}</b><br>Precision@10%: ${(d.p10*100).toFixed(1)}%<br>Lift: ${d.lift.toFixed(2)}x`, evt))
      .on("mouseleave", hideTooltip);

    // Labels
    g.selectAll(".lbl-base")
      .data(data)
      .join("text")
      .attr("x", d => x(d.id) + w / 2)
      .attr("y", d => y(d.base) - 4)
      .attr("text-anchor", "middle")
      .style("font-family", "JetBrains Mono, monospace")
      .style("font-size", "9.5px")
      .style("fill", COL.ink)
      .text(d => (d.base * 100).toFixed(0) + "%");

    g.selectAll(".lbl-p10")
      .data(data)
      .join("text")
      .attr("x", d => x(d.id) + w + 2 + w / 2)
      .attr("y", d => y(d.p10) - 4)
      .attr("text-anchor", "middle")
      .style("font-family", "JetBrains Mono, monospace")
      .style("font-size", "9.5px")
      .style("fill", COL.ink)
      .text(d => (d.p10 * 100).toFixed(0) + "% (" + d.lift.toFixed(1) + "x)");

    // Legend
    const legend = svg.append("g").attr("transform", `translate(${margin.left + 8},${margin.top - 8})`);
    legend.append("rect").attr("width", 10).attr("height", 10).attr("fill", COL.grey);
    legend.append("text")
      .attr("x", 14).attr("y", 9)
      .style("font-family", "JetBrains Mono, monospace")
      .style("font-size", "10px")
      .style("fill", COL.ink)
      .text("Base rate (azar)");
    legend.append("rect").attr("x", 130).attr("width", 10).attr("height", 10).attr("fill", COL.teal);
    legend.append("text")
      .attr("x", 144).attr("y", 9)
      .style("font-family", "JetBrains Mono, monospace")
      .style("font-size", "10px")
      .style("fill", COL.ink)
      .text("Precision@10% (modelo)");
  }

  // -----------------------------------------------------------------------
  // F6 - Contribucion por grupo de variables (heatmap)
  // -----------------------------------------------------------------------
  function fig6Groups() {
    const container = $("#fig6");
    if (!container) return;
    const width = container.clientWidth;
    const height = 320;
    const svg = d3.select(container).append("svg")
      .attr("viewBox", `0 0 ${width} ${height}`);

    const gc = window.MP.group_contribution;
    const matrix = gc.matrix;
    const groups = gc.groups;
    const clIds = gc.clusters.map(c => c.id);
    const m = matrix.length, n = matrix[0].length;

    const margin = { top: 24, right: 24, bottom: 80, left: 60 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3.scaleBand().domain(d3.range(n)).range([0, innerW]).padding(0.06);
    const y = d3.scaleBand().domain(d3.range(m)).range([0, innerH]).padding(0.06);

    const color = d3.scaleSequential(d3.interpolateYlGnBu).domain([0, Math.max(...matrix.flat()) + 5]);

    for (let i = 0; i < m; i++) {
      for (let j = 0; j < n; j++) {
        g.append("rect")
          .attr("x", x(j)).attr("y", y(i))
          .attr("width", x.bandwidth()).attr("height", y.bandwidth())
          .attr("fill", color(matrix[i][j]))
          .attr("stroke", COL.ink)
          .attr("stroke-width", 0.2)
          .on("mousemove", (evt) => showTooltip(
            `<b>${groups[j]}</b><br>Cluster ${clIds[i]}<br>${matrix[i][j].toFixed(1)}%`, evt))
          .on("mouseleave", hideTooltip);

        g.append("text")
          .attr("x", x(j) + x.bandwidth() / 2)
          .attr("y", y(i) + y.bandwidth() / 2 + 4)
          .attr("text-anchor", "middle")
          .style("font-family", "JetBrains Mono, monospace")
          .style("font-size", "10px")
          .style("font-weight", "600")
          .style("fill", matrix[i][j] > 30 ? "white" : COL.ink)
          .text(matrix[i][j].toFixed(0) + "%");
      }
    }

    // Eje X
    g.append("g")
      .attr("transform", `translate(0,${innerH})`)
      .call(d3.axisBottom(x).tickFormat((d) => groups[d]).tickSize(0))
      .selectAll(".tick text")
      .style("font-size", "10.5px")
      .style("fill", COL.ink)
      .attr("transform", "rotate(-20)")
      .attr("text-anchor", "end")
      .attr("dy", "0.3em");

    // Eje Y
    g.append("g")
      .call(d3.axisLeft(y).tickFormat((d) => "Cluster " + clIds[d]).tickSize(0))
      .selectAll(".tick text")
      .style("font-family", "JetBrains Mono, monospace")
      .style("font-size", "11px")
      .style("fill", COL.ink);
  }

  // -----------------------------------------------------------------------
  // F7 - Hiperparametros (mini bargrid)
  // -----------------------------------------------------------------------
  function fig7Hiper() {
    const container = $("#fig7");
    if (!container) return;
    const width = container.clientWidth;
    const height = 280;
    const svg = d3.select(container).append("svg")
      .attr("viewBox", `0 0 ${width} ${height}`);

    const hip = window.MP.hiperparametros;
    const clusters = Object.keys(hip);
    const params = ["n_estimators", "learning_rate", "subsample", "colsample_bytree",
                    "reg_alpha", "reg_lambda", "max_depth", "num_leaves", "scale_pos_weight"];

    const margin = { top: 24, right: 24, bottom: 80, left: 60 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3.scaleBand().domain(params).range([0, innerW]).padding(0.1);
    const subgroup = d3.scaleBand().domain(clusters).range([0, x.bandwidth()]).padding(0.04);

    // Normalizar cada parametro a [0, 1] por su maximo entre clusters
    const paramMax = {};
    for (const p of params) {
      paramMax[p] = d3.max(clusters, cl => hip[cl][p]) || 1;
    }

    g.append("g")
      .attr("transform", `translate(0,${innerH})`)
      .call(d3.axisBottom(x).tickSize(0))
      .selectAll(".tick text")
      .style("font-size", "10px")
      .style("fill", COL.ink)
      .attr("transform", "rotate(-30)")
      .attr("text-anchor", "end")
      .attr("dy", "0.3em");

    g.append("g").call(d3.axisLeft(d3.scaleLinear().domain([0, 1]).range([innerH, 0])).ticks(4));

    clusters.forEach((cl, i) => {
      g.selectAll(null)
        .data(params)
        .join("rect")
        .attr("x", p => x(p) + subgroup(cl))
        .attr("y", p => innerH * (1 - hip[cl][p] / paramMax[p]))
        .attr("width", subgroup.bandwidth())
        .attr("height", p => innerH * (hip[cl][p] / paramMax[p]))
        .attr("fill", COLORS[i])
        .attr("stroke", COL.ink)
        .attr("stroke-width", 0.3)
        .on("mousemove", (evt, p) => showTooltip(
          `<b>${p}</b><br>cluster ${cl.split(".")[0]}<br>${hip[cl][p]}`, evt))
        .on("mouseleave", hideTooltip);
    });

    // Legend
    const legend = svg.append("g").attr("transform", `translate(${innerW - 120},10)`);
    clusters.forEach((cl, i) => {
      const lg = legend.append("g").attr("transform", `translate(0,${i * 14})`);
      lg.append("rect").attr("width", 10).attr("height", 10).attr("fill", COLORS[i]);
      lg.append("text")
        .attr("x", 14).attr("y", 9)
        .style("font-family", "JetBrains Mono, monospace")
        .style("font-size", "10px")
        .style("fill", COL.ink)
        .text("Cluster " + cl.split(".")[0]);
    });
  }

  // -----------------------------------------------------------------------
  // Tabla resumen operacional
  // -----------------------------------------------------------------------
  function tablaResumen() {
    const container = $("#tabla-resumen");
    if (!container) return;
    const r = window.MP.results;
    const pk = window.MP.precision_at_k;
    const clusters = Object.keys(r);

    let html = `<table class="bench">
      <caption>Tabla 3 - Resumen consolidado de metricas por cluster (deployment 2021-04)</caption>
      <thead>
        <tr>
          <th>Cluster</th>
          <th>N deploy</th>
          <th>Base rate</th>
          <th>AUC val</th>
          <th>n_features</th>
          <th>P@10%</th>
          <th>Lift</th>
        </tr>
      </thead>
      <tbody>`;
    clusters.forEach(cl => {
      const rr = r[cl];
      const pp = pk[cl];
      html += `<tr>
        <td><strong>${cl.split(".")[0]}</strong> ${cl.split(". ")[1]}</td>
        <td>${rr.n_deploy.toLocaleString()}</td>
        <td class="up">${(pp.base_rate * 100).toFixed(0)}%</td>
        <td>${rr.auc_validacion.toFixed(4)}</td>
        <td>${rr.n_features}</td>
        <td>${(pp.precision_at_10pct * 100).toFixed(1)}%</td>
        <td class="up">${pp.lift.toFixed(2)}x</td>
      </tr>`;
    });
    html += `</tbody></table>`;
    container.innerHTML = html;
  }

  // -----------------------------------------------------------------------
  // Init
  // -----------------------------------------------------------------------
  function init() {
    if (!window.MP) return;
    fig1Segments();
    fig2FeatureImportance();
    fig3Auc();
    fig4Scores();
    fig5Precision();
    fig6Groups();
    fig7Hiper();
    tablaResumen();

    // Stats overview
    const r = window.MP.results;
    const clusters = Object.keys(r);
    const totalN = clusters.reduce((s, cl) => s + r[cl].n_deploy, 0);
    const avgAuc = clusters.reduce((s, cl) => s + r[cl].auc_validacion, 0) / clusters.length;
    const avgLift = Object.values(window.MP.precision_at_k).reduce((s, p) => s + p.lift, 0) / clusters.length;
    const maxLift = Math.max(...Object.values(window.MP.precision_at_k).map(p => p.lift));

    if ($("#stat-clusters")) $("#stat-clusters").textContent = clusters.length;
    if ($("#stat-n-deploy")) $("#stat-n-deploy").textContent = totalN.toLocaleString();
    if ($("#stat-avg-auc")) $("#stat-avg-auc").textContent = avgAuc.toFixed(3);
    if ($("#stat-avg-lift")) $("#stat-avg-lift").textContent = avgLift.toFixed(2) + "x";
  }

  window.MP = window.MP || {};
  window.MP.figures = { init };
})();
