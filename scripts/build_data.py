"""
scripts/build_data.py
=====================

Genera js/data.js (datos embebidos para el dashboard HTML) desde
data/processed/metrics.json. Solo incluye los datos necesarios para
las visualizaciones (no las listas grandes de y_pred_*).

Uso:
    python scripts/build_data.py
"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Workspace\Modelo_DataScore")
PROC_DIR = PROJECT_ROOT / "data" / "processed"
JS_DIR = PROJECT_ROOT / "js"
JS_DIR.mkdir(parents=True, exist_ok=True)

src = json.loads((PROC_DIR / "metrics.json").read_text(encoding="utf-8"))

# Limpiar el JSON para el dashboard
data = {
    "metadata": src["metadata"],
    "segmentos": src["segmentos"],
    "results": src["results"],
    "precision_at_k": src["precision_at_k"],
    "feature_importance": src["feature_importance"],
    "hiperparametros": src["hiperparametros"],
    "base_rate_operativo": src["base_rate_operativo"],
}

# Variable groups para la figura de contribucion por grupo
GROUPS = {
    "Cliente": ["tipo_fase_M", "potencia", "tiempo_ult_cambio_med", "longitud"],
    "Inspeccion": ["notificaciones", "notif_causal1", "insp_efectivas",
                   "insp_pendientes", "dist_ult_insp_efect"],
    "Contexto red": ["insp_por_cuenta_marca", "efectividad_marca",
                     "perc_recup_causal4_marca", "recup_prom_causal4_marca",
                     "efectividad_distrito", "recup_prom_set",
                     "insp_por_cuenta_set", "recupero_marca",
                     "perc_notif_causal4_marca", "barrido_perc_marca",
                     "nro_notif_causal4_distrito", "insp_por_cuenta_distrito",
                     "perc_notif_causal4_distrito", "notif_otros_causal_distrito",
                     "barrido_perc_distrito", "recupero_set_alimentador"],
    "Consumo": ["pro_cons_6m", "pro_cons_12m", "std_cons_6m",
                "diff_cons_6m_12m", "min_diff", "diff_cons_6m_24m",
                "cv_cons_24m", "ratio_cons_potencia_12m"],
    "Anomalias medidor": ["consumos_dimi", "consumos_0",
                          "casos_medidor_cambiado", "casos_medidor_manip",
                          "casos_fact_U", "dist_med_interno", "dist_pri_lectura"],
}
data["groups"] = GROUPS

# Construir matriz de contribucion por grupo y cluster
clusters = list(data["results"].keys())
matrix = []
for cl in clusters:
    fi = {f["feature"]: f["importance"] for f in data["feature_importance"][cl]}
    total = sum(fi.values()) or 1
    row = []
    for gname, feats in GROUPS.items():
        s = sum(fi.get(f, 0) for f in feats)
        row.append(round(s / total * 100, 1))
    matrix.append(row)
data["group_contribution"] = {
    "groups": list(GROUPS.keys()),
    "clusters": [{"id": cl.split(".")[0], "name": cl} for cl in clusters],
    "matrix": matrix,
}

# Generar data.js con IIFE
out = JS_DIR / "data.js"
js_content = (
    "/**\n"
    " * js/data.js\n"
    " * Datos embebidos para el dashboard HTML del modelo de propension.\n"
    " * Generado por scripts/build_data.py desde data/processed/metrics.json.\n"
    " */\n"
    "(function () {\n"
    "  'use strict';\n"
    f"  window.MP = {json.dumps(data, indent=2, ensure_ascii=False)};\n"
    "})();\n"
)
out.write_text(js_content, encoding="utf-8")
print(f"OK {out} ({out.stat().st_size:,} bytes)")
