import boto3
from datetime import datetime, timedelta

# Set up the CloudWatch Logs client
logs_client = boto3.client('logs', region_name='your-region')  # Replace 'your-region' with the AWS region

# Replace with your CloudWatch log group name (usually starts with '/aws/aes/domains/...')
log_group_name = '/aws/aes/domains/your-domain-name/logs'  # Replace 'your-domain-name' with your OpenSearch domain

def get_opensearch_logs(log_group_name, start_time, end_time):
    try:
        # Convert start and end times to the required format (milliseconds since epoch)
        start_time_ms = int(start_time.timestamp() * 1000)
        end_time_ms = int(end_time.timestamp() * 1000)
        
        # Retrieve log streams from the specified log group
        log_streams = logs_client.describe_log_streams(logGroupName=log_group_name, orderBy='LastEventTime', descending=True)
        
        logs = []
        for log_stream in log_streams['logStreams']:
            log_stream_name = log_stream['logStreamName']
            
            # Get log events for each log stream
            response = logs_client.get_log_events(
                logGroupName=log_group_name,
                logStreamName=log_stream_name,
                startTime=start_time_ms,
                endTime=end_time_ms,
                limit=50  # Adjust the limit as needed
            )
            
            for event in response['events']:
                logs.append(event['message'])
        
        return logs

    except Exception as e:
        print(f"Error retrieving logs: {e}")
        return None

# Define the time range for retrieving logs (e.g., last 1 hour)
end_time = datetime.now()
start_time = end_time - timedelta(hours=1)

# Retrieve logs
logs = get_opensearch_logs(log_group_name, start_time, end_time)

if logs:
    print("OpenSearch Logs:")
    for log in logs:
        print(log)
else:
    print("No logs found or an error occurred.")
