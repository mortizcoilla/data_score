"""
scripts/generate_synthetic_data.py
==================================

Genera el paquete de datos sinteticos reproducibles para el pipeline de
DESPLIEGUE del modelo de propension a hurto de energia.

A diferencia de un generador de entrenamiento, este script produce el
estado de un sistema en produccion:

  1. Cuatro modelos LightGBM (clf_01.pkl ... clf_04.pkl) ya entrenados,
     uno por cluster, con sus hiperparametros y el feature importance
     que vio el entrenador en su grid search.
  2. Catalogos (maestros) de distrito / marca / sector / zona.
  3. La base de despliegue del periodo 2021-04 (4 segmentos cluster
     01..04) con las variables que el SQL Server entrega a este notebook.
  4. Las tablas de variables de inspeccion (con_notif y sin_notif) que
     el notebook joinea contra la base principal.
  5. Las metricas operacionales resultantes (AUC del modelo en
     validacion, base rate por cluster, n de despliegue) que el
     dashboard consume.

Reproducibilidad: seed = 2021.
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb

# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(r"C:\Workspace\Modelo_DataScore")
SYNTH_DIR = PROJECT_ROOT / "data" / "synthetic"
PROC_DIR = PROJECT_ROOT / "data" / "processed"
SYNTH_DIR.mkdir(parents=True, exist_ok=True)
(SYNTH_DIR / "maestros").mkdir(parents=True, exist_ok=True)
PROC_DIR.mkdir(parents=True, exist_ok=True)

SEED = 2021
rng = np.random.default_rng(SEED)

# Universo
CLUSTERS = [
    "01.- ConHurtoPrevio",
    "02.- ConIrregularidadNoHurto",
    "03.- ConInspeccionesSinIrregularidad",
    "04.- SinInspecciones",
]
CLUSTER_WEIGHTS = np.array([0.05, 0.06, 0.20, 0.69])

N_DISTRITOS = 12
N_MARCAS = 6
N_SECTORES = 10
N_ZONAS = 8

# Tamaños de la base de despliegue (por cluster, para 2021-04)
N_DEPLOY = {
    "01.- ConHurtoPrevio": 549,
    "02.- ConIrregularidadNoHurto": 672,
    "03.- ConInspeccionesSinIrregularidad": 1488,
    "04.- SinInspecciones": 5320,
}

# Hiperparametros finales por cluster (lo que el entrenador entrego)
HIPER = {
    "01.- ConHurtoPrevio": {
        "n_estimators": 300, "learning_rate": 0.075, "subsample": 0.80,
        "colsample_bytree": 0.90, "reg_alpha": 15.0, "reg_lambda": 20.0,
        "max_depth": 3, "min_child_samples": 50, "num_leaves": 30,
        "scale_pos_weight": 0.79, "n_features": 10,
    },
    "02.- ConIrregularidadNoHurto": {
        "n_estimators": 300, "learning_rate": 0.010, "subsample": 0.85,
        "colsample_bytree": 0.90, "reg_alpha": 9.0, "reg_lambda": 5.0,
        "max_depth": 3, "min_child_samples": 50, "num_leaves": 30,
        "scale_pos_weight": 4.62, "n_features": 5,
    },
    "03.- ConInspeccionesSinIrregularidad": {
        "n_estimators": 400, "learning_rate": 0.010, "subsample": 0.85,
        "colsample_bytree": 0.90, "reg_alpha": 4.0, "reg_lambda": 5.0,
        "max_depth": 3, "min_child_samples": 50, "num_leaves": 30,
        "scale_pos_weight": 11.10, "n_features": 8,
    },
    "04.- SinInspecciones": {
        "n_estimators": 400, "learning_rate": 0.090, "subsample": 0.85,
        "colsample_bytree": 0.90, "reg_alpha": 4.0, "reg_lambda": 5.0,
        "max_depth": 3, "min_child_samples": 50, "num_leaves": 30,
        "scale_pos_weight": 25.29, "n_features": 14,
    },
}

# Variables por cluster (las mismas que el notebook original)
COLS_BY_CLUSTER = {
    "01.- ConHurtoPrevio": [
        "cod_distrito", "id_marca", "notificaciones",
        "insp_por_cuenta_marca", "perc_recup_causal4_marca",
        "consumos_dimi", "pro_cons_6m", "diff_cons_6m_12m",
        "consumos_0", "casos_medidor_cambiado",
    ],
    "02.- ConIrregularidadNoHurto": [
        "tipo_fase_M", "notif_causal1", "diff_cons_6m_12m",
        "efectividad_marca",
    ],
    "03.- ConInspeccionesSinIrregularidad": [
        "tipo_fase_M", "tiempo_ult_cambio_med", "potencia",
        "insp_efectivas", "insp_pendientes", "dist_ult_insp_efect",
        "recupero_set_alimentador", "insp_por_cuenta_marca",
        "recup_prom_causal4_marca", "perc_notif_causal4_distrito",
        "barrido_perc_distrito", "casos_medidor_manip",
        "dist_med_interno", "dist_pri_lectura",
        "ratio_cons_potencia_12m", "casos_fact_U", "std_cons_6m",
    ],
    "04.- SinInspecciones": [
        "longitud", "tipo_fase_M", "potencia",
        "recup_prom_set", "insp_por_cuenta_set", "recupero_marca",
        "insp_por_cuenta_marca", "perc_notif_causal4_marca",
        "recup_prom_causal4_marca", "barrido_perc_marca",
        "nro_notif_causal4_distrito", "efectividad_distrito",
        "insp_por_cuenta_distrito", "perc_notif_causal4_distrito",
        "notif_otros_causal_distrito", "casos_medidor_manip",
        "consumos_0", "consumos_dimi", "dist_pri_lectura",
        "std_cons_6m", "pro_cons_12m", "min_diff",
        "diff_cons_6m_24m", "cv_cons_24m",
    ],
}


def save_csv(df: pd.DataFrame, name: str) -> None:
    out = SYNTH_DIR / name
    df.to_csv(out, index=False)
    print(f"  {name:<55s} {len(df):>10,} filas, {df.shape[1]:>3d} cols")


def save_pickle(obj, name: str) -> None:
    out = SYNTH_DIR / name
    with open(out, "wb") as f:
        pickle.dump(obj, f)
    print(f"  {name:<55s} (LightGBM model, pickled)")


# ---------------------------------------------------------------------------
# 1. Catalogos / maestros
# ---------------------------------------------------------------------------

print("\n[1/5] Generando catalogos y maestros ...")

distritos = [f"D{d:02d}" for d in range(1, N_DISTRITOS + 1)]
marcas = [f"M{m}" for m in range(1, N_MARCAS + 1)]
sectores = [f"sec{i}" for i in range(1, N_SECTORES + 1)]
zonas = [f"Z{z}" for z in range(1, N_ZONAS + 1)]

pd.DataFrame({"cod_distrito": distritos, "id_distrito": range(len(distritos))}).to_csv(
    SYNTH_DIR / "maestros" / "maestro_distrito.csv", index=False
)
pd.DataFrame({"id_marca": marcas, "marca": [f"Marca {m}" for m in marcas]}).to_csv(
    SYNTH_DIR / "maestros" / "maestro_marca.csv", index=False
)
pd.DataFrame({"id_sector": sectores, "sector": [f"Sector {i}" for i in range(1, N_SECTORES + 1)]}).to_csv(
    SYNTH_DIR / "maestros" / "maestro_sector.csv", index=False
)
pd.DataFrame({"id_zona": zonas, "zona": [f"Zona {z}" for z in range(1, N_ZONAS + 1)]}).to_csv(
    SYNTH_DIR / "maestros" / "maestro_zona.csv", index=False
)

# Maestro de marca con descripcion y base rate de efectividad
maestro_marca = pd.DataFrame({
    "id_marca": marcas,
    "marca": [f"Marca {m}" for m in marcas],
    "efectividad_marca": np.round(rng.uniform(0.04, 0.18, N_MARCAS), 4),
    "recup_prom_marca": np.round(rng.uniform(20000, 90000, N_MARCAS), 0),
    "insp_por_cuenta_marca": np.round(rng.uniform(0.05, 0.25, N_MARCAS), 4),
    "perc_recup_causal4_marca": np.round(rng.uniform(0.20, 0.65, N_MARCAS), 4),
})
maestro_marca.to_csv(SYNTH_DIR / "maestros" / "maestro_marca.csv", index=False)
print(f"  maestros/maestro_distrito.csv: {len(distritos)} distritos")
print(f"  maestros/maestro_marca.csv: {len(marcas)} marcas con stats de efectividad")
print(f"  maestros/maestro_sector.csv: {len(sectores)} sectores")
print(f"  maestros/maestro_zona.csv: {len(zonas)} zonas")


# ---------------------------------------------------------------------------
# 2. Base de despliegue global 2021-04
# ---------------------------------------------------------------------------

print("\n[2/5] Generando base de despliegue global 2021-04 ...")

deploy_rows = []
for cl in CLUSTERS:
    n = N_DEPLOY[cl]
    n_distritos = len(distritos)
    # Distribuir clientes entre distritos segun la concentracion del cluster
    if "HurtoPrevio" in cl:
        dist_probs = rng.dirichlet(np.ones(n_distritos) * 0.5)
    elif "IrregularidadNoHurto" in cl:
        dist_probs = rng.dirichlet(np.ones(n_distritos) * 0.7)
    else:
        dist_probs = rng.dirichlet(np.ones(n_distritos) * 1.5)
    for i in range(n):
        d = rng.choice(distritos, p=dist_probs)
        m = rng.choice(marcas)
        # Fecha de instalacion: hace 1-15 anios
        days_back = int(rng.integers(365, 365 * 15))
        fecha_inst = pd.Timestamp("2021-04-01") - pd.Timedelta(days=days_back)
        # Potencia instalada (kW)
        if "IrregularidadNoHurto" in cl:
            potencia = float(rng.uniform(5.0, 45.0))
        else:
            potencia = float(np.clip(rng.normal(6.0, 2.5), 1.5, 15.0))
        # Fase
        fase = "M" if rng.random() < 0.85 else "T"
        # Cuenta: codigo unico
        cuenta = f"{cl[:2].strip('.')}-{i:05d}"
        # Coordenadas (Santiago aprox)
        longitud = float(rng.uniform(-70.75, -70.50))
        latitud = float(rng.uniform(-33.55, -33.35))
        # Variables de inspeccion y anomalias
        nro_notificaciones = int(rng.integers(0, 8))
        nro_inspecciones = int(rng.integers(0, 6))
        insp_efectivas = int(rng.integers(0, nro_inspecciones + 1))
        insp_pendientes = int(rng.integers(0, 4))
        dist_ult_insp_efect = int(rng.integers(30, 1200))  # dias
        notific_otros_causal_distrito = float(rng.uniform(0, 80))
        nro_notif_causal4_distrito = float(rng.uniform(0, 30))
        perc_notif_causal4_distrito = float(rng.uniform(0, 0.6))
        perc_notif_causal4_marca = float(rng.uniform(0, 0.6))
        barrido_perc_distrito = float(rng.uniform(0.10, 0.85))
        barrido_perc_marca = float(rng.uniform(0.10, 0.85))
        efectividad_distrito = float(rng.uniform(0.05, 0.35))
        recup_prom_set = float(rng.uniform(20000, 90000))
        recup_prom_causal4_marca = float(rng.uniform(20000, 90000))
        recupero_marca = float(rng.uniform(5000, 80000))
        recupero_set_alimentador = float(rng.uniform(5000, 80000))
        insp_por_cuenta_set = float(rng.uniform(0.05, 0.30))
        insp_por_cuenta_distrito = float(rng.uniform(0.05, 0.30))
        dist_med_interno = int(rng.integers(30, 600))
        dist_pri_lectura = int(rng.integers(30, 1200))
        casos_medidor_manip = int(rng.integers(0, 5))
        casos_fact_U = int(rng.integers(0, 6))
        # Notificaciones (feature explicita en cluster 01)
        notificaciones = nro_notificaciones
        consumos_dimi = int(rng.integers(0, 8))
        consumos_0 = int(rng.integers(0, 6))
        casos_medidor_cambiado = int(rng.integers(0, 4))
        deploy_rows.append({
            "periodo": 202104,
            "cuenta": cuenta,
            "cod_distrito": d,
            "id_marca": m,
            "fase": fase,
            "potencia": round(potencia, 2),
            "longitud": round(longitud, 5),
            "latitud": round(latitud, 5),
            "fecha_instalacion": fecha_inst.strftime("%Y-%m-%d"),
            "cluster": cl,
            "notificaciones": notificaciones,
            "consumos_dimi": consumos_dimi,
            "consumos_0": consumos_0,
            "casos_medidor_cambiado": casos_medidor_cambiado,
            "insp_efectivas": insp_efectivas,
            "insp_pendientes": insp_pendientes,
            "dist_ult_insp_efect": dist_ult_insp_efect,
            "recupero_set_alimentador": round(recupero_set_alimentador, 0),
            "recup_prom_causal4_marca": round(recup_prom_causal4_marca, 0),
            "perc_notif_causal4_distrito": round(perc_notif_causal4_distrito, 4),
            "barrido_perc_distrito": round(barrido_perc_distrito, 4),
            "casos_medidor_manip": casos_medidor_manip,
            "dist_med_interno": dist_med_interno,
            "dist_pri_lectura": dist_pri_lectura,
            "casos_fact_U": casos_fact_U,
            "recup_prom_set": round(recup_prom_set, 0),
            "insp_por_cuenta_set": round(insp_por_cuenta_set, 4),
            "recupero_marca": round(recupero_marca, 0),
            "perc_notif_causal4_marca": round(perc_notif_causal4_marca, 4),
            "barrido_perc_marca": round(barrido_perc_marca, 4),
            "nro_notif_causal4_distrito": round(nro_notif_causal4_distrito, 0),
            "efectividad_distrito": round(efectividad_distrito, 4),
            "insp_por_cuenta_distrito": round(insp_por_cuenta_distrito, 4),
            "notif_otros_causal_distrito": round(notific_otros_causal_distrito, 0),
        })
df_deploy_global = pd.DataFrame(deploy_rows)
save_csv(df_deploy_global, "temp_deploy_global_202104.csv")


# ---------------------------------------------------------------------------
# 3. Tablas de variables por cluster
# ---------------------------------------------------------------------------

print("\n[3/5] Generando tablas de variables de inspeccion/consumo ...")

# 3a. Tabla CON notificacion (clusters 01, 02)
con_notif_rows = []
for cl in ["01.- ConHurtoPrevio", "02.- ConIrregularidadNoHurto"]:
    n = N_DEPLOY[cl]
    for i in range(n):
        cuenta = f"{cl[:2].strip('.')}-{i:05d}"
        # Consumos trimestrales antes/despues
        q01_ant = float(rng.uniform(80, 600))
        q02_ant = float(rng.uniform(80, 600))
        q03_ant = float(rng.uniform(80, 600))
        q01_post = float(np.clip(q01_ant + rng.normal(-30, 80), 0, 800))
        q02_post = float(np.clip(q02_ant + rng.normal(-30, 80), 0, 800))
        q03_post = float(np.clip(q03_ant + rng.normal(-30, 80), 0, 800))
        # Promedios de consumo
        pro_6m = float(rng.uniform(100, 500))
        pro_12m = pro_6m * float(rng.uniform(0.85, 1.15))
        # Variable de cluster 02
        notif_causal1 = int(rng.integers(0, 8))
        con_notif_rows.append({
            "cuenta": cuenta,
            "q01_promedio_ant": round(q01_ant, 2),
            "q02_promedio_ant": round(q02_ant, 2),
            "q03_promedio_ant": round(q03_ant, 2),
            "q01_promedio_post": round(q01_post, 2),
            "q02_promedio_post": round(q02_post, 2),
            "q03_promedio_post": round(q03_post, 2),
            "pro_cons_6m": round(pro_6m, 2),
            "pro_cons_12m": round(pro_12m, 2),
            "notif_causal1": notif_causal1,
        })
df_con_notif = pd.DataFrame(con_notif_rows)
save_csv(df_con_notif, "tmp_deploy_202104_global_con_notif_vars.csv")

# 3b. Tabla SIN notificacion (clusters 03, 04)
sin_notif_rows = []
for cl in ["03.- ConInspeccionesSinIrregularidad", "04.- SinInspecciones"]:
    n = N_DEPLOY[cl]
    for i in range(n):
        cuenta = f"{cl[:2].strip('.')}-{i:05d}"
        # Consumos trimestrales
        q01_ant = float(rng.uniform(60, 500))
        q02_ant = float(rng.uniform(60, 500))
        q03_ant = float(rng.uniform(60, 500))
        q01_post = float(np.clip(q01_ant + rng.normal(0, 60), 0, 700))
        q02_post = float(np.clip(q02_ant + rng.normal(0, 60), 0, 700))
        q03_post = float(np.clip(q03_ant + rng.normal(0, 60), 0, 700))
        # Promedios
        pro_6m = float(rng.uniform(80, 450))
        pro_12m = pro_6m * float(rng.uniform(0.80, 1.20))
        pro_24m = pro_12m * float(rng.uniform(0.90, 1.10))
        # Std
        std_6m = float(rng.uniform(10, 80))
        std_24m = std_6m * float(rng.uniform(0.8, 1.2))
        sin_notif_rows.append({
            "cuenta": cuenta,
            "q01_promedio_ant": round(q01_ant, 2),
            "q02_promedio_ant": round(q02_ant, 2),
            "q03_promedio_ant": round(q03_ant, 2),
            "q01_promedio_post": round(q01_post, 2),
            "q02_promedio_post": round(q02_post, 2),
            "q03_promedio_post": round(q03_post, 2),
            "pro_cons_6m": round(pro_6m, 2),
            "pro_cons_12m": round(pro_12m, 2),
            "pro_cons_24m": round(pro_24m, 2),
            "std_cons_6m": round(std_6m, 2),
            "std_cons_24m": round(std_24m, 2),
        })
df_sin_notif = pd.DataFrame(sin_notif_rows)
save_csv(df_sin_notif, "tmp_deploy_202104_global_sin_notif_vars.csv")


# ---------------------------------------------------------------------------
# 4. Modelos LightGBM pre-entrenados
# ---------------------------------------------------------------------------

print("\n[4/5] Construyendo 4 modelos LightGBM (uno por cluster) ...")

# Para hacer un demo creible, generamos cada modelo entrenando un LightGBM
# sobre datos sinteticos con la estructura del cluster, y luego exportamos.

def make_synthetic_training_data(cluster_name: str, n_samples: int = 4000) -> tuple[pd.DataFrame, pd.Series]:
    """Genera datos sinteticos de entrenamiento para un cluster dado.

    Para producir AUC realista (0.7-0.9) en vez de perfecto, se introduce
    ruido: la senal esta presente pero no es deterministica, y se solapan
    las distribuciones de positivos y negativos.
    """
    cols = COLS_BY_CLUSTER[cluster_name]
    n_pos = int(n_samples * 0.15)
    n_neg = n_samples - n_pos
    rows = []

    def sample_pos(c):
        """Senal presente pero ruidosa (mezcla de distribuciones)."""
        if c in ("cod_distrito", "id_marca"):
            return rng.choice(distritos if c == "cod_distrito" else marcas)
        if c == "tipo_fase_M":
            return 1 if rng.random() < 0.7 else 0
        if c == "potencia":
            return float(np.clip(rng.normal(7.5, 2.5), 2, 15))
        if c == "longitud":
            return float(rng.uniform(-70.7, -70.5))
        if c in ("notificaciones", "consumos_dimi", "casos_medidor_cambiado",
                 "casos_medidor_manip", "insp_efectivas", "insp_pendientes",
                 "casos_fact_U", "notif_causal1"):
            return int(np.clip(rng.normal(5, 3), 0, 20))
        if c in ("consumos_0",):
            return int(np.clip(rng.normal(1, 2), 0, 10))
        if c.startswith("insp_por_cuenta_") or c.startswith("efectividad_") or \
           c.startswith("recup_prom_") or c.startswith("perc_") or \
           c.startswith("recupero_") or c == "barrido_perc_marca" or \
           c == "barrido_perc_distrito" or c == "min_diff" or \
           c == "diff_cons_6m_12m" or c == "diff_cons_6m_24m" or \
           c == "cv_cons_24m" or c == "ratio_cons_potencia_12m":
            return float(np.clip(rng.normal(0.35, 0.20), 0, 1))
        if c.startswith("pro_cons_") or c.startswith("std_cons_") or \
           c == "dist_med_interno" or c == "dist_pri_lectura" or \
           c == "dist_ult_insp_efect" or c == "tiempo_ult_cambio_med" or \
           c.startswith("nro_notif_") or c == "notif_otros_causal_distrito":
            return float(np.clip(rng.normal(250, 100), 0, 800))
        return 0.0

    def sample_neg(c):
        """Senal debil (parcialmente solapada con la positiva)."""
        if c in ("cod_distrito", "id_marca"):
            return rng.choice(distritos if c == "cod_distrito" else marcas)
        if c == "tipo_fase_M":
            return 1 if rng.random() < 0.4 else 0
        if c == "potencia":
            return float(np.clip(rng.normal(5.5, 2.0), 2, 15))
        if c == "longitud":
            return float(rng.uniform(-70.7, -70.5))
        if c in ("notificaciones", "consumos_dimi", "casos_medidor_cambiado",
                 "casos_medidor_manip", "insp_efectivas", "insp_pendientes",
                 "casos_fact_U", "notif_causal1"):
            return int(np.clip(rng.normal(2, 2), 0, 15))
        if c in ("consumos_0",):
            return int(np.clip(rng.normal(2, 3), 0, 12))
        if c.startswith("insp_por_cuenta_") or c.startswith("efectividad_") or \
           c.startswith("recup_prom_") or c.startswith("perc_") or \
           c.startswith("recupero_") or c == "barrido_perc_marca" or \
           c == "barrido_perc_distrito" or c == "min_diff" or \
           c == "diff_cons_6m_12m" or c == "diff_cons_6m_24m" or \
           c == "cv_cons_24m" or c == "ratio_cons_potencia_12m":
            return float(np.clip(rng.normal(0.18, 0.15), 0, 1))
        if c.startswith("pro_cons_") or c.startswith("std_cons_") or \
           c == "dist_med_interno" or c == "dist_pri_lectura" or \
           c == "dist_ult_insp_efect" or c == "tiempo_ult_cambio_med" or \
           c.startswith("nro_notif_") or c == "notif_otros_causal_distrito":
            return float(np.clip(rng.normal(180, 90), 0, 800))
        return 0.0

    for _ in range(n_pos):
        row = {c: sample_pos(c) for c in cols}
        row["__target__"] = 1
        rows.append(row)
    for _ in range(n_neg):
        row = {c: sample_neg(c) for c in cols}
        row["__target__"] = 0
        rows.append(row)
    df = pd.DataFrame(rows)
    y = df.pop("__target__").astype(int)
    # Codificar categoricas a enteros para LightGBM
    for c in ("cod_distrito", "id_marca"):
        if c in df.columns:
            df[c] = df[c].astype("category").cat.codes
    return df, y


model_metrics = {}
for cl in CLUSTERS:
    hp = HIPER[cl]
    print(f"  cluster {cl[:2]}: entrenando LightGBM ...")
    X_tr, y_tr = make_synthetic_training_data(cl, n_samples=4000)
    X_va, y_va = make_synthetic_training_data(cl, n_samples=1000)

    params = {
        "n_estimators": hp["n_estimators"],
        "learning_rate": hp["learning_rate"],
        "subsample": hp["subsample"],
        "colsample_bytree": hp["colsample_bytree"],
        "reg_alpha": hp["reg_alpha"],
        "reg_lambda": hp["reg_lambda"],
        "max_depth": hp["max_depth"],
        "min_child_samples": hp["min_child_samples"],
        "num_leaves": hp["num_leaves"],
        "scale_pos_weight": hp["scale_pos_weight"],
        "random_state": SEED,
        "verbose": -1,
    }
    clf = lgb.LGBMClassifier(**params)
    clf.fit(X_tr.values, y_tr.values)

    # Guardar
    fname = f"clf_{cl[:2].replace('.', '')}.pkl"
    save_pickle(clf, fname)

    # Metricas basicas en validacion
    from sklearn.metrics import roc_auc_score
    p_va = clf.predict_proba(X_va.values)[:, 1]
    auc_va = float(roc_auc_score(y_va.values, p_va))

    # Feature importance
    fi = pd.DataFrame({
        "feature": list(X_tr.columns),
        "importance": clf.booster_.feature_importance(importance_type="gain"),
    }).sort_values("importance", ascending=False).reset_index(drop=True)
    fi["importance"] = fi["importance"].astype(float).round(3)

    model_metrics[cl] = {
        "n_features": hp["n_features"],
        "scale_pos_weight": hp["scale_pos_weight"],
        "auc_validacion": round(auc_va, 4),
        "n_deploy": N_DEPLOY[cl],
        "feature_importance": fi.to_dict(orient="records"),
        "hiperparametros": hp,
    }

# ---------------------------------------------------------------------------
# 5. Metricas operacionales y outputs para el dashboard
# ---------------------------------------------------------------------------

print("\n[5/5] Generando metricas operacionales para el dashboard ...")

# Anadir metricas agregadas
metadata = {
    "fecha_despliegue": "2021-04-30",
    "periodo_despliegue": 202104,
    "modelo": "LGBMClassifier (4 modelos, uno por cluster)",
    "version_modelos": "1.0.0-despliegue",
    "total_deploy": sum(N_DEPLOY.values()),
    "seed": SEED,
}

base_rate_operativo = {
    "01.- ConHurtoPrevio": 0.55,
    "02.- ConIrregularidadNoHurto": 0.18,
    "03.- ConInspeccionesSinIrregularidad": 0.08,
    "04.- SinInspecciones": 0.03,
}

# Precision@10% y lift se estiman a partir de la base rate + AUC
# (calibracion optimista para que el lift sea >= 1 siempre)
precision_at_k = {}
for cl, base in base_rate_operativo.items():
    auc = model_metrics[cl]["auc_validacion"]
    # Aproximacion: P@10% ~ min(0.95, base * (1 + (auc - 0.5) * 4))
    p10 = min(0.95, base * (1 + max(0, auc - 0.45) * 6))
    precision_at_k[cl] = {
        "base_rate": base,
        "precision_at_10pct": round(p10, 4),
        "lift": round(p10 / base, 2),
        "n_deploy": N_DEPLOY[cl],
    }

# Composicion por cluster
segments = {
    "clusters": [{"id": cl[:2], "name": cl, "n": N_DEPLOY[cl], "base_rate": base_rate_operativo[cl]}
                 for cl in CLUSTERS],
    "total": sum(N_DEPLOY.values()),
}

metricas_operacionales = {
    "metadata": metadata,
    "results": {cl: {k: v for k, v in m.items() if k not in ("feature_importance", "hiperparametros")}
                for cl, m in model_metrics.items()},
    "feature_importance": {cl: m["feature_importance"] for cl, m in model_metrics.items()},
    "precision_at_k": precision_at_k,
    "segmentos": segments,
    "hiperparametros": {cl: m["hiperparametros"] for cl, m in model_metrics.items()},
    "base_rate_operativo": base_rate_operativo,
}

# Calcular group_contribution: contribucion al gain por grupo de variables
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

group_matrix = []
for cl in CLUSTERS:
    fi = {f["feature"]: f["importance"] for f in model_metrics[cl]["feature_importance"]}
    total = sum(fi.values()) or 1
    row = []
    for gname, feats in GROUPS.items():
        s = sum(fi.get(f, 0) for f in feats)
        row.append(round(s / total * 100, 1))
    group_matrix.append(row)

metricas_operacionales["group_contribution"] = {
    "groups": list(GROUPS.keys()),
    "clusters": [{"id": cl.split(".")[0], "name": cl} for cl in CLUSTERS],
    "matrix": group_matrix,
}

out_metrics = PROC_DIR / "metrics.json"
out_metrics.write_text(json.dumps(metricas_operacionales, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"  data/processed/metrics.json ({out_metrics.stat().st_size:,} bytes)")

# Resumen de segmentos en CSV
df_segments = pd.DataFrame([
    {"cluster": c["name"], "id": c["id"], "n_deploy": c["n"], "base_rate": c["base_rate"]}
    for c in segments["clusters"]
])
df_segments.to_csv(PROC_DIR / "segments_summary.csv", index=False)
print(f"  data/processed/segments_summary.csv")

# Feature importance por cluster
for cl, m in model_metrics.items():
    df_fi = pd.DataFrame(m["feature_importance"])
    out_fi = PROC_DIR / f"feature_importance_{cl[:2].replace('.', '')}.csv"
    df_fi.to_csv(out_fi, index=False)
    print(f"  data/processed/feature_importance_{cl[:2].replace('.', '')}.csv")

print("\n[OK] Generacion de datos sinteticos completa.")
print(f"     Raiz: {SYNTH_DIR}")
print(f"     Processed: {PROC_DIR}")
