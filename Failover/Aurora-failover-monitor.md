Creating a failover script for an AWS Aurora RDS Global Cluster involves monitoring the health and status of the database instances and triggering a failover if needed. Below is a Python-based solution that uses the AWS SDK (boto3) to perform failover, monitor health status at regular intervals, log all the steps, and generate metrics that can be used for dashboards (for example, by pushing metrics to Amazon CloudWatch).

Step 1: Install Dependencies

Make sure you have the necessary packages installed:

pip install boto3

Step 2: Python Script for Aurora Global Cluster Failover and Monitoring

import boto3
import time
import logging
from datetime import datetime

# AWS clients
rds_client = boto3.client('rds')
cloudwatch_client = boto3.client('cloudwatch')

# Set up logging
logging.basicConfig(filename='aurora_failover.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variables
GLOBAL_DB_CLUSTER_IDENTIFIER = "your-global-db-cluster-identifier"
REGION = "your-secondary-region"
CHECK_INTERVAL = 15  # seconds

# Function to monitor DB status
def check_db_status():
    try:
        response = rds_client.describe_db_clusters(DBClusterIdentifier=GLOBAL_DB_CLUSTER_IDENTIFIER)
        cluster = response['DBClusters'][0]
        status = cluster['Status']
        logging.info(f"DB Cluster Status: {status}")
        return status
    except Exception as e:
        logging.error(f"Error checking DB status: {e}")
        return None

# Function to monitor DB instance health
def check_db_instance_health():
    try:
        response = rds_client.describe_db_instances()
        unhealthy_instances = []
        
        for instance in response['DBInstances']:
            db_instance_id = instance['DBInstanceIdentifier']
            instance_status = instance['DBInstanceStatus']
            logging.info(f"DB Instance {db_instance_id} Status: {instance_status}")

            if instance_status != "available":
                unhealthy_instances.append(db_instance_id)
        
        return unhealthy_instances
    except Exception as e:
        logging.error(f"Error checking DB instance health: {e}")
        return []

# Function to trigger failover
def trigger_failover():
    try:
        logging.info("Triggering failover...")
        response = rds_client.failover_global_cluster(
            GlobalClusterIdentifier=GLOBAL_DB_CLUSTER_IDENTIFIER,
            TargetDbClusterIdentifier=GLOBAL_DB_CLUSTER_IDENTIFIER + "-secondary"
        )
        logging.info("Failover triggered successfully")
    except Exception as e:
        logging.error(f"Error triggering failover: {e}")

# Function to publish metrics to CloudWatch
def publish_metrics(healthy_instances, unhealthy_instances):
    try:
        cloudwatch_client.put_metric_data(
            Namespace='AuroraGlobalCluster',
            MetricData=[
                {
                    'MetricName': 'HealthyInstances',
                    'Dimensions': [{'Name': 'GlobalCluster', 'Value': GLOBAL_DB_CLUSTER_IDENTIFIER}],
                    'Timestamp': datetime.utcnow(),
                    'Value': healthy_instances,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'UnhealthyInstances',
                    'Dimensions': [{'Name': 'GlobalCluster', 'Value': GLOBAL_DB_CLUSTER_IDENTIFIER}],
                    'Timestamp': datetime.utcnow(),
                    'Value': unhealthy_instances,
                    'Unit': 'Count'
                }
            ]
        )
        logging.info(f"Metrics published: {healthy_instances} healthy, {unhealthy_instances} unhealthy")
    except Exception as e:
        logging.error(f"Error publishing metrics to CloudWatch: {e}")

# Main monitoring loop
def monitor_and_failover():
    while True:
        logging.info("Starting health check...")

        # Check global DB cluster status
        status = check_db_status()

        # Check the health of DB instances
        unhealthy_instances = check_db_instance_health()

        # Check for failover condition (e.g., status not available or unhealthy instances)
        if status != "available" or len(unhealthy_instances) > 0:
            logging.warning(f"Cluster unhealthy: status={status}, unhealthy instances={unhealthy_instances}")
            trigger_failover()
        else:
            logging.info("Cluster is healthy.")

        # Publish metrics to CloudWatch
        publish_metrics(healthy_instances=len(check_db_instance_health()), unhealthy_instances=len(unhealthy_instances))

        # Sleep before the next check
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    monitor_and_failover()

Key Components of the Script

	1.	check_db_status(): This function retrieves the status of the global Aurora DB cluster using the describe_db_clusters() method. It logs the status and returns it.
	2.	check_db_instance_health(): This function retrieves the status of each individual DB instance using the describe_db_instances() method. It logs the instance status and returns a list of unhealthy instances (those that are not “available”).
	3.	trigger_failover(): This function triggers a failover to the secondary region using the failover_global_cluster() method. It targets the secondary region cluster for failover.
	4.	publish_metrics(): This function publishes two custom metrics (HealthyInstances and UnhealthyInstances) to Amazon CloudWatch for dashboarding. Metrics are tagged with the global Aurora cluster identifier.
	5.	Logging: Each step is logged, including the status checks, failover initiation, and metrics publishing. The logs are saved to a file aurora_failover.log.
	6.	Monitoring Loop: The script continuously monitors the status of the global DB cluster and instances in a 15-second interval. If a failover condition is detected (e.g., the cluster is not “available” or unhealthy instances are found), a failover is triggered.

Step 3: Configurations

	1.	Set the GLOBAL_DB_CLUSTER_IDENTIFIER: Replace "your-global-db-cluster-identifier" with your actual global Aurora DB cluster identifier.
	2.	Set the REGION: Replace "your-secondary-region" with the secondary region where you want the failover to occur.
	3.	CloudWatch Namespace: Customize the CloudWatch namespace (AuroraGlobalCluster) as needed.

Step 4: Create CloudWatch Dashboard

You can now create a dashboard in Amazon CloudWatch to visualize the metrics (HealthyInstances and UnhealthyInstances) that the script sends.

	1.	Go to CloudWatch Console.
	2.	Create a new dashboard and add widgets for the custom metrics (AuroraGlobalCluster namespace).
	3.	Choose the metrics like HealthyInstances and UnhealthyInstances to monitor the health of the Aurora DB cluster in real-time.

Step 5: Run the Script

Make sure the script runs from an EC2 instance, Lambda, or any other machine with the necessary IAM permissions to access RDS and CloudWatch. You’ll need:

	•	rds:DescribeDBClusters
	•	rds:DescribeDBInstances
	•	rds:FailoverGlobalCluster
	•	cloudwatch:PutMetricData

python aurora_failover.py

Step 6: IAM Permissions

Ensure the AWS credentials used by this script have the necessary IAM permissions for the operations:

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "rds:DescribeDBClusters",
                "rds:DescribeDBInstances",
                "rds:FailoverGlobalCluster",
                "cloudwatch:PutMetricData"
            ],
            "Resource": "*"
        }
    ]
}

Conclusion

This Python script automates the monitoring of an AWS Aurora RDS global cluster, logs the status of the DB instances, triggers failovers if unhealthy conditions are detected, and publishes health metrics to Amazon CloudWatch for dashboarding.