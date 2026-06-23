resource "random_id" "product_images" {
  byte_length = 4
}

resource "random_id" "vton_results" {
  byte_length = 4
}

resource "aws_s3_bucket" "product_images" {
  bucket = "${var.project_name}-product-images-${var.environment}-${random_id.product_images.hex}"

  tags = {
    Name        = "${var.project_name}-product-images-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_s3_bucket" "vton_results" {
  bucket = "${var.project_name}-vton-results-${var.environment}-${random_id.vton_results.hex}"

  tags = {
    Name        = "${var.project_name}-vton-results-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_s3_bucket" "terraform_state" {
  bucket = "${var.project_name}-terraform-state-${var.environment}"

  tags = {
    Name        = "${var.project_name}-terraform-state-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_s3_bucket_public_access_block" "product_images" {
  bucket = aws_s3_bucket.product_images.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "vton_results" {
  bucket = aws_s3_bucket.vton_results.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_cors_configuration" "product_images" {
  bucket = aws_s3_bucket.product_images.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }
}

resource "aws_s3_bucket_cors_configuration" "vton_results" {
  bucket = aws_s3_bucket.vton_results.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "vton_results" {
  bucket = aws_s3_bucket.vton_results.id

  rule {
    id     = "expire-old-vton-results"
    status = "Enabled"

    expiration {
      days = 30
    }

    filter {}
  }
}
