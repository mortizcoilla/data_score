# 10 ideas de proyectos de Data Science para el sector eléctrico chileno - 2026

> **Working notes**
> Miguel Ortiz C. - Julio 2026
> Continuacion de los modelos de propension y score de despliegue en Enel Distribucion Chile

---

## Resumen ejecutivo

Este documento propone 10 ideas de proyectos de Data Science para el sector eléctrico chileno, alineados con los modelos de propension y score ya desarrollados en Enel Distribucion (modelo de hurto, modelo de propension por cluster, modelo de despliegue mensual). Cada idea se evalua con cuatro criterios:

1. **Tamano del mercado / impacto potencial** (cifras concretas 2025-2026)
2. **Disponibilidad de datos** en la distribuidora
3. **Tendencia regulatoria o de mercado** que impulse la adopcion
4. **Reutilizacion de infraestructura tecnica** del proyecto existente (4 LightGBM segmentados, pipeline de despliegue, dashboard)

Los proyectos estan ordenados por **potencial economico decreciente** (no por facilidad tecnica). Para cada uno se estima el orden de magnitud del valor economico anual capturable por la distribuidora, en CLP y USD.

**Hallazgo principal:** los cinco primeros proyectos tienen cada uno un potencial economico anual superior a USD 5 millones para una distribuidora del tamano de Enel Distribucion (zona central de Santiago, ~1,9 millones de clientes). El top 3 (fraude PMGD, mantenimiento predictivo de transformadores y pronostico de demanda) suma mas de USD 25 millones al ano en valor capturable.

---

## Contexto: el sector eléctrico chileno en 2026

Antes de presentar las ideas, resumo las seis megatendencias que dan forma a las oportunidades de Data Science en distribucion electrica en Chile 2026.

### 1. Las perdidas no tecnicas (NTL) son un problema estructural, no resuelto

- Enel Distribucion Chile reporto 5,79% de perdidas de energia en 2024 y 5,8% a marzo 2025 (Memoria Integrada Enel Chile 2024; CMF 2025).
- La estrategia corporativa 2026-2028 apunta a reducir las network losses de 6,0% (2025) a 5,7% proyectado (Enel Chile FY 2025 Results & Strategic Plan 2026-28).
- Cada punto porcentual de mejora en NTL representa ~USD 8-12 millones al ano en energia recuperada para una distribuidora del tamano de Enel (1,9 millones de clientes, 18.000 GWh vendidos al ano).
- La Ley 21.340 (2021) congela el corte de servicio por mora, lo que cambia la naturaleza del fraude: ya no es solo hurto, tambien es impago formalizado.

### 2. El PMGD (paneles solares) esta en auge explosivo

- 3.908 MW de PMGD instalados a diciembre 2025 (10% de la capacidad del sistema electrico nacional) - ACESOL 2025.
- 27.230 instalaciones solares residenciales bajo Netbilling a diciembre 2024; +5.479 nuevas en 2025 - Plataforma Transicion Energetica.
- Crecimiento CAGR del 92% del 2015 al 2024 en instalaciones Netbilling.
- Netbilling +54% en 2025 vs 2024.
- Pipeline de 9,4 GW en construccion, 52,7% solar fotovoltaico.
- **Implicacion:** cada nuevo PMGD es un punto de medicion bidireccional, un cliente con capacidad de fraude por inyeccion no registrada, y una fuente de intermitencia que requiere pronostico.

### 3. La electromovilidad acelera la carga residencial

- Chile cerro 2025 con 310.000 vehiculos vendidos; 2,8% enchufables, 11,4% considerando hibridos - ANAC 2025.
- Proyeccion ANAC 2026: 3,8% BEV+PHEV (12.000 unidades), 16,8% cero y bajas emisiones.
- Primer semestre 2026: 7.802 enchufables vendidos, +162,9% vs mismo periodo 2025 - BCN 2026.
- Meta oficial: 100% cero emisiones en ventas nuevas para 2035.
- **Implicacion:** un auto electrico carga entre 3,7 y 22 kW; la penetracion residencial va a estresar transformadores de distribucion. La distribuidora necesita modelos de adopcion por zona para dimensionar red.

### 4. La calidad de servicio (SAIDI/SAIFI) esta en zona critica

- 2024 fue el peor ano desde 2017: SAIDI nacional 27,59 horas por cliente (record historico) - En Cancha 2025.
- Enel Distribucion: 150 min en 2024, 167 min en 2025 (empeorando 11%) - Memoria Integrada Enel 2024.
- El 60% de los minutos de SAIDI son por causas internas (responsabilidad de la distribuidora).
- Limites 2026+ son mas estrictos: SAIFI 3,5 a 6,5 segun densidad de red (CNE NTCSDx2024).
- Cada hora de interrupcion no autorizada genera compensacion al usuario equivalente al duplo del valor de la energia no suministrada.
- **Implicacion:** reducir SAIDI en 10% es material; predecir fallas es la palanca de mayor impacto en millones de dolares al ano.

### 5. La morosidad esta en maximo historico

- 720.840 clientes morosos en mayo 2025 (10,1% del total) - La Tercera 2025.
- Deuda morosa total: $248.512 millones CLP (marzo 2025), $860 mil millones (marzo 2026, 23% mas por interes del Estado) - CIPER 2026.
- El 33% de los clientes morosos concentra el 57% de la deuda.
- Enel Distribución y CGE concentran la mayor parte de los 5,86 millones de clientes residenciales con deuda.
- **Implicacion:** un modelo de scoring de morosidad permite focalizar cobranza y prevenir cortes (politicamente sensibles).

