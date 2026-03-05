output "cluster_name" {
  value = module.eks.cluster_name
}

output "cluster_endpoint" {
  value     = module.eks.cluster_endpoint
  sensitive = true
}

output "vpc_id" {
  value = module.networking.vpc_id
}

output "region" {
  value = var.region
}

output "cost_optimizer_irsa_role_arn" {
  value = module.eks.cost_optimizer_irsa_role_arn
}
