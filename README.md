# aws-serverless-sales-pipeline
## Architecture
CSV Upload → S3 → Lambda (Python) → DynamoDB → Athena

## Services Used
| Service | Purpose |
|---|---|
| S3 | Store raw CSV files |
| Lambda | Auto-process on upload |
| DynamoDB | Store sales records |
| Athena | SQL analytics on S3 |
| IAM | Security & permissions |

## How It Works
1. Sales CSV file is uploaded to S3 bucket
2. S3 trigger automatically invokes Lambda
3. Lambda reads CSV and inserts each row into DynamoDB
4. Athena queries raw CSV in S3 using SQL

## Tech Stack
- Python 3.12
- AWS S3, Lambda, DynamoDB, Athena, IAM
- boto3 library

## Sample Athena Query
SELECT region, COUNT(*) as total_sales
FROM sales_db.sales_data
GROUP BY region
ORDER BY total_sales DESC;