### 6. La regulacion tarifaria se moderniza

- Existen opciones tarifarias con cargo por demanda maxima en hora punta ($5.011/kW/mes en BT) - EMELCA 2026.
- El esquema tarifario refleja costo de transporte en hora punta, abriendo espacio para **gestion activa de demanda** (DR/DSM).
- La Estrategia Nacional de Electromovilidad 2030 requiere 6.500 puntos de carga publica al 2030.
- **Implicacion:** la distribuidora tiene incentivo economico directo para mover carga de hora punta a valle; un modelo de respuesta a precio dinamico es infraestructura habilitante.

---

## Tabla resumen de los 10 proyectos

| # | Idea | Cluster | Potencial economico anual (CLP) | Tamano mercado | Datos disponibles | Reutiliza infra |
|---|---|---|---:|---|---|---|
| 1 | Deteccion de fraude en PMGD (inyeccion no facturada) | 04 sin inspecciones | USD 8-15 M | 3.908 MW, 27 mil clientes | SI (medidores bidireccionales + Netbilling) | Si (4 LightGBM por cluster) |
| 2 | Mantenimiento predictivo de transformadores | 03 con insp sin irreg | USD 6-10 M | 27.000 transformadores | SI (SCADA, NeoMante, IoT) | Si (segmentacion) |
| 3 | Pronostico de demanda per-cluster para compra de energia | 01-04 | USD 4-8 M | 18.000 GWh/ano | SI (consumo historico 5 anos) | Si (cluster 01-04) |
| 4 | Scoring de morosidad y propension a impago | 01-04 | USD 3-6 M | $860 MM CLP deuda | SI (historial pago, SEC, Equifax) | Si (4 clusters) |
| 5 | Pronostico de generacion solar agregada (PMGD forecasting) | new | USD 2-4 M | 21 TWh/ano solar | SI (CNE publica, telemedida) | Parcial (infra D3) |
| 6 | Peak shaving residencial (prediccion de demanda maxima) | 02-04 | USD 1.5-3 M | Cargo punta $5.011/kW/mes | SI (smart meters 80%) | Si (segmentos) |
| 7 | Scoring de propension a reclamos a SEC | 04 | USD 1-2.5 M | 1.5 M reclamos/historico | SI (SIC, SEC) | Si (cluster 04) |
| 8 | Propension a adopcion de electromovilidad por manzana | new | USD 1-2 M | 6.500 cargadores meta 2030 | SI (padron vehicular, ANAC) | Parcial |
| 9 | Deteccion de fraude en autoconsumo Netbilling residencial | 04 | USD 1-2 M | 322 MW residencial | SI (Netbilling, telemedida) | Si (cluster 04) |
| 10 | Optimizacion de tarifas dinamicas residenciales (DR/DSM) | 02-03 | USD 0.5-1.5 M | 5,86 M clientes BT1 | SI (consumo, smart meters) | Si (segmentacion) |

**Total capturable (estimacion agregada):** USD 28-54 millones al ano, equivalente al 1,5% a 3,0% de los ingresos operacionales de Enel Distribucion Chile (USD ~1.800 M al ano en 2025).

---

## 1. Deteccion de fraude en PMGD (inyeccion no facturada)

### Problema
Los PMGD (Pequeños Medios de Generacion Distribuida) son proyectos de generacion solar o eolica conectados a la red de distribucion, con potencia hasta 9 MW. La ley permite que inyecten excedentes a la red y reciban creditos en su boleta (Netbilling) o paguen un precio regulado (PMGD propiamente tales). **El problema:** no todos los PMGD declaran correctamente su inyeccion. Un panel residencial de 5 kW que inyecta 4 kW de noche (sin consumo nocturno) o que declara potencia menor a la real (subdimensionando el credito a la distribuidora) genera perdida directa. Tambien hay casos de inversion del sentido de la medicion por intervencion del medidor.

### Tamano del mercado y potencial economico
- 3.908 MW PMGD instalados a diciembre 2025 (10% de la capacidad del sistema).
- 27.230 instalaciones residenciales Netbilling; +5.479 en 2025.
- 322 MW Netbilling residencial acumulado.
- Estimacion: 2-5% de fraude tecnico o declarativo en PMGD residenciales y 5-10% en PMGD comerciales. Sobre 322 MW residenciales a 6 horas equivalentes de inyeccion no facturada por dia, eso son ~70 GWh al ano no facturados = **USD 8-15 millones al ano en energia no cobrada**.

### Como se conecta con el modelo existente
Reutiliza directamente la **segmentacion por historial del cliente**: los PMGD con historial de inspecciones problematicas (cluster 01-02) requieren un score distinto que los PMGD nuevos (cluster 04). La metodologia de 4 LightGBM por cluster es identica. La feature engineering es la misma: historial de inspeccion, contexto de red (SET, alimentador), anomalias de medidor (lecturas invertidas, gaps), consumo mensual comparado con la potencia instalada. El dashboard ya tiene el patron visual y el pipeline de despliegue esta probado.

### Datos necesarios
- Telemedida de PMGD (CNE publica series de inyeccion).
- Padron de PMGD registrados (CNE Open Data).
- Historial de inspecciones a PMGD (si existen).
- Lecturas de medidor bidireccional por hora.
- Variables climaticas (radiacion solar) para cross-check.

