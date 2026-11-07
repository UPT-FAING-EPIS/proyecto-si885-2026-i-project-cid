# Reporte de costos — pendiente de región y cuenta

La configuración Terraform define los recursos que deben cotizarse. No se declara un precio final sin región elegida ni presupuesto aprobado.

| Recurso configurado | Cantidad | Base para el costo mensual |
|---|---:|---|
| EC2 `t3.small` | 1 | Tarifa de la región × horas encendida |
| Disco EBS `gp3` cifrado | 20 GB | Tarifa por GB-mes y operaciones adicionales si aplican |
| IPv4 pública elástica | 1 | Tarifa por hora de dirección pública |
| S3 privado y versionado | Según exportaciones reales | GB-mes, solicitudes y transferencia aplicable |
| Transferencia y registros | Según uso real | Medir después del despliegue |

**Para cerrar este informe:** seleccionar la región AWS, obtener los precios vigentes de [EC2](https://aws.amazon.com/ec2/pricing/) y [S3](https://aws.amazon.com/s3/pricing/), calcular un mes de uso previsto y contrastarlo luego con el costo observado en la cuenta. El hecho de usar un nivel gratuito no implica costo cero garantizado.
