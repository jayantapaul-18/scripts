### **Overview: AWS Lambda Function to Trigger Teams Notifications Based on SNS Alerts**

This solution allows you to send notifications to Microsoft Teams when AWS SNS (Simple Notification Service) alerts are triggered. Here's the step-by-step process and full code for the Lambda function that integrates SNS alerts with Microsoft Teams.

### **Architecture Overview**

1. **AWS Services Involved:**
   - **Amazon SNS (Simple Notification Service)**: Receives alerts or messages from other AWS services (like CloudWatch alarms or custom events).
   - **AWS Lambda**: Acts as the backend that triggers the Teams notification when an SNS alert is received.
   - **Microsoft Teams**: Receives notifications via an **Incoming Webhook** that posts messages to a specified channel.

2. **Flow:**
   - An AWS service (e.g., CloudWatch Alarm) sends an alert to an SNS topic.
   - The SNS topic triggers an AWS Lambda function.
   - The Lambda function parses the SNS message and sends it to a Microsoft Teams webhook URL.
   - The message is posted to a specific Microsoft Teams channel, alerting the team.

### **Step-by-Step Process:**

#### **Step 1: Create a Microsoft Teams Incoming Webhook**

1. Open Microsoft Teams, navigate to the desired channel, and click on **"Connectors"**.
2. Search for **"Incoming Webhook"** and configure it.
3. Name the webhook and copy the webhook URL for later use. This URL is the endpoint where you'll send the SNS notifications.

#### **Step 2: Create an SNS Topic**

1. Go to the **Amazon SNS** console and create a new SNS topic.
   - Give it a name like `teams-alerts`.
2. Create a subscription to your SNS topic.
   - Choose **AWS Lambda** as the protocol and select your Lambda function once it's created.

#### **Step 3: Create the Lambda Function**

Create a Lambda function that listens for SNS messages and sends them to Microsoft Teams.

##### **Lambda Function Code (Python 3.x):**

```python
import json
import urllib3
import os

# Create an HTTP connection pool manager for sending requests
http = urllib3.PoolManager()

def send_teams_notification(message, webhook_url):
    """Sends a notification message to Microsoft Teams using the Incoming Webhook URL."""
    # Define the message structure that Microsoft Teams expects
    payload = {
        "text": message
    }
    
    encoded_data = json.dumps(payload).encode('utf-8')
    
    try:
        response = http.request(
            'POST',
            webhook_url,
            body=encoded_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"Teams notification response status: {response.status}")
        return response.status
    except Exception as e:
        print(f"Error sending notification to Microsoft Teams: {e}")
        return None

def lambda_handler(event, context):
    """Lambda handler to process SNS events and send them to Microsoft Teams."""
    # The incoming SNS message, this is passed in the event
    sns_message = event['Records'][0]['Sns']['Message']
    
    # Get the webhook URL from the Lambda environment variables
    teams_webhook_url = os.environ['TEAMS_WEBHOOK_URL']
    
    print(f"Received SNS message: {sns_message}")
    
    # Parse the SNS message (it's usually JSON-encoded)
    try:
        sns_message_json = json.loads(sns_message)
        message_to_send = json.dumps(sns_message_json, indent=4)  # Pretty print the message
    except json.JSONDecodeError:
        # If the message is not JSON, send it as-is
        message_to_send = sns_message
    
    # Send the notification to Microsoft Teams
    send_teams_notification(message_to_send, teams_webhook_url)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Notification sent to Microsoft Teams!')
    }
```

##### **Explanation:**
- **send_teams_notification function**: This sends the SNS message to the Microsoft Teams webhook URL.
- **lambda_handler function**: This is the entry point for the Lambda function. It extracts the SNS message from the event, formats it, and passes it to the `send_teams_notification` function.
- The webhook URL for Microsoft Teams is provided via **Lambda environment variables** (see Step 5).

#### **Step 4: Set Up the Lambda Function in AWS Console**

1. Go to the **AWS Lambda** console and click on **Create Function**.
   - Choose the option **Author from scratch**.
   - Name your function `sns-teams-notification`.
   - Select **Python 3.x** as the runtime.
   - Choose or create an appropriate execution role (this role needs permissions to log to CloudWatch and receive SNS events).

2. In the function code section, copy the Python code provided above.

#### **Step 5: Configure Environment Variables**

- In the **Configuration** tab of your Lambda function, under **Environment Variables**, add the following key-value pair:
  - **Key**: `TEAMS_WEBHOOK_URL`
  - **Value**: Paste your Microsoft Teams incoming webhook URL here.

#### **Step 6: Add SNS Trigger to Lambda Function**

1. Under the **Configuration** tab in Lambda, click **Add Trigger**.
2. Choose **SNS** as the trigger source.
3. Select the SNS topic (`teams-alerts`) you created earlier.
4. Save the configuration.

#### **Step 7: Test the Lambda Function**

1. You can test the Lambda function manually by triggering an SNS alert. Here's an example of manually publishing a test message to the SNS topic:
   ```bash
   aws sns publish --topic-arn arn:aws:sns:region:account-id:teams-alerts --message "This is a test message"
   ```

2. Check the Microsoft Teams channel to ensure that the message is received.

#### **Step 8: Monitor Logs**

- You can view the logs for the Lambda function in **CloudWatch Logs** to debug any issues.
- The logs will show details about the SNS messages received and the Teams notification status.

---

### **Full Architecture Diagram**

1. **SNS Topic**: Receives alerts from AWS services like CloudWatch, Auto Scaling, or custom applications.
2. **AWS Lambda**: The Lambda function listens for SNS messages and formats the message to send it to Teams.
3. **Microsoft Teams**: Uses an incoming webhook to receive alerts from the Lambda function.

```
    +------------------------+
    |                        |
    | AWS CloudWatch Alarm    |
    |                        |
    +------------------------+
               |
               | Trigger
               v
    +------------------------+
    |                        |
    |      Amazon SNS         |
    |    (teams-alerts)       |
    +------------------------+
               |
               | SNS Event
               v
    +------------------------+
    |                        |
    | AWS Lambda Function     |
    |  (sns-teams-notification)|
    +------------------------+
               |
               | HTTP POST
               v
    +------------------------+
    |                        |
    |  Microsoft Teams        |
    |   Incoming Webhook      |
    +------------------------+
```

---

### **Summary of Full Process:**
1. **AWS Service (e.g., CloudWatch Alarm)** sends an alert to an SNS topic.
2. The SNS topic triggers the **Lambda function**.
3. The Lambda function receives the SNS message, formats it, and sends a notification to the **Microsoft Teams webhook**.
4. The message is displayed in the Microsoft Teams channel as an alert.

This setup allows for real-time notifications in Microsoft Teams whenever an SNS event occurs, enhancing your alerting and monitoring capabilities.