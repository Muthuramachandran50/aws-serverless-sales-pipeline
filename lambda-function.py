import json
import boto3
import csv
import io
import logging
from datetime import datetime
 
# Set up logging so we can see output in CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.INFO)
 
# AWS clients — boto3 lets Python talk to AWS services
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('sales_records')  # Must match your DynamoDB table name
 
def lambda_handler(event, context):
    """
    This function runs every time a file is uploaded to S3.
    event: contains info about WHICH file was uploaded (bucket name, file key)
    context: AWS runtime info (not used here)
    """
    logger.info(f'Received event: {json.dumps(event)}')
 
    # ── Step A: Extract bucket name and file name from the S3 event ──
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    file_key = event['Records'][0]['s3']['object']['key']
 
    logger.info(f'Processing file: {file_key} from bucket: {bucket_name}')
 
    # ── Step B: Only process .csv files ──
    if not file_key.endswith('.csv'):
        logger.warning(f'File {file_key} is not a CSV. Skipping.')
        return {'statusCode': 200, 'body': 'Not a CSV file, skipped.'}
 
    # ── Step C: Download the CSV file from S3 into memory ──
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        csv_content = response['Body'].read().decode('utf-8')
        logger.info('Successfully read CSV from S3')
    except Exception as e:
        logger.error(f'Error reading file from S3: {str(e)}')
        raise e
 
    # ── Step D: Parse CSV and insert each row into DynamoDB ──
    csv_reader = csv.DictReader(io.StringIO(csv_content))
    success_count = 0
    error_count = 0
 
    for row in csv_reader:
        try:
            # Build the DynamoDB item from the CSV row
            item = {
                'sale_id':     row.get('sale_id', '').strip(),
                'product':     row.get('product', '').strip(),
                'quantity':    int(row.get('quantity', 0)),
                'price':       str(row.get('price', '0')).strip(),
                'customer':    row.get('customer', '').strip(),
                'sale_date':   row.get('sale_date', '').strip(),
                'region':      row.get('region', '').strip(),
                # Add metadata — when and from where was this record loaded
                'loaded_at':   datetime.utcnow().isoformat(),
                'source_file': file_key
            }
 
            # Validate: sale_id must not be empty
            if not item['sale_id']:
                logger.warning(f'Skipping row with empty sale_id: {row}')
                error_count += 1
                continue
 
            # Insert into DynamoDB
            table.put_item(Item=item)
            success_count += 1
            logger.info(f'Inserted sale_id: {item["sale_id"]}')
 
        except Exception as e:
            logger.error(f'Error inserting row {row}: {str(e)}')
            error_count += 1
 
    # ── Step E: Return a summary ──
    summary = {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Processing complete',
            'file_processed': file_key,
            'records_inserted': success_count,
            'records_failed': error_count
        })
    }
    logger.info(f'Summary: {summary}')
    return summary
