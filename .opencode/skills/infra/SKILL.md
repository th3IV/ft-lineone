---
name: infra
description: >
  Use when working on infrastructure: Terraform modules, AWS resources (EKS,
  RDS, S3, ElastiCache), or environment configuration. Covers deployment
  conventions for dev and prod.
---

# Infraestructura Skill

Infraestructura como código con Terraform + AWS (EKS, RDS PostgreSQL, S3, ElastiCache Redis).

## Estructura
```
infra/
└── terraform/
    ├── modules/
    │   ├── vpc/           # VPC, subnets, security groups
    │   ├── eks/           # EKS cluster + node groups
    │   ├── rds/           # RDS PostgreSQL
    │   └── s3/            # S3 buckets (media, backups)
    └── environments/
        ├── dev/           # Entorno de desarrollo
        └── prod/          # Entorno de producción
```

## Convenciones
- Usar `terraform fmt` antes de cada commit
- Variables sensibles via `terraform.tfvars` (no committear)
- Ambientes separados (`dev/` y `prod/`)
- Cada módulo con `variables.tf`, `outputs.tf`, `main.tf`
- Usar módulos oficiales de Terraform Registry cuando sea posible
- Etiquetar recursos con `Environment`, `Project`, `ManagedBy`

## Despliegue
```powershell
cd infra/terraform/environments/dev
terraform init
terraform plan
terraform apply -auto-approve
```
