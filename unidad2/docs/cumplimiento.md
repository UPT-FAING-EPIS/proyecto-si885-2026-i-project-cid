# Estado frente a la consigna

Esta tabla evita presentar como terminada una parte que todavía no funciona con datos reales.

| Entregable | Estado comprobado | Falta |
|---|---|---|
| FD01–FD04 de la primera unidad | Entrega conservada en `main`, commit `36057dc` | Adaptar los informes al alcance nuevo si el docente exige una versión actualizada |
| Aplicación pública | El dominio actual responde, pero sirve el Observatorio de GitHub | Acceso al despliegue y publicación de esta aplicación |
| Arquitectura Data Warehouse | Modelo dimensional y diagramas; primera carga real validada localmente | Ampliar muestra y documentar entorno cloud finalmente utilizado |
| ETL programado en nube | Worker preparado para revisar S3 cada hora; probado localmente | Desplegar en AWS y registrar ejecuciones reales |
| Infraestructura como código | Terraform validado localmente | Cuenta, región, presupuesto, `terraform plan` y aplicación controlada |
| Reporte de costos | Componentes identificados en `costos.md` | Cotización regional y costo observado en AWS |
| Procesos e infraestructura | Diagramas Mermaid y diagrama físico generado desde SQL | Evidencia de ejecución automatizada en GitHub Actions |
| Seis reportes con filtro temporal | Seis gráficos locales con nueve publicaciones reales; filtros de captura/publicación separados | Obtener fechas exactas para producción por día, ampliar cuentas y verificar despliegue público |

**Infraestructura por aclarar:** el propietario indica que utilizó un VPS Debian en Contabo. El dominio entregado apunta a otra IP. No se ha creado ningún recurso AWS. La propuesta Terraform AWS no prueba que el despliegue actual use AWS.

**Límite de la muestra:** una cuenta con vínculo autodeclarado a EPIS; nueve posts, cinco contadores de reacciones visibles. Fechas absolutas, alcance, impresiones y otros contadores no observados se mantienen nulos. Los datos locales no se publican en el repositorio.
