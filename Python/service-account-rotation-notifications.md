Here is a Python script that reads the service account configuration from a file (for example, a JSON or YAML file), checks if the secret expiration date is within 15 days, sends a notification email, and logs the audit event.

We’ll use the following libraries:

	•	smtplib for sending email notifications.
	•	logging for logging the audit events.
	•	datetime for date calculations.
	•	json or yaml to read the configuration file.

Step 1: Configuration File

Let’s assume we have a JSON configuration file service_accounts.json:

[
    {
        "name": "service-account-1",
        "secret_expiration": "2024-10-18",
        "notification_email": "admin@example.com",
        "last_rotation": "2024-07-01",
        "poc": "John Doe",
        "notes": "Important service account"
    },
    {
        "name": "service-account-2",
        "secret_expiration": "2024-10-28",
        "notification_email": "admin2@example.com",
        "last_rotation": "2024-08-15",
        "poc": "Jane Doe",
        "notes": "Used for external API"
    }
]

Step 2: Python Script to Monitor and Notify

import json
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText

# Configuring logging
logging.basicConfig(filename="service_account_audit.log", 
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Function to send email notifications
def send_email(to_email, subject, body):
    from_email = "no-reply@example.com"  # Email address for notifications
    smtp_server = "smtp.example.com"  # Replace with your SMTP server
    smtp_port = 587  # Replace with your SMTP server port
    smtp_user = "user@example.com"  # SMTP server login
    smtp_pass = "password"  # SMTP server password

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, to_email, msg.as_string())
            logging.info(f"Notification sent to {to_email} for service account expiry alert")
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}. Error: {e}")

# Function to check expiration and trigger notifications
def check_expiration_and_notify(service_accounts):
    today = datetime.now()
    warning_period = timedelta(days=15)

    for account in service_accounts:
        expiration_date = datetime.strptime(account['secret_expiration'], '%Y-%m-%d')
        time_to_expiration = expiration_date - today

        if time_to_expiration <= warning_period and time_to_expiration > timedelta(0):
            subject = f"Service Account {account['name']} Expiration Warning"
            body = (f"Service Account: {account['name']}\n"
                    f"Expiration Date: {account['secret_expiration']}\n"
                    f"Point of Contact: {account['poc']}\n"
                    f"Notes: {account['notes']}\n\n"
                    "The secret for this account is expiring soon. Please take action.")
            
            # Trigger email notification
            send_email(account['notification_email'], subject, body)
            
            # Log the event
            logging.info(f"Notified {account['notification_email']} about the upcoming expiration of {account['name']} on {account['secret_expiration']}")
        
        elif time_to_expiration <= timedelta(0):
            logging.warning(f"Service account {account['name']} has already expired on {account['secret_expiration']}")

# Function to read the configuration file
def load_service_accounts(config_file):
    try:
        with open(config_file, 'r') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Error reading configuration file: {e}")
        return []

# Main function to orchestrate the monitoring
def main():
    service_accounts = load_service_accounts("service_accounts.json")
    if service_accounts:
        check_expiration_and_notify(service_accounts)
    else:
        logging.error("No service accounts found to process.")

if __name__ == "__main__":
    main()

Step 3: Explanation

	1.	Configuration:
	•	We assume service accounts are stored in a JSON file (service_accounts.json).
	•	Each service account entry has attributes such as name, secret_expiration, notification_email, last_rotation, poc, and notes.
	2.	Logging:
	•	A log file (service_account_audit.log) will record every time the script checks for expirations and sends notifications.
	•	If there are errors (e.g., reading the configuration file or sending an email), those will also be logged.
	3.	Email Notification:
	•	When a service account’s secret expiration is within 15 days, an email is sent to the specified contact using the smtplib library.
	•	The script assumes an SMTP server is available and configured correctly.
	4.	Expiration Check:
	•	The script calculates the number of days until the secret expiration for each service account.
	•	If it’s 15 days or less, it triggers an email notification and logs the action.
	•	If the expiration date has passed, a warning is logged.
	5.	Audit Logging:
	•	Every notification and important event (such as expired service accounts) is logged for auditing purposes.

Step 4: Configuration File

You can adapt this configuration to use other formats, such as YAML, by simply modifying the file reading part of the script.

Step 5: Scheduling the Script

To run this script periodically, you can use a cron job (on Linux/Mac) or Task Scheduler (on Windows) to check the service accounts daily.

For example, to run the script daily at midnight, you can add a cron job:

0 0 * * * /usr/bin/python3 /path/to/script.py

This setup ensures that the service accounts are continuously monitored, and you receive notifications before their secrets expire.