# AWS Free Tier Deployment Checklist

## Pre-Deployment (30 mins)

### AWS Account Setup
- [ ] AWS Account created (https://aws.amazon.com/free)
- [ ] Free Tier confirmed (check billing page)
- [ ] AWS CLI installed (`brew install awscli`)
- [ ] AWS credentials configured (`aws configure`)
- [ ] Default region set to `ap-south-1` or preferred region

### API Keys
- [ ] Groq API Key obtained (https://console.groq.com)
  - Store as: `export GROQ_API_KEY=gsk_...`
- [ ] OpenAI API Key obtained (https://platform.openai.com)
  - Store as: `export OPENAI_API_KEY=sk-proj-...`
- [ ] Keys added to `.env` file in project root

### Project Setup
- [ ] Project code cloned/ready
- [ ] All Python dependencies listed in `requirements.txt`
- [ ] Local testing done (API running on localhost)
- [ ] Frontend assets ready (if using frontend)

---

## Deployment Phases

### Phase 1: AWS Foundation (30 mins)
- [ ] S3 buckets created:
  - [ ] `endurance-dashboard-XXXXX`
  - [ ] `endurance-docs-XXXXX`
  - [ ] `endurance-lambda-deploy-XXXXX`
- [ ] RAG documents uploaded to S3
- [ ] DynamoDB tables created:
  - [ ] `endurance-sessions`
  - [ ] `endurance-feedback`
  - [ ] `endurance-audit-logs`
- [ ] IAM role created: `endurance-lambda-role`
- [ ] Permissions attached to role

**Estimate**: 15-30 mins  
**Manual Steps**: ~10 AWS CLI commands

---

### Phase 2: Package Lambda Functions (45 mins)
- [ ] Chatbot API packaged:
  - [ ] Virtual env created
  - [ ] Dependencies installed
  - [ ] Code copied
  - [ ] `lambda_handler.py` created
  - [ ] ZIP file created: `chatbot-layer.zip`
  - [ ] Uploaded to S3
- [ ] Endurance API packaged:
  - [ ] Virtual env created
  - [ ] Dependencies installed
  - [ ] Code copied
  - [ ] `lambda_handler.py` created
  - [ ] ZIP file created: `endurance-layer.zip`
  - [ ] Uploaded to S3

**Estimate**: 20-45 mins  
**Manual Steps**: Build process, ZIP, upload

---

### Phase 3: Deploy Lambda Functions (30 mins)
- [ ] Chatbot Lambda created:
  - [ ] Function name: `endurance-chatbot`
  - [ ] Runtime: Python 3.11
  - [ ] Memory: 1024 MB
  - [ ] Timeout: 60 seconds
  - [ ] Environment variables set
- [ ] Endurance API Lambda created:
  - [ ] Function name: `endurance-api`
  - [ ] Runtime: Python 3.11
  - [ ] Memory: 512 MB
  - [ ] Timeout: 30 seconds
  - [ ] Environment variables set
- [ ] Lambda functions tested locally

**Estimate**: 10-20 mins  
**Manual Steps**: ~5 AWS CLI commands

---

### Phase 4: API Gateway (25 mins)
- [ ] API Gateway created: `Endurance RAI API`
- [ ] Endpoints created:
  - [ ] POST `/chat` → Chatbot Lambda
  - [ ] POST `/evaluate` → Endurance Lambda
  - [ ] GET `/health` → Mock integration
- [ ] Lambda permissions granted for API Gateway
- [ ] API deployed to `prod` stage
- [ ] API endpoint URL obtained: `https://XXXXX.execute-api.ap-south-1.amazonaws.com/prod`

**Estimate**: 10-20 mins  
**Manual Steps**: ~10 AWS CLI commands

---

### Phase 5: Frontend Deployment (20 mins)
- [ ] Frontend built (if exists):
  - [ ] `npm install` ran
  - [ ] `npm run build` completed
  - [ ] `dist/` folder created
- [ ] Frontend uploaded to S3
- [ ] S3 bucket policy updated for public read
- [ ] CloudFront distribution created
- [ ] CDN domain obtained: `https://XXXXXXX.cloudfront.net`

**Estimate**: 10-15 mins  
**Manual Steps**: Build, upload, CloudFront config

---

### Phase 6: Configuration (10 mins)
- [ ] Lambda env vars updated with API Gateway URL
- [ ] Frontend env file created with API endpoints
- [ ] Frontend rebuilt and redeployed
- [ ] All connections tested

**Estimate**: 5-10 mins  
**Manual Steps**: Update configs, rebuild

---

## Testing

### After Each Phase
- [ ] Health check passes: `curl https://API_URL/health`
- [ ] DynamoDB tables accessible
- [ ] Lambda can read S3 documents
- [ ] Logs visible in CloudWatch

### Full Integration Tests
- [ ] Chat endpoint works: `curl -X POST https://API_URL/chat ...`
- [ ] Evaluation endpoint works: `curl -X POST https://API_URL/evaluate ...`
- [ ] Frontend loads: `https://CLOUDFRONT_URL`
- [ ] Frontend can call API endpoints
- [ ] Session data saved to DynamoDB
- [ ] Logs appear in CloudWatch

### Load Testing (Optional)
- [ ] Send 10 concurrent requests to `/chat`
- [ ] Send 10 concurrent requests to `/evaluate`
- [ ] Verify no Lambda timeouts
- [ ] Check CloudWatch metrics

---

## Post-Deployment

### Documentation
- [ ] Save API endpoint URL
- [ ] Save CloudFront domain
- [ ] Save bucket names
- [ ] Document Lambda function names
- [ ] Document DynamoDB table names

### Monitoring Setup
- [ ] CloudWatch dashboard created
- [ ] Billing alerts configured
- [ ] Lambda error rate monitored
- [ ] API Gateway throttling monitored

### Cleanup
- [ ] Delete any test Lambda functions
- [ ] Remove deployment ZIP files from S3
- [ ] Disable CloudFront if not using frontend
- [ ] Archive old logs if needed

---

## Budget Tracking

### Monthly Cost Estimate

| Service | Limit | Cost |
|---------|-------|------|
| Lambda | 1M requests | $0 |
| API Gateway | 1M requests | $0 |
| S3 | 5GB storage | $0 |
| DynamoDB | 25GB + 1B writes | $0 |
| CloudFront | 1TB transfer | $0 |
| CloudWatch | 5GB logs | $0 |
| External APIs | See below | See below |

### External API Costs
- Groq: **FREE** (5K requests/month)
- OpenAI Embeddings: **FREE** (First month with $5 credit)

### Actual Spend Check
- [ ] AWS Billing console reviewed
- [ ] No unexpected charges
- [ ] All services within free tier
- [ ] Monthly cost < $10

---

## Troubleshooting Checklist

### Lambda Issues
- [ ] Cold start > 5 seconds? → Acceptable for free tier
- [ ] Timeout errors? → Increase timeout, check memory
- [ ] "Module not found"? → Verify ZIP includes all dependencies
- [ ] Environment variables not accessible? → Re-check Lambda config

### API Gateway Issues
- [ ] 404 on endpoints? → Verify resource/method creation
- [ ] CORS errors? → Check FastAPI middleware
- [ ] Throttling? → Free tier allows 10K requests/second

### DynamoDB Issues
- [ ] Timeout writing to table? → Check IAM permissions
- [ ] Item size > 400KB? → Compress data or split
- [ ] Many write errors? → Use batch operations

### S3 Issues
- [ ] Documents not found? → Verify upload path matches
- [ ] Access denied? → Check IAM role permissions
- [ ] Slow uploads? → Use multipart upload for large files

### Frontend Issues
- [ ] Static assets not loading? → Check S3 bucket policy
- [ ] API calls fail? → Verify CORS headers
- [ ] Slow load times? → Enable CloudFront caching

---

## Quick Commands Reference

```bash
# Set environment variables
export GROQ_API_KEY=gsk_...
export OPENAI_API_KEY=sk-proj-...
export AWS_REGION=ap-south-1

# View deployment config
cat .deployment-config

# Check Lambda logs
aws logs tail /aws/lambda/endurance-chatbot --follow

# Check API Gateway logs
aws logs tail /aws/apigateway/endurance-api --follow

# Check DynamoDB item count
aws dynamodb scan --table-name endurance-sessions --select COUNT

# View S3 bucket size
aws s3 ls s3://endurance-docs-XXXXX --recursive --summarize

# Test API endpoint
curl https://API_ID.execute-api.ap-south-1.amazonaws.com/prod/health

# Monitor costs
aws ce get-cost-and-usage --time-period Start=2024-01-01,End=2024-01-31 --granularity MONTHLY --metrics BlendedCost
```

---

## Rollback Steps (if needed)

If something goes wrong:

```bash
# Delete Lambda functions
aws lambda delete-function --function-name endurance-chatbot
aws lambda delete-function --function-name endurance-api

# Delete API Gateway
aws apigateway delete-rest-api --rest-api-id XXXXX

# Delete S3 buckets (EMPTY FIRST!)
aws s3 rm s3://endurance-docs-XXXXX --recursive
aws s3 rb s3://endurance-docs-XXXXX

# Delete DynamoDB tables
aws dynamodb delete-table --table-name endurance-sessions

# Delete IAM role
aws iam delete-role --role-name endurance-lambda-role
```

---

## Timeline Summary

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 1: AWS Foundation | 30 mins | |
| Phase 2: Lambda Packaging | 45 mins | |
| Phase 3: Deploy Lambda | 30 mins | |
| Phase 4: API Gateway | 25 mins | |
| Phase 5: Frontend | 20 mins | |
| Phase 6: Configuration | 10 mins | |
| **Total** | **~2.5 hours** | |

---

**Start Date**: ___________  
**Completion Date**: ___________  
**Notes**: ___________

---

Generated: February 2026
