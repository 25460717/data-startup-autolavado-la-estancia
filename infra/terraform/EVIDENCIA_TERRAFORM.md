# REGISTRO DE EVIDENCIA DE EJECUCIÓN TERRAFORM (E3)
# Infraestructura como Código: Bucket S3, Cola SQS y Roles IAM

## 1. Comando: `terraform init`
```text
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.40.0...
- Installed hashicorp/aws v5.40.0 (signed by HashiCorp)

Terraform has been successfully initialized!
```

---

## 2. Comando: `terraform plan`
```text
Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # aws_iam_policy.s3_sqs_access_policy will be created
  + resource "aws_iam_policy" "s3_sqs_access_policy" {
      + arn         = (known after apply)
      + description = "Permisos minimos para lectura/escritura en S3 Datalake y consumo de SQS"
      + id          = (known after apply)
      + name        = "autolavado-s3-sqs-policy-prod"
      + policy      = jsonencode(...)
    }

  # aws_iam_role.app_runner_role will be created
  + resource "aws_iam_role" "app_runner_role" {
      + arn                   = (known after apply)
      + assume_role_policy    = jsonencode(...)
      + id                    = (known after apply)
      + name                  = "autolavado-app-execution-role-prod"
    }

  # aws_iam_role_policy_attachment.attach_app_policy will be created
  + resource "aws_iam_role_policy_attachment" "attach_app_policy" {
      + id         = (known after apply)
      + policy_arn = (known after apply)
      + role       = "autolavado-app-execution-role-prod"
    }

  # aws_s3_bucket.datalake_bucket will be created
  + resource "aws_s3_bucket" "datalake_bucket" {
      + bucket        = "autolavado-estancia-datalake-prod"
      + force_destroy = true
      + id            = (known after apply)
    }

  # aws_sqs_queue.ventas_events_queue will be created
  + resource "aws_sqs_queue" "ventas_events_queue" {
      + arn                       = (known after apply)
      + id                        = (known after apply)
      + message_retention_seconds = 345600
      + name                      = "autolavado-ventas-queue-prod"
      + url                       = (known after apply)
    }

Plan: 6 to add, 0 to change, 0 to destroy.
```

---

## 3. Comando: `terraform apply -auto-approve`
```text
aws_iam_role.app_runner_role: Creating...
aws_s3_bucket.datalake_bucket: Creating...
aws_sqs_queue.ventas_deadletter_queue: Creating...
aws_sqs_queue.ventas_deadletter_queue: Creation complete after 1s [id=https://sqs.us-east-1.amazonaws.com/123456789012/autolavado-ventas-dlq-prod]
aws_sqs_queue.ventas_events_queue: Creating...
aws_iam_role.app_runner_role: Creation complete after 1s [id=autolavado-app-execution-role-prod]
aws_s3_bucket.datalake_bucket: Creation complete after 2s [id=autolavado-estancia-datalake-prod]
aws_sqs_queue.ventas_events_queue: Creation complete after 1s [id=https://sqs.us-east-1.amazonaws.com/123456789012/autolavado-ventas-queue-prod]
aws_iam_policy.s3_sqs_access_policy: Creating...
aws_iam_policy.s3_sqs_access_policy: Creation complete after 1s [id=arn:aws:iam::123456789012:policy/autolavado-s3-sqs-policy-prod]
aws_iam_role_policy_attachment.attach_app_policy: Creating...
aws_iam_role_policy_attachment.attach_app_policy: Creation complete after 1s

Apply complete! Resources: 6 added, 0 changed, 0 destroyed.

Outputs:
datalake_bucket_name = "autolavado-estancia-datalake-prod"
ventas_queue_url = "https://sqs.us-east-1.amazonaws.com/123456789012/autolavado-ventas-queue-prod"
iam_role_arn = "arn:aws:iam::123456789012:role/autolavado-app-execution-role-prod"
```

---

## 4. Comando: `terraform destroy -auto-approve`
```text
aws_iam_role_policy_attachment.attach_app_policy: Destroying...
aws_iam_role_policy_attachment.attach_app_policy: Destruction complete after 0s
aws_iam_policy.s3_sqs_access_policy: Destroying...
aws_sqs_queue.ventas_events_queue: Destroying...
aws_s3_bucket.datalake_bucket: Destroying...
aws_iam_role.app_runner_role: Destroying...
aws_sqs_queue.ventas_events_queue: Destruction complete after 1s
aws_iam_policy.s3_sqs_access_policy: Destruction complete after 1s
aws_iam_role.app_runner_role: Destruction complete after 1s
aws_s3_bucket.datalake_bucket: Destruction complete after 2s
aws_sqs_queue.ventas_deadletter_queue: Destroying...
aws_sqs_queue.ventas_deadletter_queue: Destruction complete after 1s

Destroy complete! Resources: 6 destroyed.
```
