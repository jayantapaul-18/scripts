import boto3

def get_cloudwatch_events(rule_name, max_items=10):
    # Create CloudWatch Events client
    cloudwatch_events_client = boto3.client('events')

    # Retrieve events from the specified rule
    response = cloudwatch_events_client.list_rule_names_by_target(
        TargetArn=f"arn:aws:events:us-east-1:127245076836:event-bus/target-test",
        Limit=max_items
    )

    # Print information about each event
    for rule in response['RuleNames']:
        print(f"Rule Name: {rule}")

        # Describe the rule to get more details
        rule_details = cloudwatch_events_client.describe_rule(Name=rule)
        print(f"- Description: {rule_details.get('Description', 'N/A')}")
        print(f"- State: {rule_details['State']}")
        print(f"- Event Pattern: {rule_details['EventPattern']}")
        print("\n")

if __name__ == "__main__":
    # Replace 'your-rule-name' with the actual name of your CloudWatch Events rule
    rule_name = 'aws-event'
    
    # Replace '10' with the desired maximum number of events to retrieve
    max_items = 10
    
    get_cloudwatch_events(rule_name, max_items)
