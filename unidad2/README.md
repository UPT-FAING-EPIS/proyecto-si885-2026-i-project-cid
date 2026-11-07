# Unidad II — Producción en redes sociales de estudiantes EPIS

La entrega de la primera unidad se conserva en el historial (`36057dc`). Esta continuación incorpora publicaciones de cuentas con evidencia de vínculo a EPIS. No incluye datos de ejemplo en producción. La autodeclaración de un perfil no acredita matrícula vigente.

## Contrato de datos

Cada lote consiste en un CSV y un manifiesto JSON. Se aceptan dos rutas: una exportación de una cuenta administrada o una captura de publicaciones públicamente visibles. En la segunda ruta no se exige acceso a la cuenta: se guardan la URL original y una captura/HTML como evidencia. El manifiesto identifica la cuenta, la plataforma y cómo se acreditó su relación con EPIS. Nunca se colocan tokens en el repositorio.

Columnas CSV: `post_id,post_url,published_at,content_type,topic,project,likes,comments,shares,reach,impressions,metrics_captured_at`. Columna adicional opcional: `published_label`.

- `post_id`, `post_url` y `metrics_captured_at` son obligatorios. Si solo se conoce una fecha relativa, `published_at` queda vacío y `published_label` conserva el texto observado. No se calcula un día a partir de «3 sem» o del ID de LinkedIn.
- Las métricas ausentes se dejan vacías. Un cero significa que la fuente informó cero.
- Las fechas usan ISO 8601 con zona horaria, por ejemplo `2026-10-10T14:30:00-05:00`.
- Los instantes se normalizan a UTC−5 para ordenarlos correctamente aunque los archivos usen distintas zonas horarias.
- El dashboard permite elegir fecha de captura o de publicación. En modo publicación, los registros sin fecha exacta no entran al gráfico temporal ni a un filtro específico de año/mes/día. La captura no se presenta como fecha de producción.
- La cuenta del manifiesto debe estar verificada como productora estudiantil EPIS. Una publicación institucional sobre estudiantes no cumple automáticamente este criterio.
- El archivo de evidencia original se conserva fuera del repositorio público. Su hash SHA-256 queda registrado en la base.

Ejemplos de **estructura**, sin registros numéricos: `templates/publicaciones.csv`, `templates/manifiesto.json` y `templates/manifiesto_publico.json`. Reemplace todos los campos del manifiesto con valores verificables antes de importar.

## Ejecutar

```powershell
python -m pip install -r unidad2/requirements.txt
python -m unidad2.pipeline --manifest RUTA_MANIFIESTO --csv RUTA_CSV --db RUTA_BASE
streamlit run unidad2/app.py -- --db RUTA_BASE
```

La aplicación muestra un estado vacío hasta que se importa un lote auténtico. Reimportar el mismo lote no duplica publicaciones ni instantáneas. Un mismo post puede tener varias capturas de métricas en fechas distintas; los reportes usan solo la última captura disponible de cada post.

## Entregables de la unidad

El almacén dimensional y los seis reportes están en este directorio. El despliegue y la programación en nube requieren acceso a la cuenta donde se alojará el sistema; la infraestructura propuesta se configura en `infra/` y no se aplica automáticamente.

## Flujo en AWS propuesto

**Si se confirma el VPS Contabo, usar la alternativa [VPS Debian](docs/vps.md)** y `compose.vps.yaml`; ese flujo no requiere una cuenta AWS. El archivo `compose.yaml` de esta sección sí requiere S3.

`infra/` crea una instancia EC2, IP pública fija y un bucket S3 privado, cifrado y versionado. La instancia tiene permiso de **lectura** solo sobre `incoming/` y se administra mediante Systems Manager; la base no expone un puerto público. El contenedor `worker` revisa el bucket cada hora y registra errores en su salida. El tablero se publica con HTTPS mediante Caddy.

