import datetime
from threading import Timer

def notify_expiring_token(token, expiration_date, notification_method):
    """
    Checks if a token is expiring within 30 days and sends a notification
    using the specified method.

    Args:
        token (str): The token to be monitored.
        expiration_date (datetime.datetime): The expiration date of the token.
        notification_method (callable): A function that takes the token and
                                         expiration date as arguments and
                                         sends a notification.
    """

    delta = expiration_date - datetime.datetime.now()
    if delta.days <= 30:
        notification_method(token, expiration_date)

def send_email_notification(token, expiration_date):
    """
    Example notification method that sends an email (implementation details omitted).

    Args:
        token (str): The token that is expiring.
        expiration_date (datetime.datetime): The expiration date of the token.
    """

    # Replace with your email sending logic (e.g., using a library like smtplib)
    print(f"Sending email notification: Token '{token}' expires on {expiration_date}")

def send_log_notification(token, expiration_date):
    """
    Example notification method that logs a message (implementation details omitted).

    Args:
        token (str): The token that is expiring.
        expiration_date (datetime.datetime): The expiration date of the token.
    """

    # Replace with your logging logic (e.g., using a library like logging)
    print(f"Logging notification: Token '{token}' expires on {expiration_date}")

if __name__ == "__main__":
    # Read configuration (replace with your preferred method)
    token = input("Enter token: ")
    expiration_date_str = input("Enter expiration date (YYYY-MM-DD): ")
    expiration_date = datetime.datetime.strptime(expiration_date_str, "%Y-%m-%d")

    # Choose notification method (replace with your custom methods)
    notification_method = send_email_notification  # Or send_log_notification

    # Schedule notification check (replace with desired interval)
    notification_timer = Timer(3600, notify_expiring_token, args=(token, expiration_date, notification_method))
    notification_timer.start()

    print("Token monitoring started. Notification will be sent if expiration is within 30 days.")
