terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_instance" "airflow_vm" {
  ami           = "ami-07363e61041f15975" # Ubuntu Server 22.04 LTS (HVM), SSD Volume Type
  instance_type = "t2.micro"

  tags = {
    Name = "Airflow VM"
  }
}

resource "aws_s3_bucket" "datalake" {
  bucket = "datalake-bucket-for-airflow-and-delta"

  tags = {
    Name = "Datalake Bucket"
  }
}