### Stack tecnico
- 4 LightGBM por cluster (mismos hiperparametros que el modelo de hurto).
- Features de inyeccion esperada (potencia instalada x radiacion historica) vs inyeccion real.
- Anomalias: gaps de medicion, lecturas invertidas, subdimensionamiento consistente.
- Comparacion con PMGD vecinos del mismo SET/alimentador.

### Por que tiene potencial economico alto
1. **Magnitud:** USD 8-15 M al ano, el mas alto de los 10 proyectos.
2. **Crecimiento:** 92% CAGR en instalaciones Netbilling. Cada nuevo PMGD es un nuevo vector de fraude potencial.
3. **Regulacion:** la SEC audita PMGD pero la fiscalizacion es por inspeccion fisica; un modelo predictivo reduce inspecciones costosas.
4. **Margen:** un PMGD mal medido implica transferencia directa de costo a la distribuidora (la energia inyectada se descuenta del consumo del cliente pero la distribuidora la pago al precio regulado). Cada MWh no facturado es margen perdido.

---

## 2. Mantenimiento predictivo de transformadores de distribucion

### Problema
Los transformadores de distribucion son el activo mas caro y complejo de la red. Una falla no programada de un transformador genera un apagon que afecta a cientos o miles de clientes, dispara el SAIDI, y obliga a una reparacion de emergencia que cuesta 3-5x mas que un mantenimiento programado. La distribuidora atiende ~27.000 transformadores en Chile (Coordinador Electrico Nacional). Hoy el mantenimiento es por tiempo o por inspeccion visual; las fallas son reactivas.

### Tamano del mercado y potencial economico
- 27.000 transformadores en la red de distribucion nacional.
- Cada falla no programada de un transformador urbano afecta ~200-500 clientes y dura 2-4 horas.
- Enel Distribucion tuvo SAIDI 150 min (2024) y 167 min (2025). El 60% del SAIDI es por causas internas.
- Reducir SAIDI en 10% (de 167 a 150 min) significa ~ USD 4 millones en compensaciones evitadas, mas USD 2-3 millones en costo de reparacion de emergencia evitado.
- Estimacion conservadora: **USD 6-10 millones al ano** en compensaciones y reparaciones evitadas, mas 5-10% en extension de vida util de activos (reemplazo programado vs de emergencia).

### Como se conecta con el modelo existente
Este proyecto es la **evolucion natural** del modelo de inspeccion del cluster 03 (ConInspeccionesSinIrregularidad). En lugar de predecir si un *cliente residencial* tiene hurto, predecimos si un *transformador* va a fallar. El input sigue siendo un historial de inspecciones + variables climaticas + edad + carga, pero la unidad de observacion es el activo, no el cliente. El dashboard puede extenderse con un panel de "salud de activos" sin modificar la infra D3 existente.

### Datos necesarios
- Falla historica de transformadores (Coordinador Electrico Nacional publica NeoMante 2014-2022 con 27.000 registros).
- Variables climaticas: temperatura, humedad, precipitacion, eventos atmosfericos.
- Carga historica del transformador (kVA, factor de utilizacion).
- Edad, marca, tipo de aceite, historial de mantenimiento.
- Telemetria IoT (si esta disponible; creciente en Chile).

### Stack tecnico
- Modelo de clasificacion binaria (falla si/no en proximos 12 meses) - SVM o LightGBM (teseo U.Chile confirma viabilidad con 90% de accuracy en caso similar).
- Modelos de regresion para vida util restante (RUL) por activo.
- Series de tiempo para pronostico de carga.
- Combinacion con inspecciones fisicas y termografia.

### Por que tiene potencial economico alto
1. **Demanda regulatoria:** la CNE endurece los limites SAIDI/SAIFI cada ano; el modelo se vuelve necesario para cumplir.
2. **Costo de falla conocido:** USD 30-50k por transformador quemado de emergencia, vs USD 5-10k mantenimiento programado.
3. **Vida util extendida:** 5 anos adicionales en un transformador nuevo (~USD 100k) son USD 60k de costo evitado.
4. **Caso de referencia:** tesis de Universidad de Chile (Repositorio Uchile 2022) confirma reduccion de SAIDI de 1,08 horas a 0,3 horas con modelo predictivo - 72% de mejora en disponibilidad.

---

## 3. Pronostico de demanda per-cluster para compra de energia

### Problema
La distribuidora compra energia en el mercado mayorista (SEN) a precio spot y a precio de contrato. Comprar mal es muy caro: si compra menos de lo que va a demandar, debe pagar spot en horas punta (hasta USD 200/MWh); si compra mas, vende los excedentes a precio de liquidacion. El pronostico de demanda residencial per-cluster (1-2-3-4) permite:
- Compra de energia ajustada al perfil real
- Planificacion de mantenimientos programados en horas valle
- Deteccion de cambios estructurales (penetracion PMGD, electromovilidad)

### Tamano del mercado y potencial economico
- Enel Distribucion vende ~18.000 GWh al ano; el costo de compra es ~USD 80/MWh (mix contratos + spot), ~USD 1.440 millones al ano.
- Una mejora de 1% en el pronostico (reducir el error medio de 5% a 4%) significa ~USD 14 millones al ano en compras optimizadas.
- **Estimacion conservadora:** USD 4-8 millones al ano capturables (la mitad del upside por restricciones operacionales).

