import boto3
import logging
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s')

# Initialize S3 client
s3 = boto3.client('s3')

def get_all_buckets():
    """Returns a list of all S3 buckets in the AWS account."""
    try:
        response = s3.list_buckets()
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        return buckets
    except ClientError as e:
        logging.error(f"Error fetching bucket list: {e}")
        return []

def get_bucket_lifecycle_policy(bucket_name):
    """Fetches the lifecycle policy for a given bucket."""
    try:
        response = s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)
        lifecycle_rules = response['Rules']
        logging.info(f"Bucket {bucket_name} has lifecycle policy: {lifecycle_rules}")
        return lifecycle_rules
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':
            logging.info(f"Bucket {bucket_name} does not have a lifecycle policy.")
            return None
        else:
            logging.error(f"Error fetching lifecycle policy for {bucket_name}: {e}")
            return None

def get_bucket_tags(bucket_name):
    """Fetches the tags for a given bucket."""
    try:
        response = s3.get_bucket_tagging(Bucket=bucket_name)
        tags = response['TagSet']
        logging.info(f"Bucket {bucket_name} has tags: {tags}")
        return tags
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchTagSet':
            logging.info(f"Bucket {bucket_name} does not have any tags.")
            return None
        else:
            logging.error(f"Error fetching tags for {bucket_name}: {e}")
            return None

def audit_s3_buckets():
    """Audits S3 buckets that start with 'isp-' for lifecycle policy and tags."""
    buckets = get_all_buckets()
    if not buckets:
        logging.error("No buckets found or error in retrieving buckets.")
        return

    for bucket in buckets:
        # Only audit buckets that start with 'isp-'
        if bucket.startswith('isp-'):
            logging.info(f"\nAuditing bucket: {bucket}")
            # Check lifecycle policy
            lifecycle_policy = get_bucket_lifecycle_policy(bucket)
            if lifecycle_policy:
                logging.info(f"Bucket {bucket} Lifecycle Policy Details: {lifecycle_policy}")
            else:
                logging.info(f"Bucket {bucket} does not have a lifecycle policy.")

            # Check tags
            tags = get_bucket_tags(bucket)
            if tags:
                logging.info(f"Bucket {bucket} Tags: {tags}")
            else:
                logging.info(f"Bucket {bucket} does not have tags.")
        else:
            logging.info(f"Skipping bucket {bucket} as it does not start with 'isp-'.")

if __name__ == "__main__":
    audit_s3_buckets()