import boto3

def download_from_s3(bucket_name, object_key, download_path):
    # Initialize boto3 S3 client
    s3 = boto3.client('s3')
    
    # Download the object from S3 to the specified path
    s3.download_file(bucket_name, object_key, download_path)
    print(f"Downloaded {object_key} from {bucket_name} to {download_path}")

if __name__ == "__main__":
    # Replace these with your S3 details
    BUCKET_NAME = "your-bucket-name"
    OBJECT_KEY = "path/to/your/object"
    DOWNLOAD_PATH = "/app/data/your_object"

    download_from_s3(BUCKET_NAME, OBJECT_KEY, DOWNLOAD_PATH)