### Como se conecta con el modelo existente
**Reutilizacion directa:** la segmentacion por cluster 01-04 ya esta validada. El pronostico per-cluster es una extension natural: en lugar de entrenar un modelo de hurto por cluster, se entrena un modelo de pronostico de demanda por cluster. Los 4 modelos son LightGBM (mismo algoritmo, diferentes features y target). El feature engineering ya existe (consumo 6m, 12m, 24m, estacionalidad, cluster de historial). El dashboard puede extenderse con un panel de pronostico vs realizado.

### Datos necesarios
- Series historicas de consumo mensual por cliente (5+ anos disponibles en Enel).
- Variables climaticas (temperatura, radiacion - SEN ha publicado 30 anos).
- Calendario (feriados, eventos especiales).
- Variables socioeconomicas (IPC, empleo, etc. para pronostico macro).

### Stack tecnico
- LightGBM por cluster, con horizonte de pronostico T+1 a T+12 meses.
- Prophet o SARIMA como baseline.
- Features de lag y rolling windows.
- Cuantiles para intervalos de confianza (cuantil 0.5, 0.8, 0.95).

### Por que tiene potencial economico alto
1. **Universalidad:** todas las distribuidoras tienen este problema.
2. **Stack conocido:** pronostico de demanda electrica es el caso de uso mas estudiado de ML en utilities.
3. **Retorno inmediato:** las compras se ajustan mes a mes; el modelo se reentrena mensualmente.
4. **Externalidades positivas:** mejor pronostico = mejor planificacion de red = mejor calidad de servicio.

---

## 4. Scoring de morosidad y propension a impago

### Problema
La distribuidora tiene 5,86 millones de clientes residenciales (BT1) en Chile. El 10% esta moroso (720.840 clientes, $248 mil millones CLP en deuda a marzo 2025, $860 mil millones a marzo 2026). La Ley 21.340 (2021) congela el corte por mora, lo que hace que la cobranza preventiva sea el unico mecanismo operativo. La cobranza actual es indiscriminada: carta, llamado, visita, suspension. Un modelo de scoring permite focalizar la gestion en los clientes con mayor probabilidad de pago y ofrecer planes de pago preventivos a los de mayor riesgo de deterioro.

### Tamano del mercado y potencial economico
- $248-860 mil millones CLP en deuda (2025-2026), concentrada en 33% de los morosos.
- La distribuidora recupera ~30% de la deuda via gestion actual; con scoring podria llegar a 35-40%.
- Un 1% de mejora en la tasa de recuperacion sobre $248 mil millones = $2.485 millones CLP / ano (~USD 2,5 millones).
- Considerando gestion preventiva que evita deterioro de cuenta corriente, el upside llega a **USD 3-6 millones al ano**.

### Como se conecta con el modelo existente
**Reutilizacion directa:** la segmentacion 01-04 ya distingue clientes segun su historial. El cluster 01 (ConHurtoPrevio) y cluster 02 (ConIrregularidad) son candidatos naturales para scoring de morosidad: clientes con historial problematico tienden a ser morosos cronicos. Las features son muy similares: historial de inspeccion, notificaciones, distrito, marca de medidor, potencia. El target es diferente (impago vs hurto) pero la metodologia (4 LightGBM por cluster) es identica. El dashboard companion puede extenderse con un panel de riesgo de morosidad.

### Datos necesarios
- Historial de pago por cliente (3+ anos en Enel).
- Datos socioeconomicos por manzana (CENSO 2024, IRIC, Equifax).
- Historial de inspecciones y notificaciones.
- Variables climaticas y eventos socioeconomicos (paro, pandemia).
- Datos de contacto y canales de pago preferidos.

### Stack tecnico
- 4 LightGBM por cluster (mismo patron).
- Modelo de sobrevivencia (Cox, DeepSurv) para tiempo hasta mora.
- Modelos de uplift para identificar a quien mandar la carta vs a quien ofrecer plan de pago.

### Por que tiene potencial economico alto
1. **Magnitud del problema:** 720 mil morosos, $248-860 mil millones CLP en deuda.
2. **Regulacion critica:** la ley congela el corte, asi que la cobranza es el unico levier.
3. **Recuperacion media-baja:** hay mucho espacio para mejorar.
4. **Extension natural del modelo actual:** el cluster 02 ya existe, solo se cambia el target.

---

## 5. Pronostico de generacion solar agregada (PMGD forecasting)

### Problema
La generacion distribuida (PMGD + Netbilling residencial) es **intermitente** y **descentralizada**. 3.908 MW PMGD + 322 MW Netbilling residencial en Chile, con penetracion creciente (92% CAGR historico). Para el operador del sistema y la distribuidora, la variabilidad de esta generacion es un problema de gestion de red: la curva de generacion solar cae abruptamente a las 18:00 ("duck curve"), exigiendo que otras centrales rampen rapido. Un pronostico preciso de generacion solar agregada por zona permite:
- Planificacion de reservas rotantes
- Deteccion de fallas en PMGD (un PMGD que no inyecta lo esperado es una anomalia)
- Compra de energia complementaria mas ajustada

### Tamano del mercado y potencial economico
- 21,14 TWh de generacion solar en 2025 (29,3% del total solar = 6,19 TWh PMGD).
- 9,4 GW de pipeline en construccion (52,7% solar).
- Una mejora de 5% en el pronostico de generacion solar = reduccion de compras spot para balance = ~USD 2-4 millones al ano para el sistema.
- **Estimacion para la distribuidora (no para el operador):** USD 2-4 millones al ano, principalmente en la planificacion de compras de potencia.

