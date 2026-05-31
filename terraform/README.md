# Terraform — EKS Cluster

Infrastructure-as-code that provisions an AWS EKS cluster (VPC, subnets, NAT
gateway, managed worker nodes) ready to run the image-classifier app from this
repo. Built on the official `terraform-aws-modules` VPC and EKS modules.

##  Cost warning — read this first

**This is NOT free-tier.** Running `terraform apply` creates real, billable AWS
resources:

- EKS control plane — ~$0.10/hour (~$73/month)
- 2× `t3.medium` worker nodes — ~$0.08/hour combined
- 1× NAT gateway — ~$0.045/hour + data

That's roughly **$0.20–0.25 per hour** while it's running. For a portfolio
demo, the right workflow is: `apply` → take your screenshots / test it →
**`terraform destroy`** within an hour or two. Always destroy when you're done,
and check the AWS Billing console afterward to confirm nothing was left behind.

## Prerequisites

- An AWS account and the AWS CLI configured (`aws configure`) with credentials
  that can create VPC, EKS, EC2 and IAM resources.
- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5
- `kubectl` (to talk to the cluster once it's up)

## Usage

```bash
cd terraform

# 1. Download the modules and providers
terraform init

# 2. Preview what will be created (always do this first)
terraform plan

# 3. Create the cluster (takes ~15 minutes)
terraform apply
```

When `apply` finishes it prints a `configure_kubectl` command. Run it to point
kubectl at the new cluster:

```bash
aws eks update-kubeconfig --region ap-southeast-2 --name mlops-pipeline
kubectl get nodes   # should list your worker nodes
```

## Deploy the app onto the cluster

Once kubectl is connected, deploy the image classifier using the manifests in
`../k8s` (set the image to the one your CI/CD pipeline published to GHCR first):

```bash
kubectl apply -f ../k8s/
kubectl get service image-classifier   # grab the external LoadBalancer URL
```

## Tear it all down

```bash
terraform destroy
```

This removes everything Terraform created. Do this as soon as you're finished
to stop the meter.

## What this provisions

- A VPC across 3 availability zones with public and private subnets
- A single NAT gateway (cost-optimised) for private-subnet egress
- An EKS cluster with a managed node group of worker nodes
- Subnet tags so Kubernetes can auto-provision load balancers

## Configuration

Defaults live in `variables.tf`. To override, copy `terraform.tfvars.example`
to `terraform.tfvars` and edit it — that file is gitignored so your local
settings won't be committed.
