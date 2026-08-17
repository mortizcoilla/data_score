# Despliegue de Score de DataMining - Working paper

> **Miguel Ortiz C.** - Julio 2026 - Working paper
> Repositorio: [github.com/mortizcoilla/portfolio]

---

## Descripcion

Pipeline reproducible para el **despliegue mensual** del modelo de propension a hurto de energia en Enel Distribucion Chile, con cuatro modelos LightGBM (uno por cluster de historial del cliente) y 8 029 cuentas-periodo procesadas en la corrida de 2021-04.

Este es el **working paper companero** del paper de modelamiento. Mientras el paper companero documenta como se entrenaron los cuatro modelos, este paper se enfoca en como se llevan a produccion: contrato de features, segmentacion al momento del scoring, y verificacion automatica antes de marcar el periodo como completado.

El proyecto entrega tres artefactos:

1. **Working paper** (`docs/paper1_despliegue_datamining.{md,docx}`) - paper academico con IMRyD, 8 figuras y referencias.
2. **Dashboard HTML** (`index.html` + `css/` + `js/`) - companion interactivo con D3.js v7 y datos embebidos.
3. **Jupyter notebook** (`notebooks/Despliegue_Score_DataMining.ipynb`) - pipeline ejecutable end-to-end con markdown explicativo.

Los datos son **sinteticos reproducibles** (seed = 2021), generados por `scripts/generate_synthetic_data.py`. La estructura, distribuciones y correlaciones son fiel reflejo del trabajo original realizado en Enel Distribucion Chile, sin contener datos personales ni informacion operacional real.

---

## Estructura del proyecto

```
Modelo_DataScore/
├── README.md
├── index.html                       # dashboard interactivo (entry point)
├── docs/
│   ├── paper1_despliegue_datamining.md   # paper markdown
│   ├── paper1_despliegue_datamining.docx # paper Word (con figuras)
│   └── figures/                          # 8 figuras PNG del paper
├── data/
│   ├── synthetic/                    # datos sinteticos reproducibles (seed=2021)
│   │   ├── temp_deploy_global_202104.csv
│   │   ├── tmp_deploy_202104_global_con_notif_vars.csv
│   │   ├── tmp_deploy_202104_global_sin_notif_vars.csv
│   │   ├── clf_01.pkl ... clf_04.pkl   # 4 modelos LightGBM pre-entrenados
│   │   └── maestros/maestro_marca.csv
│   └── processed/                    # outputs del cuaderno
│       ├── scores_202104_global.csv      # tabla operacional
│       ├── deploy_summary_202104.csv     # resumen por cluster
│       ├── metrics.json                  # metricas para el dashboard
│       └── feature_importance_*.csv
├── scripts/
│   ├── generate_synthetic_data.py    # generador de datos + modelos
│   ├── build_notebook.py             # regenera el cuaderno .ipynb
│   ├── build_data.py                 # genera js/data.js desde metrics.json
│   ├── figures_paper.py              # genera las 8 figuras del paper
│   └── md_to_docx.py                 # convierte paper.md -> paper.docx
├── notebooks/
│   ├── Despliegue_Score_DataMining.ipynb         # cuaderno ejecutable
│   └── Despliegue_Score_DataMining_executed.ipynb # cuaderno ejecutado
├── css/
│   └── styles.css                    # estilos del dashboard
└── js/
    ├── data.js                       # datos embebidos (generado)
    ├── figures.js                    # figuras D3 v7
    └── main.js                       # bootstrap
```

---

## Quickstart

### 1. Generar datos sinteticos

```bash
python scripts/generate_synthetic_data.py
```

Genera 4 modelos LightGBM pickle (uno por cluster) y las bases de despliegue en `data/synthetic/` (~5 MB total, seed = 2021).

### 2. Ejecutar el cuaderno de despliegue

```bash
python -c "import nbformat; from nbclient import NotebookClient; \
  nb = nbformat.read('notebooks/Despliegue_Score_DataMining.ipynb', as_version=4); \
  client = NotebookClient(nb, timeout=180, kernel_name='python3'); \
  client.execute(); \
  nbformat.write(nb, 'notebooks/Despliegue_Score_DataMining_executed.ipynb')"
```

Tiempo: ~30 segundos. Genera:
- `data/processed/scores_202104_global.csv` con 8 029 scores
- `data/processed/deploy_summary_202104.csv` con metricas por cluster
- `docs/figures/fig7_score_distributions.png` (figura del cuaderno)

### 3. Generar las figuras del paper

```bash
python scripts/figures_paper.py
```

Genera 8 figuras PNG en `docs/figures/` (composicion, feature importance, AUC, scores, grupos, ROC, hiperparametros, tabla resumen).

### 4. Construir el JSON embebido del dashboard

```bash
python scripts/build_data.py
```

Genera `js/data.js` (~11 KB) con los datos del dashboard.

### 5. Convertir el paper a Word

```bash
python scripts/md_to_docx.py
```

Genera `docs/paper1_despliegue_datamining.docx` (~620 KB) con todas las figuras embebidas.

### 6. Servir el dashboard

```bash
python -m http.server 8000
```

Abrir <http://localhost:8000> en el navegador.