### Como se conecta con el modelo existente
Reutilizacion parcial: el modelo de despliegue ya tiene las variables climaticas (radiacion, temperatura) como input al feature engineering de consumo. Se agrega una capa de pronostico meteorologico (numeros GFS o ECMWF) y se entrena un LightGBM por SET/alimentador en lugar de por cluster de cliente. El dashboard puede extenderse con un panel de generacion esperada vs real.

### Datos necesarios
- Telemedida de PMGD por hora (CNE publica).
- Pronostico meteorologico numerico (GFS, ECMWF) a 24-72 horas.
- Coordenadas de cada PMGD.
- Variables climaticas historicas (radiacion, temperatura, nubosidad).
- Calendario (estacionalidad).

### Stack tecnico
- LightGBM por alimentador / SET.
- LSTM o Transformer para series de tiempo.
- Numerical Weather Prediction (NWP) como feature.
- Quantile regression para intervalos.

### Por que tiene potencial economico alto
1. **Crecimiento exponencial del sector:** 92% CAGR en Netbilling, 9,4 GW de pipeline.
2. **Problema nuevo:** la duck curve es de los ultimos 3 anos, las distribuidoras no tienen modelos.
3. **Externalidad para el SEN:** el pronostico beneficia al sistema completo, no solo a la distribuidora.
4. **Stack de PMGDs creciente:** cada nueva conexion es un nuevo dato y un nuevo desafio.

---

## 6. Peak shaving residencial (prediccion de demanda maxima)

### Problema
La distribuidora factura a clientes residenciales con cargo por **demanda maxima en hora punta** ($5.011/kW/mes en BT segun tarifas EMELCA 2026) y la hora punta es 18:00-23:00 entre abril y septiembre. La distribuidora paga la **demanda maxima coincidente** del sistema en el SEN a precio de potencia. Si la distribuidora subdimensiona la demanda maxima, paga sobreprecio en el SEN. Si la sobreestima, pierde margen.

### Tamano del mercado y potencial economico
- Cargo punta: $5.011/kW/mes para clientes BT1, ~5,86 millones de clientes.
- Cargo SEN por demanda maxima: ~$4.000-6.000/kW/mes segun temporada.
- Una prediccion de demanda maxima con error <2% (vs ~5% actual) permite ahorros por **USD 1,5-3 millones al ano** para una distribuidora de 1,9 millones de clientes.

### Como se conecta con el modelo existente
**Reutilizacion directa:** los 4 clusters de LightGBM se entrenan con features de consumo horario (q01-q03 = promedios trimestrales). El feature engineering agrega variables de hora del dia, dia de la semana, estacionalidad, temperatura, eventos locales (partidos, conciertos). El output del modelo de pronostico se alimenta al de pronostico de demanda (proyecto 3) y al modulo de peak shaving. El dashboard puede mostrar perfil de carga proyectado por cluster y por zona.

### Datos necesarios
- Lectura horaria de medidores inteligentes (80% de penetration en Enel).
- Calendario y eventos especiales.
- Variables climaticas horarias.
- Distribucion de PMGD por zona (para corregir la inyeccion).

### Stack tecnico
- LightGBM por cluster + zona, con horizonte T+24h, T+7d, T+30d.
- Prophet o DeepAR como baseline.
- Conformal prediction para intervalos de confianza.

### Por que tiene potencial economico alto
1. **Cargo regulatorio especifico:** $5.011/kW/mes es un numero concreto que la distribuidora factura.
2. **Smart meters disponibles:** 80% de penetration en Enel.
3. **Estacionalidad marcada:** la hora punta es 18:00-23:00 de abril a septiembre, facil de modelar.
4. **Sinergia con PMGD:** la inyeccion solar reduce la demanda maxima, hay que modelar el neto.

---

## 7. Scoring de propension a reclamos a SEC

### Problema
La distribuidora recibio 1,5 millones de reclamos entre abril y octubre de 2020 (Memoria Uchile 2022). Cada reclamo que escala a la SEC genera compensacion, multa, y dano reputacional. Un modelo que predice que clientes son mas propensos a escalar un reclamo permite gestion preventiva (contacto proactivo, resolucion in-situ).

### Tamano del mercado y potencial economico
- 1,5 millones de reclamos en 6 meses = 250 mil reclamos/mes extrapolable a la red nacional.
- Costo promedio de gestion de un reclamo que escala a SEC: ~$50-150k CLP (incluye tiempo de atencion, compensacion, multa).
- Reduccion del 10% de los reclamos que escalan = **USD 1-2,5 millones al ano**.

### Como se conecta con el modelo existente
**Reutilizacion directa del cluster 04 (SinInspecciones):** los clientes que nunca han sido inspeccionados son los mas propensos a escalar un reclamo (desconocimiento del proceso, primera mala experiencia). El feature engineering reutiliza: historial de inspecciones, distrito, marca, potencia, estacionalidad. El target es un reclamo escalado (binario) en lugar de hurto. El dashboard puede extenderse con un panel de "riesgo de escalamiento SEC" por zona.

### Datos necesarios
- Historial de reclamos por cliente (sistema SIC de la SEC).
- Historial de inspecciones y resoluciones.
- Datos socioeconomicos por zona.
- Tasa de resolucion en primera instancia.
- Variables climaticas (los reclamos escalan despues de eventos climaticos extremos).

