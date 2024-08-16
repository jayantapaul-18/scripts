# Provider configuration
provider "aws" {
  region = "us-east-1"
}

# Create a VPC
resource "aws_vpc" "aurora_vpc" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name = "aurora-vpc"
  }
}

# Create Subnets
resource "aws_subnet" "aurora_subnet_a" {
  vpc_id            = aws_vpc.aurora_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
  tags = {
    Name = "aurora-subnet-a"
  }
}

resource "aws_subnet" "aurora_subnet_b" {
  vpc_id            = aws_vpc.aurora_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"
  tags = {
    Name = "aurora-subnet-b"
  }
}

# Create a Security Group
resource "aws_security_group" "aurora_sg" {
  name        = "aurora-sg"
  description = "Aurora security group"
  vpc_id      = aws_vpc.aurora_vpc.id

  ingress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Make sure to restrict this in production
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "aurora-sg"
  }
}

# Create DB Subnet Group
resource "aws_db_subnet_group" "aurora_subnet_group" {
  name       = "aurora-subnet-group"
  subnet_ids = [aws_subnet.aurora_subnet_a.id, aws_subnet.aurora_subnet_b.id]

  tags = {
    Name = "aurora-subnet-group"
  }
}

# Create Aurora MySQL Cluster
resource "aws_rds_cluster" "aurora_cluster" {
  cluster_identifier      = "aurora-cluster"
  engine                  = "aurora-mysql"
  engine_version          = "8.0.mysql_aurora.3.02.0"
  master_username         = "admin"
  master_password         = "YourPasswordHere"
  db_subnet_group_name    = aws_db_subnet_group.aurora_subnet_group.name
  vpc_security_group_ids  = [aws_security_group.aurora_sg.id]
  backup_retention_period = 5
  preferred_backup_window = "07:00-09:00"

  tags = {
    Name = "aurora-cluster"
  }
}

# Create Aurora MySQL Cluster Instances (2 instances)
resource "aws_rds_cluster_instance" "aurora_instance_a" {
  identifier              = "aurora-instance-a"
  cluster_identifier      = aws_rds_cluster.aurora_cluster.id
  instance_class          = "db.r5.large"
  engine                  = aws_rds_cluster.aurora_cluster.engine
  engine_version          = aws_rds_cluster.aurora_cluster.engine_version
  publicly_accessible     = false
  db_subnet_group_name    = aws_db_subnet_group.aurora_subnet_group.name
  availability_zone       = "us-east-1a"

  tags = {
    Name = "aurora-instance-a"
  }
}

resource "aws_rds_cluster_instance" "aurora_instance_b" {
  identifier              = "aurora-instance-b"
  cluster_identifier      = aws_rds_cluster.aurora_cluster.id
  instance_class          = "db.r5.large"
  engine                  = aws_rds_cluster.aurora_cluster.engine
  engine_version          = aws_rds_cluster.aurora_cluster.engine_version
  publicly_accessible     = false
  db_subnet_group_name    = aws_db_subnet_group.aurora_subnet_group.name
  availability_zone       = "us-east-1b"

  tags = {
    Name = "aurora-instance-b"
  }
}

# Add 200GB Storage
resource "aws_rds_cluster_parameter_group" "aurora_storage" {
  name   = "aurora-storage"
  family = "aurora-mysql8.0"

  parameter {
    name  = "innodb_buffer_pool_size"
    value = "200000000000"  # ~200GB in bytes
  }

  tags = {
    Name = "aurora-storage"
  }
}
