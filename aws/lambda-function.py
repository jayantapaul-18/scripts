import json
import boto3

sns_topic_arn = 'YOUR_SNS_TOPIC_ARN'
sns_client = boto3.client('sns')

def lambda_handler(event, context):
    for record in event['Records']:
        if record['eventName'] == 'CreateRole':
            role_arn = record['responseElements']['role']['arn']
            message = f"IAM Role Created: {role_arn}"
            sns_client.publish(TopicArn=sns_topic_arn, Message=message)