### Stack tecnico
- 4 LightGBM por cluster.
- NLP sobre el texto del reclamo (clasificación de causa raiz).
- Modelo de uplift para identificar el canal de resolucion optimo.

### Por que tiene potencial economico alto
1. **Regulacion especifica:** la SEC monitorea y publica tasa de reclamos por distribuidora.
2. **Costo directo:** compensacion + multa por reclamo escalado.
3. **Dano reputacional:** la tasa de reclamos es publica; los clientes la consultan.
4. **Reutilizacion:** el cluster 04 es identico al del modelo de hurto.

---

## 8. Propension a adopcion de electromovilidad por manzana

### Problema
La Estrategia Nacional de Electromovilidad 2030 requiere 6.500 puntos de carga publica. La penetracion residencial de vehiculos electricos (3,8% en 2026) genera una carga adicional proyectada de 3-22 kW por hogar, lo que puede saturar transformadores de distribucion. La distribuidora necesita dimensionar la red electrica **antes** de que la demanda se materialice, no despues.

### Tamano del mercado y potencial economico
- Meta 6.500 cargadores publicos al 2030.
- 12.000 BEV+PHEV en 2026, ~25.000 en 2027, ~50.000 en 2028 (proyeccion ANAC).
- Cada hogar que adopta un EV agrega 3-22 kW de carga. Si 5.000 hogares adoptan en 2026, son 25-110 MW adicionales en la red BT.
- Costo de refuerzo de red: USD 1.000-3.000 por hogar.
- Optimizacion del 20% en planificacion de red = **USD 1-2 millones al ano** en CAPEX diferido.

### Como se conecta con el modelo existente
Reutilizacion parcial: la segmentacion por cluster aplica a la dimension de "carga electrica total" (consumo + EV). El feature engineering agrega variables socioeconomicas: ingreso promedio de la manzana, tenencia de vivienda, distancia al trabajo (proxy de commuting), densidad de EV actuales (del padron vehicular). El modelo de propension se entrena con el target = "primer EV registrado en la manzana en los proximos 12 meses".

### Datos necesarios
- Padron vehicular 2024-2026 (INE/ANAC).
- CENSO 2024 (ingreso, educacion, tenencia).
- Topologia de la red (subestaciones, transformadores, capacidad).
- Datos de electricidad por manzana (consumo agregado).

### Stack tecnico
- LightGBM por manzana, con horizonte T+12m.
- Modelo de adoption diffusion (Bass model) para proyeccion de la curva S.
- Geospatial features (densidad urbana, distancia a corredor de transporte).

### Por que tiene potencial economico alto
1. **Crecimiento explosivo:** +162,9% en 2026 vs 2025, segmento en despegue.
2. **Meta regulatoria explicita:** 6.500 cargadores al 2030 obliga a planificacion.
3. **CAPEX evitado:** reforzar red cuesta USD 1-3k por hogar; predecir evita obras en frio.
4. **Caso de uso replicable:** el mismo modelo sirve para paneles solares, bombas de calor, etc.

---

## 9. Deteccion de fraude en autoconsumo Netbilling residencial

### Problema
Los 27 mil sistemas solares residenciales bajo Netbilling inyectan excedentes a la red y reciben creditos. Hay varios tipos de fraude:
- **Subdimensionamiento declarado:** instalar 8 kW pero declarar 5 kW.
- **Modular el medidor:** intervenir el medidor para registrar menos inyeccion.
- **Inyeccion no registrada:** vender excedentes a un tercero sin facturarlos a la distribuidora.

### Tamano del mercado y potencial economico
- 322 MW Netbilling residencial (2024), creciendo 54% anual.
- 27 mil instalaciones; si 5% tiene algun tipo de fraude, son 1.350 clientes.
- Estimacion: USD 1-3k/ano por cliente fraudulento = **USD 1-2 millones al ano** capturables.

### Como se conecta con el modelo existente
**Reutilizacion directa del cluster 04 (SinInspecciones):** los clientes con Netbilling residencial sin inspeccion previa son candidatos para scoring de fraude. El feature engineering reutiliza: potencia instalada, distrito, marca del inversor, historial de inspecciones, inyeccion esperada (potencia x radiacion x 6h). El target es "inyeccion real << inyeccion esperada en X%" o "medidor intervenido" (binario). El dashboard ya tiene el patron visual y el contrato de features.

### Datos necesarios
- Padron Netbilling (CNE Open Data).
- Telemedida del medidor bidireccional (horaria).
- Radiacion solar historica por coordenada.
- Padron de inversores y marcas de paneles.
- Coordenadas de cada instalacion.

### Stack tecnico
- 4 LightGBM por cluster (cluster 04 = Netbilling residencial sin inspeccion).
- Features de inyeccion esperada vs inyeccion real.
- Anomalias: variabilidad atipica, declaracion de potencia sospechosa.
- Comparacion con vecinos del mismo SET (peer benchmarking).

### Por que tiene potencial economico alto
1. **Sector en crecimiento explosivo:** +54% anual en Netbilling.
2. **Margen directo:** cada kWh de inyeccion no facturada es margen perdido para la distribuidora.
3. **Tecnologia accesible:** la telemedida horaria ya esta disponible.
4. **Reutilizacion maxima:** es el mismo modelo de hurto aplicado a otra fuente de fraude.

---

## 10. Optimizacion de tarifas dinamicas residenciales (DR/DSM)

