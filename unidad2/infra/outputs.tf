output "public_ip" {
  description = "IP de la instancia; configurar SITE_HOST y TLS antes de publicar."
  value       = aws_eip.web.public_ip
}

output "source_bucket" {
  description = "Bucket privado para lotes de exportaciones autorizadas."
  value       = aws_s3_bucket.sources.bucket
}
