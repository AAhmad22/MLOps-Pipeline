data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  # Use the first three availability zones in the region.
  azs = slice(data.aws_availability_zones.available.names, 0, 3)

  tags = {
    Project   = "mlops-pipeline"
    ManagedBy = "terraform"
  }
}

# --- Networking -------------------------------------------------------------
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.cluster_name}-vpc"
  cidr = var.vpc_cidr

  azs             = local.azs
  private_subnets = [for k in range(3) : cidrsubnet(var.vpc_cidr, 4, k)]
  public_subnets  = [for k in range(3) : cidrsubnet(var.vpc_cidr, 4, k + 3)]

  enable_nat_gateway = true
  single_nat_gateway = true # one shared NAT gateway keeps cost down

  # Tags let Kubernetes auto-discover subnets when creating load balancers.
  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }

  tags = local.tags
}

# --- EKS cluster ------------------------------------------------------------
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = var.cluster_name
  kubernetes_version = var.kubernetes_version

  # Expose the API endpoint so you can run kubectl from your laptop.
  endpoint_public_access = true

  # Grant the IAM identity running `terraform apply` admin access to the cluster.
  enable_cluster_creator_admin_permissions = true

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    default = {
      ami_type       = "AL2023_x86_64_STANDARD"
      instance_types = var.instance_types

      min_size     = var.min_size
      max_size     = var.max_size
      desired_size = var.desired_size
    }
  }

  tags = local.tags
}