### Problema
La distribuidora tiene 5,86 millones de clientes residenciales (BT1). El esquema tarifario actual cobra un **cargo por demanda maxima en hora punta** ($5.011/kW/mes) que incentiva a los clientes a mover carga. Pero el esquema es pasivo: el cliente no sabe que esta en punta. La distribuidora puede ofrecer tarifas dinamicas (precio mayor en punta, menor en valle) o programas de respuesta a la demanda (DR) para mover carga. La adopcion actual de estos esquemas es baja (<5% de clientes residenciales). Un modelo de propension permite identificar que clientes son mas propensos a adoptar DR/DSM y priorizarlos.

### Tamano del mercado y potencial economico
- 5,86 millones de clientes BT1; si 20% adopta DR/DSM, son 1,17 millones.
- Cada cliente que adopta DR/DSM reduce su demanda punta 10-20% = 0,3-0,6 kW menos en punta.
- La distribuidora ahorra en compras de potencia y se beneficia del esquema regulatorio.
- Estimacion conservadora: **USD 0,5-1,5 millones al ano** en margen tarifario + USD 0,5-1 M en CAPEX evitado.

### Como se conecta con el modelo existente
**Reutilizacion directa de la segmentacion 01-04:** los clusters ya distinguen clientes segun su perfil de consumo. El cluster 02 (ConIrregularidadNoHurto) y cluster 03 (ConInspeccionesSinIrregularidad) son los mas propensos a adoptar tarifas dinamicas (tienen consumo alto y son sensibles a precio). El feature engineering agrega: variabilidad del consumo horario, estacionalidad, respuesta a eventos climaticos, tenencia de vehiculo electrico. El target es "acepta oferta de tarifa dinamica" (binario) o "reduce consumo en punta" (regresion). El dashboard puede mostrar el potencial de DR por cluster.

### Datos necesarios
- Lectura horaria de medidores inteligentes (80% de penetration en Enel).
- Historial de pago y reaccion a cambios tarifarios.
- Datos socioeconomicos por manzana.
- Tenencia de electrodomesticos grandes (calefaccion electrica, piscina).
- Historial de eventos climaticos extremos.

### Stack tecnico
- 4 LightGBM por cluster (cluster 02-03 son los prioritarios).
- Modelo de uplift (causal) para identificar el incentivo optimo.
- Algoritmo de optimizacion de tarifas (linear programming).

### Por que tiene potencial economico alto
1. **Regulacion habilitante:** la opcion tarifaria existe (TRBT2) pero la adopcion es baja.
2. **Stack disponible:** smart meters, lectura horaria.
3. **Externalidades:** reducir picos beneficia al SEN completo.
4. **Reutilizacion:** extension natural del modelo de propension.

---

## Resumen y ranking de implementacion

### Por potencial economico (orden de magnitud anual)

| Rank | Proyecto | USD M/ano | Facilidad | Tiempo a valor |
|---|---|---:|---|---|
| 1 | Fraude PMGD | 8-15 | Media | 6-9 meses |
| 2 | Mantenimiento transformadores | 6-10 | Alta (teseo U.Chile confirma) | 4-6 meses |
| 3 | Pronostico de demanda per-cluster | 4-8 | Alta (caso de uso conocido) | 3-4 meses |
| 4 | Scoring de morosidad | 3-6 | Alta (mismo cluster) | 3-4 meses |
| 5 | Pronostico PMGD | 2-4 | Media | 6-9 meses |
| 6 | Peak shaving | 1,5-3 | Alta (smart meters 80%) | 3-4 meses |
| 7 | Scoring reclamos SEC | 1-2,5 | Alta (cluster 04) | 3-4 meses |
| 8 | Propension electromovilidad | 1-2 | Media (datos externos) | 6-9 meses |
| 9 | Fraude Netbilling | 1-2 | Alta (reutiliza cluster 04) | 3-4 meses |
| 10 | Tarifas dinamicas | 0,5-1,5 | Media (modelo uplift) | 6-9 meses |

### Por facilidad de implementacion (rapido time-to-value)

1. **Pronostico de demanda** (mes 3) - caso de uso conocido, datos disponibles
2. **Scoring de morosidad** (mes 3) - extension del cluster existente
3. **Peak shaving** (mes 3) - smart meters ya disponibles
4. **Mantenimiento transformadores** (mes 4) - tesis U.Chile valida el approach
5. **Scoring reclamos** (mes 3) - cluster 04 directo
6. **Fraude Netbilling** (mes 3) - cluster 04 + Netbilling
7. **Fraude PMGD** (mes 6) - nuevos datos, mas desarrollo
8. **Pronostico PMGD** (mes 6) - NWP como feature
9. **Propension electromovilidad** (mes 6) - datos externos (padron)
10. **Tarifas dinamicas** (mes 6) - modelo uplift complejo

### Recomendacion de implementacion (roadmap 18 meses)

**Fase 1 (meses 1-4): Quick wins**
- Proyecto 3 (pronostico de demanda) + Proyecto 4 (scoring de morosidad) + Proyecto 6 (peak shaving)
- Reutilizan 100% de la infra de 4 LightGBM y el dashboard existente
- Valor: USD 9-17 millones al ano

**Fase 2 (meses 5-9): Expansion**
- Proyecto 2 (mantenimiento transformadores) + Proyecto 7 (reclamos SEC) + Proyecto 9 (fraude Netbilling)
- Reutilizan infra de cluster 01-04
- Valor: USD 8-14,5 millones al ano

