import boto3
import pymysql

# Retrieve the database endpoint and credentials from AWS Secrets Manager (optional)
secrets_client = boto3.client('secretsmanager', region_name='your-region')
secret_value = secrets_client.get_secret_value(SecretId='your-secret-id')
secret = json.loads(secret_value['SecretString'])

# Connect to Aurora MySQL database
connection = pymysql.connect(
    host=secret['host'],
    user=secret['username'],
    password=secret['password'],
    database='your-database-name',
    port=secret['port']
)

try:
    with connection.cursor() as cursor:
        # Execute a simple SQL query
        sql = "SELECT VERSION()"
        cursor.execute(sql)
        result = cursor.fetchone()
        print("Database version:", result)
finally:
    connection.close()
