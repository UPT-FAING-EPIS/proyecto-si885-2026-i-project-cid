variable "aws_region" {
  description = "Región de AWS elegida por el equipo."
  type        = string
}

variable "project_name" {
  description = "Prefijo único para recursos del proyecto."
  type        = string
  default     = "epis-social-bi"
}

variable "instance_type" {
  description = "Tipo de instancia según presupuesto y carga medida."
  type        = string
  default     = "t3.small"
}

variable "source_bucket_name" {
  description = "Nombre globalmente único del bucket privado de fuentes."
  type        = string
}
