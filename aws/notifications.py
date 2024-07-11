import boto3

def get_cloudwatch_alarms(region_name='us-west-2'):
    # Create a CloudWatch client
    cloudwatch = boto3.client('cloudwatch', region_name=region_name)
    
    # Retrieve alarms
    response = cloudwatch.describe_alarms()
    
    alarms = response['MetricAlarms']
    return alarms

if __name__ == '__main__':
    # Replace 'us-west-2' with your AWS region
    region = 'us-west-2'
    alarms = get_cloudwatch_alarms(region)
    for alarm in alarms:
        print(f"Alarm Name: {alarm['AlarmName']}")
        print(f"State: {alarm['StateValue']}")
        print(f"Metric: {alarm['MetricName']}")
        print(f"Namespace: {alarm['Namespace']}")
        print('-' * 40)
