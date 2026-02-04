#!/bin/bash

###############################################################################
# AWS DEPLOYMENT SCRIPT - Endurance RAG Application
# This script automates the AWS free tier deployment
# Run: bash aws-deploy.sh
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Validation
validate_prerequisites() {
    print_header "VALIDATING PREREQUISITES"

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not installed"
        echo "Install with: brew install awscli"
        exit 1
    fi
    print_success "AWS CLI installed"

    # Check Python
    if ! command -v python3.11 &> /dev/null; then
        print_warning "Python 3.11 not found, using available python3"
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python3.11"
    fi
    print_success "Python available: $PYTHON_CMD"

    # Check git
    if ! command -v git &> /dev/null; then
        print_error "Git not installed"
        exit 1
    fi
    print_success "Git installed"

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured"
        echo "Run: aws configure"
        exit 1
    fi
    print_success "AWS credentials configured"

    # Check API keys
    if [ -z "$GROQ_API_KEY" ]; then
        print_error "GROQ_API_KEY not set"
        echo "Get it from: https://console.groq.com"
        exit 1
    fi
    print_success "GROQ_API_KEY is set"

    if [ -z "$OPENAI_API_KEY" ]; then
        print_error "OPENAI_API_KEY not set"
        echo "Get it from: https://platform.openai.com"
        exit 1
    fi
    print_success "OPENAI_API_KEY is set"
}

# Set up environment
setup_environment() {
    print_header "SETTING UP ENVIRONMENT"

    # Detect AWS region
    AWS_REGION=$(aws configure get region)
    if [ -z "$AWS_REGION" ]; then
        AWS_REGION="ap-south-1"
        print_warning "No default region set, using $AWS_REGION"
    fi
    print_success "AWS Region: $AWS_REGION"

    # Get AWS Account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    print_success "AWS Account ID: $AWS_ACCOUNT_ID"

    # Generate unique suffix
    SUFFIX=$(date +%s)
    print_success "Deployment Suffix: $SUFFIX"

    # Create bucket names
    DASH_BUCKET="endurance-dashboard-${SUFFIX}"
    DOCS_BUCKET="endurance-docs-${SUFFIX}"
    DEPLOY_BUCKET="endurance-lambda-deploy-${SUFFIX}"

    print_success "Bucket Names:"
    echo "  - $DASH_BUCKET"
    echo "  - $DOCS_BUCKET"
    echo "  - $DEPLOY_BUCKET"

    # Save configuration
    cat > .deployment-config << EOF
AWS_REGION=$AWS_REGION
AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID
DASH_BUCKET=$DASH_BUCKET
DOCS_BUCKET=$DOCS_BUCKET
DEPLOY_BUCKET=$DEPLOY_BUCKET
SUFFIX=$SUFFIX
EOF
    print_success "Configuration saved to .deployment-config"
}

# Phase 1: Create S3 Buckets
create_s3_buckets() {
    print_header "PHASE 1: CREATING S3 BUCKETS"

    # Dashboard bucket
    if aws s3 ls "s3://$DASH_BUCKET" 2>/dev/null; then
        print_warning "Dashboard bucket already exists: $DASH_BUCKET"
    else
        aws s3 mb "s3://$DASH_BUCKET" --region "$AWS_REGION"
        print_success "Created: $DASH_BUCKET"
    fi

    # Docs bucket
    if aws s3 ls "s3://$DOCS_BUCKET" 2>/dev/null; then
        print_warning "Docs bucket already exists: $DOCS_BUCKET"
    else
        aws s3 mb "s3://$DOCS_BUCKET" --region "$AWS_REGION"
        print_success "Created: $DOCS_BUCKET"
    fi

    # Deploy bucket
    if aws s3 ls "s3://$DEPLOY_BUCKET" 2>/dev/null; then
        print_warning "Deploy bucket already exists: $DEPLOY_BUCKET"
    else
        aws s3 mb "s3://$DEPLOY_BUCKET" --region "$AWS_REGION"
        print_success "Created: $DEPLOY_BUCKET"
    fi

    # Enable versioning
    aws s3api put-bucket-versioning \
        --bucket "$DASH_BUCKET" \
        --versioning-configuration Status=Enabled \
        --region "$AWS_REGION" 2>/dev/null || true
    print_success "Versioning enabled"
}

