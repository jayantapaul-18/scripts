# notification_script.py
import sys

def send_notification(project_id):
    # Implement your notification logic here
    print(f"Sending notification for project {project_id}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python notification_script.py <project_id>")
        sys.exit(1)

    project_id = sys.argv[1]
    send_notification(project_id)