---

## Resultados principales

El cuaderno produce la tabla operacional `scores_202104_global` con 8 029 cuentas-periodo y la distribucion de scores por cluster:

| Cluster | N deploy | Score medio | Score p90 | Score max |
|---|---:|---:|---:|---:|
| 01 ConHurtoPrevio | 549 | 0.30 | 0.77 | 0.96 |
| 02 ConIrreg.NoHurto | 672 | 0.50 | 0.81 | 0.86 |
| 03 ConInsp.SinIrreg. | 1 488 | 0.71 | 0.94 | 0.95 |
| 04 SinInspecciones | 5 320 | 0.75 | 0.99 | 1.00 |

| Cluster | Base rate | AUC val | P@10% | Lift |
|---|---:|---:|---:|---:|
| 01 ConHurtoPrevio | 0.55 | 0.98 | 0.61 | 1.1x |
| 02 ConIrreg.NoHurto | 0.18 | 0.94 | 0.22 | 1.3x |
| 03 ConInsp.SinIrreg. | 0.08 | 0.99 | 0.09 | 1.2x |
| 04 SinInspecciones | 0.04 | 0.99 | 0.04 | 1.1x |

> **En datos operacionales reales** (no incluidos por privacidad) el AUC out-of-time es 0.70-0.80 y el lift operacional 1.7x-4.5x. La metodologia y el codigo son los mismos.

---

## Diseno del despliegue

### Segmentacion

La base se divide en cuatro clusters segun el historial del cliente, replicando la segmentacion del paper de modelamiento:

| Cluster | Descripcion | Base rate | n_features |
|---|---|---:|---:|
| 01 | ConHurtoPrevio (notificacion previa por hurto) | ~55% | 10 |
| 02 | ConIrregularidadNoHurto (notificacion previa, no hurto) | ~18% | 4 |
| 03 | ConInspeccionesSinIrregularidad (inspeccionado, sin irregularidad) | ~8% | 17 |
| 04 | SinInspecciones (nunca inspeccionado) | ~3% | 24 |

La varianza de la base rate entre clusters es de un orden de magnitud. Un modelo global comprime la senal a la media; un modelo por cluster preserva la heterogeneidad.

### Contrato de features

El cuaderno verifica el contrato de features al inicio con asserts automaticos:

```python
assert clf_01.n_features_ == len(cols_sel_01), f'clf_01: {clf_01.n_features_} vs {len(cols_sel_01)}'
```

Si el modelo espera 10 features y la lista de despliegue tiene 11, el assert falla y la corrida se aborta antes de producir scores. Esto evita scores invalidos silenciosos por desalineacion entre entrenamiento y despliegue.

### Conversion de categoricas

LightGBM no acepta strings ni `category` dtype directamente. El cuaderno aplica `pd.factorize` antes de `predict_proba`:

```python
for X in [X_dep_global_202104_01, X_dep_global_202104_02,
          X_dep_global_202104_03, X_dep_global_202104_04]:
    for c in ('cod_distrito', 'id_marca'):
        if c in X.columns:
            X[c] = pd.factorize(X[c])[0]
```

---

## Variables

10, 4, 17 y 24 features por cluster, distribuidas en cinco grupos. El detalle completo esta en el paper.

| Grupo | Ejemplos |
|---|---|
| Cliente | `tipo_fase_M`, `potencia`, `tiempo_ult_cambio_med`, `longitud` |
| Inspeccion | `notificaciones`, `notif_causal1`, `insp_efectivas`, `insp_pendientes`, `dist_ult_insp_efect` |
| Contexto red | `insp_por_cuenta_marca`, `efectividad_marca`, `recup_prom_set`, `barrido_perc_marca` |
| Consumo | `pro_cons_6m`, `pro_cons_12m`, `std_cons_6m`, `diff_cons_6m_12m`, `cv_cons_24m` |
| Anomalias medidor | `consumos_dimi`, `consumos_0`, `casos_medidor_manip`, `casos_fact_U` |

---

## Stack tecnologico

- **Python** 3.11+ - pandas, numpy, scikit-learn, lightgbm, matplotlib
- **D3.js v7** via CDN (sin build step)
- **Jupyter** notebook (ejecutado con nbclient)
- **python-docx** para el paper en formato Word
- Sin frameworks de UI (vanilla JS + HTML + CSS)

---

## Limitaciones

- **Datos sinteticos.** Los resultados cuantitativos son ilustrativos; las metricas reales son mejores.
- **El cuaderno no reentrena.** Este paper cubre la fase de despliegue, no la de reentrenamiento.
- **El scoring es por cluster independiente.** Los scores no son comparables entre clusters (cluster 04 con score 0.7 no es lo mismo que cluster 01 con score 0.7).
- **Las categoricas se factorizan con `pd.factorize`**, no con un encoder entrenado. En produccion, el encoder debe entrenarse con la base completa y guardarse para estabilidad entre periodos.

---

## Autor

Miguel Ortiz C. - Working paper, Julio 2026.

Contacto: <mortizcoilla@gmail.com> - LinkedIn: <linkedin.com/in/mortizcoilla> - WhatsApp: <wa.me/56933293943>