# Phase 1b: Upload RAG Documents
upload_rag_documents() {
    print_header "UPLOADING RAG DOCUMENTS TO S3"

    DOCS_PATH="./chatbot/rag_docs"
    
    if [ ! -d "$DOCS_PATH" ]; then
        print_warning "RAG docs directory not found at $DOCS_PATH"
        return
    fi

    aws s3 sync "$DOCS_PATH/" "s3://$DOCS_BUCKET/" \
        --region "$AWS_REGION"
    
    print_success "RAG documents uploaded"
    
    # List uploaded files
    echo "Files in S3:"
    aws s3 ls "s3://$DOCS_BUCKET/" --region "$AWS_REGION"
}

# Phase 2: Create DynamoDB Tables
create_dynamodb_tables() {
    print_header "PHASE 2: CREATING DYNAMODB TABLES"

    # Sessions table
    if aws dynamodb describe-table --table-name endurance-sessions --region "$AWS_REGION" 2>/dev/null; then
        print_warning "Sessions table already exists"
    else
        aws dynamodb create-table \
            --table-name endurance-sessions \
            --attribute-definitions \
                AttributeName=session_id,AttributeType=S \
                AttributeName=timestamp,AttributeType=N \
            --key-schema \
                AttributeName=session_id,KeyType=HASH \
                AttributeName=timestamp,KeyType=RANGE \
            --billing-mode PAY_PER_REQUEST \
            --region "$AWS_REGION"
        print_success "Created: endurance-sessions"
    fi

    # Feedback table
    if aws dynamodb describe-table --table-name endurance-feedback --region "$AWS_REGION" 2>/dev/null; then
        print_warning "Feedback table already exists"
    else
        aws dynamodb create-table \
            --table-name endurance-feedback \
            --attribute-definitions \
                AttributeName=feedback_id,AttributeType=S \
            --key-schema \
                AttributeName=feedback_id,KeyType=HASH \
            --billing-mode PAY_PER_REQUEST \
            --region "$AWS_REGION"
        print_success "Created: endurance-feedback"
    fi

    # Audit logs table
    if aws dynamodb describe-table --table-name endurance-audit-logs --region "$AWS_REGION" 2>/dev/null; then
        print_warning "Audit logs table already exists"
    else
        aws dynamodb create-table \
            --table-name endurance-audit-logs \
            --attribute-definitions \
                AttributeName=log_id,AttributeType=S \
                AttributeName=timestamp,AttributeType=N \
            --key-schema \
                AttributeName=log_id,KeyType=HASH \
                AttributeName=timestamp,KeyType=RANGE \
            --billing-mode PAY_PER_REQUEST \
            --time-to-live-specification AttributeName=ttl,Enabled=true \
            --region "$AWS_REGION"
        print_success "Created: endurance-audit-logs"
    fi
}

# Phase 3: Create IAM Role
create_iam_role() {
    print_header "PHASE 3: CREATING IAM ROLE"

    # Check if role exists
    if aws iam get-role --role-name endurance-lambda-role 2>/dev/null; then
        print_warning "IAM role already exists"
        ROLE_ARN=$(aws iam get-role --role-name endurance-lambda-role --query 'Role.Arn' --output text)
    else
        # Create trust policy
        cat > /tmp/trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

        # Create role
        aws iam create-role \
            --role-name endurance-lambda-role \
            --assume-role-policy-document file:///tmp/trust-policy.json
        
        # Create inline policy
        cat > /tmp/lambda-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/endurance-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::endurance-docs-*",
        "arn:aws:s3:::endurance-docs-*/*"
      ]
    }
  ]
}
EOF

        aws iam put-role-policy \
            --role-name endurance-lambda-role \
            --policy-name endurance-lambda-policy \
            --policy-document file:///tmp/lambda-policy.json
        
        ROLE_ARN=$(aws iam get-role --role-name endurance-lambda-role --query 'Role.Arn' --output text)
        print_success "Created: endurance-lambda-role"
    fi

    echo "Role ARN: $ROLE_ARN"
    echo "ROLE_ARN=$ROLE_ARN" >> .deployment-config
}

# Main execution
main() {
    print_header "ENDURANCE RAG - AWS FREE TIER DEPLOYMENT"
    echo "Starting deployment at $(date)"

    validate_prerequisites
    setup_environment

    # Load config
    source .deployment-config

    create_s3_buckets
    upload_rag_documents
    create_dynamodb_tables
    create_iam_role

    print_header "DEPLOYMENT PHASE 1-3 COMPLETE ✓"
    echo -e "\n${GREEN}Configuration saved to: .deployment-config${NC}"
    echo -e "${GREEN}Next steps:${NC}"
    echo "1. Review .deployment-config"
    echo "2. Run 'bash aws-deploy-lambdas.sh' to deploy Lambda functions"
    echo "3. Run 'bash aws-deploy-apigateway.sh' to create API Gateway"
    echo ""
}

# Run main
main "$@"
