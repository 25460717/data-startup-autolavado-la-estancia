output "datalake_bucket_name" {
  description = "Nombre del bucket S3 creado"
  value       = aws_s3_bucket.datalake_bucket.id
}

output "ventas_queue_url" {
  description = "URL de la cola SQS de eventos de ventas"
  value       = aws_sqs_queue.ventas_events_queue.url
}

output "iam_role_arn" {
  description = "ARN del rol de ejecucion IAM"
  value       = aws_iam_role.app_runner_role.arn
}