**Fase 3 (meses 10-18): Bets grandes**
- Proyecto 1 (fraude PMGD) + Proyecto 5 (pronostico PMGD) + Proyecto 8 (electromovilidad) + Proyecto 10 (tarifas dinamicas)
- Requieren datos externos y modelos nuevos
- Valor: USD 11-22,5 millones al ano

**Total capturable en 18 meses:** USD 28-54 millones al ano, 1,5-3,0% de los ingresos operacionales de Enel Distribucion Chile.

---

## Referencias y fuentes

### Datos del sector eléctrico chileno 2025-2026

- ACESOL (2025). *Reporte ACESOL 2025: Año de Consolidación Solar y Almacenamiento*. https://acesol.cl/images/reportes/reporte-ACESOL-2025.pdf
- ANAC (2025). *Informe del Mercado Automotor Diciembre 2025*. https://www.anac.cl/wp-content/uploads/2026/01/12-ANAC-Mercado-Automotor-Diciembre-2025.pdf
- ANAC (2025). *Informe Cero y Bajas Emisiones Diciembre 2025*. https://www.anac.cl/wp-content/uploads/2026/01/12-ANAC-Informe-Cero-y-Bajas-Emisiones-Diciembre-2025.pdf
- BCN (2026). *Electromovilidad en Chile: Avances, brechas y desafíos regulatorios*. https://www.bcn.cl/obtienearchivo?id=repositorio/10221/38634/1/BCN___Electromovilidad_desafios_regulatorios_Chile.pdf
- CIPER (2026). *Tarifas eléctricas: todo con tu plata*. https://www.ciperchile.cl/2026/06/15/tarifas-electricas-todo-con-tu-plata/
- CNE (2024). *Norma Técnica de Calidad de Servicio para Sistemas de Distribución*. https://www.cne.cl/wp-content/uploads/2024/05/NTCSDx2024-1.pdf
- Coordinador Eléctrico Nacional (2026). *Reporte Anual de Desempeño del Sistema Eléctrico 2025*. https://www.coordinador.cl/wp-content/uploads/2026/04/CEN-Reporte-Art-72-15-ano-2025-21-04-2026.pdf
- Enel Chile (2025). *Memoria Integrada Interactiva 2024*. https://www.enel.cl/content/dam/enel-cl/inversionistas/enel-chile/reportes/memorias/2024/Memoria-Anual-Integrada-Enel-Chile-2024.pdf
- Enel Chile (2026). *FY 2025 Results & Strategic Plan 2026-28*. https://www.enel.cl/content/dam/enel-cl/inversionistas/enel-chile/informacion-para-el-accionista/plan-estrategico/presentaciones-plan/2026/Enel-Chile-FY-2025-Results-Strategic-Plan-2026-28.pdf
- Enel Chile (2025). *Form 20-F 2025*. https://www.enel.cl/content/dam/enel-cl/en/investors/enel-chile/reports/20f/2025/Form-20-F-2025-Enel-Chile.pdf
- La Tercera (2025). *Deudores de cuenta de luz superan los 720 mil*. https://www.latercera.com/earlyaccess/noticia/deudores-de-cuenta-de-luz-superan-los-720-mil-e-impago-promedio-se-duplica-en-un-ano/ZWQYYCPUEBF4PNNUGCI4KXGGYM/
- Plataforma Transición Energética (2025). *Generación distribuida para autoconsumo en Chile*. https://www.plataformatransicionenergetica.org/2025/07/28/como-avanza-la-generacion-distribuida-para-autoconsumo-en-chile/
- Senado de Chile (2021). *Soluciones para morosos por servicios básicos*. https://www.senado.cl/comunicaciones/noticias/abogan-por-soluciones-para-morosos-por-servicios-basicos

### Trabajos académicos y casos de referencia

- Alvarez, L., Lozano, C., Bravo, D. (2022). *Metodología para el mantenimiento predictivo de transformadores de distribución basada en aprendizaje automático*. Scielo. http://www.scielo.org.co/scielo.php?script=sci_arttext&pid=S0121-750X2022000300202
- Enel Generación Perú (2024). *IA para mantenimiento predictivo en transformadores*. Premios Proactivo. https://premiosproactivo.org/i-a-para-mantenimiento-predictivo-y-analisis-de-fallas-en-transformaciones-de-plantas-de-generacion/
- Guíachile Energía (2024). *Mantenimiento predictivo para la confiabilidad del sistema eléctrico*. https://www.guiachileenergia.cl/energia-sin-interrupciones-mantenimiento-predictivo-para-la-confiabilidad-del-sistema-electrico/
- IADB (2024). *Tecnologías de IA en el mantenimiento de activos del sector eléctrico*. https://publications.iadb.org/publications/spanish/document/Tecnologias-de-Inteligencia-Artificial-AI-en-el-mantenimiento-de-activos-del-sector-electrico.pdf
- Universidad de Chile (2022). *Rediseñar el proceso de estudio y calidad de servicio integrando un modelo de predicción para las desconexiones de curso forzoso en los transformadores de poder*. https://repositorio.uchile.cl/handle/2250/195386
- Universidad de Chile (2021). *Aplicaciones de Data Science para la mejora de la medición y cobro de la distribución de la energía eléctrica en contextos de Pandemia Mundial*. https://repositorio.uchile.cl/handle/2250/182461

---

*Miguel Ortiz C. - Notas de trabajo - Julio 2026*
