variable "aws_region" {
  description = "Region de AWS para despliegue de infraestructura"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Ambiente de ejecucion (dev, staging, prod)"
  type        = string
  default     = "prod"
}
