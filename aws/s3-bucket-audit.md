Below is a Python script that audits all S3 buckets in an AWS account to check whether they have a lifecycle policy and tags. If a lifecycle policy exists, the script fetches the details of that policy. The script uses the boto3 AWS SDK to interact with AWS S3 services.

Prerequisites

	•	boto3 must be installed:

pip install boto3


	•	AWS credentials must be configured locally or using environment variables.

Python Script: S3 Bucket Lifecycle and Tagging Audit

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
    """Audits all S3 buckets for lifecycle policy and tags."""
    buckets = get_all_buckets()
    if not buckets:
        logging.error("No buckets found or error in retrieving buckets.")
        return

    for bucket in buckets:
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

if __name__ == "__main__":
    audit_s3_buckets()

Explanation:

	1.	S3 Client Initialization:
The boto3.client('s3') initializes an S3 client using AWS credentials.
	2.	Fetching All Buckets:
The get_all_buckets() function calls list_buckets() to retrieve all the S3 buckets in the AWS account.
	3.	Checking Lifecycle Policy:
The get_bucket_lifecycle_policy(bucket_name) function calls get_bucket_lifecycle_configuration() to check if the bucket has a lifecycle policy. If the policy exists, the details are printed, and if it doesn’t, it logs that no lifecycle policy is configured for the bucket.
	4.	Checking Tags:
The get_bucket_tags(bucket_name) function calls get_bucket_tagging() to retrieve the bucket’s tags. It handles cases where no tags are present and logs the result.
	5.	Auditing All Buckets:
The audit_s3_buckets() function iterates through each bucket, checks for lifecycle policies and tags, and logs the results.
	6.	Logging:
All audit results (success and errors) are logged using Python’s logging module.

Sample Output:

For a bucket with a lifecycle policy and tags, the output might look like:

INFO:2024-10-03 10:00:00: Auditing bucket: my-s3-bucket-1
INFO:2024-10-03 10:00:00: Bucket my-s3-bucket-1 has lifecycle policy: [{'ID': 'Rule1', 'Prefix': '', 'Status': 'Enabled', ...}]
INFO:2024-10-03 10:00:00: Bucket my-s3-bucket-1 Tags: [{'Key': 'Environment', 'Value': 'Production'}, {'Key': 'Owner', 'Value': 'DevOps Team'}]

If the bucket doesn’t have a lifecycle policy or tags, the output might look like:

INFO:2024-10-03 10:05:00: Bucket my-s3-bucket-2 does not have a lifecycle policy.
INFO:2024-10-03 10:05:00: Bucket my-s3-bucket-2 does not have any tags.

Scheduling and Automating the Script:

You can run this script periodically (e.g., using a cron job on Linux or Task Scheduler on Windows) to continuously monitor and audit the lifecycle policies and tags of S3 buckets in your AWS account.