1. Configurar `infra/terraform.tfvars` a partir del ejemplo y revisar los costos de EC2, IP pública, disco y S3 en la región elegida. `terraform plan` permite revisar recursos antes de `terraform apply`.
2. Tras crear la instancia, obtener acceso por AWS Systems Manager. Clonar la rama aprobada del repositorio, instalar la aplicación y crear `unidad2/.env` con `EPIS_SOURCE_BUCKET`, `AWS_REGION` y `SITE_HOST`. Para una IP `1.2.3.4`, el host de sslip.io sería `1-2-3-4.sslip.io`.
3. Subir cada lote autorizado a `s3://BUCKET/incoming/LOTE/` con `manifest.json`, `posts.csv` y el archivo de evidencia indicado por `source_evidence_path` relativo a esa carpeta. No subir contraseñas, tokens ni datos personales innecesarios.
4. Ejecutar desde `unidad2/`: `docker compose up -d --build`. Verificar `docker compose logs worker` y abrir el dominio HTTPS. El primer arranque sin lotes muestra explícitamente que no hay datos.

El repositorio de la primera unidad no contiene las credenciales ni el código de la página existente. Por eso este módulo no cambia esa página hasta verificar quién administra el servidor y cuál es su despliegue. Tampoco se ejecuta `terraform apply` sin cuenta y presupuesto comprobados.

GitHub Actions ejecuta las pruebas y genera un diagrama del modelo físico directamente desde `schema.sql`, disponible como artefacto descargable del flujo.

El avance real frente a cada punto de la consigna se registra en [`docs/cumplimiento.md`](docs/cumplimiento.md). Los componentes del presupuesto se enumeran en [`docs/costos.md`](docs/costos.md); su cifra final requiere conocer la región y la cuenta de AWS.

## Modelo y seis reportes

- `fact_post`: una fila por publicación, identificada por plataforma + ID externo.
- `fact_metric_snapshot`: una fila por publicación y fecha de captura. Los reportes usan solo la última captura; no suman varias lecturas del mismo post.
- Dimensiones: plataforma, cuenta, fecha, proyecto y formato.
- Reportes: registro temporal; plataformas; autores y proyectos; temas y formatos; interacciones; procedencia y calidad.

Cada publicación conserva su URL, lote, hash del CSV, hash del archivo original, método de obtención y referencia de autorización. Las métricas vacías permanecen nulas. No se calcula una tasa de interacción común entre plataformas porque sus denominadores y definiciones no son equivalentes.

## Primera carga real local · 7 de noviembre de 2026

Se observaron nueve publicaciones originales en el perfil de LinkedIn de Nayeli Quispe Cancapa, que declara estudiar Ingeniería de Sistemas en la UPT. Cinco mostraban contadores de reacciones (suma parcial: 23). Los demás valores no observados quedan nulos. Se excluyó una republicación de otro autor. No es un censo EPIS, una serie histórica de métricas ni una muestra representativa.

Los archivos locales están en `data/incoming/linkedin-20261107/`, excluidos de Git. `evidence.json` es una transcripción de observación, no una exportación oficial ni una captura de pantalla. Conserva URLs, etiquetas de fecha, contadores observados, método de selección y limitaciones. El formato `epis_observation_v1` concilia cada métrica y fecha del CSV contra esa transcripción antes de cargar. Los temas son clasificación analítica manual.

Para reproducir la carga en esta computadora:

```powershell
python -m unidad2.pipeline --manifest unidad2/data/incoming/linkedin-20261107/manifest.json --csv unidad2/data/incoming/linkedin-20261107/posts.csv
streamlit run unidad2/app.py --server.port 8502
```

Para cumplir completamente el análisis temporal de producción falta conseguir fechas exactas y ampliar las cuentas de estudiantes. El proceso S3 automatiza la importación de lotes depositados; **no recoge automáticamente publicaciones nuevas de LinkedIn**. La recolección de esta muestra fue manual asistida por navegador.
