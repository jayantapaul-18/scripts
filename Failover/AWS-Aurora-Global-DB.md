To handle a failover of an **AWS Aurora PostgreSQL Global Database** and periodically monitor the health status of the database, you can use the **`boto3`** SDK for Python. This script will:
1. Trigger a global database failover.
2. Periodically check and retrieve the status of the database cluster.
3. Format the status in JSON to integrate with a monitoring system.

### Pre-requisites:
1. Install the required Python packages:
   ```bash
   pip install boto3
   ```

2. Set up AWS credentials and region either via AWS CLI or environment variables.

### 1. **Failover Script for Global Database**
The following script will trigger a failover for an Aurora PostgreSQL Global Database. In a global database, the failover typically happens between the secondary regions when the primary region goes down.

```python
import boto3
from botocore.exceptions import ClientError

def failover_global_database(global_db_identifier, target_region):
    client = boto3.client('rds')

    try:
        response = client.failover_global_cluster(
            GlobalClusterIdentifier=global_db_identifier,
            TargetDbClusterIdentifier=target_region
        )

        print(f"Failover initiated to region: {target_region}")
        return response
    except ClientError as e:
        print(f"Error triggering failover: {e}")
        return None

if __name__ == "__main__":
    # Replace with your Global DB Identifier and target DB Cluster (region)
    global_db_identifier = 'your-global-db-identifier'
    target_region_cluster_identifier = 'your-target-region-cluster-identifier'
    
    # Trigger failover
    failover_global_database(global_db_identifier, target_region_cluster_identifier)
```

### 2. **Monitoring Script for Health Status**
This script will fetch the health and status of the Aurora PostgreSQL Global Database cluster and return it in JSON format. The script can be run periodically using a scheduler like cron or AWS Lambda.

```python
import boto3
import json
import time
from botocore.exceptions import ClientError

def get_global_db_status(global_db_identifier):
    client = boto3.client('rds')

    try:
        response = client.describe_global_clusters(
            GlobalClusterIdentifier=global_db_identifier
        )

        global_cluster_info = response['GlobalClusters'][0]
        cluster_members = []

        # Gather information on each member cluster in different regions
        for cluster in global_cluster_info['GlobalClusterMembers']:
            cluster_info = {
                'DBClusterArn': cluster['DBClusterArn'],
                'Region': cluster['DBClusterArn'].split(':')[3],
                'IsWriter': cluster['IsWriter'],
                'Status': cluster['Status']
            }
            cluster_members.append(cluster_info)

        status_info = {
            'GlobalClusterIdentifier': global_cluster_info['GlobalClusterIdentifier'],
            'Status': global_cluster_info['Status'],
            'Members': cluster_members
        }

        return json.dumps(status_info, indent=4)
    except ClientError as e:
        print(f"Error fetching global cluster status: {e}")
        return None

def monitor_periodically(global_db_identifier, interval_seconds=60):
    while True:
        status_json = get_global_db_status(global_db_identifier)
        
        if status_json:
            print("Global Database Status:")
            print(status_json)
        
        # Wait for the next iteration
        time.sleep(interval_seconds)

if __name__ == "__main__":
    # Replace with your Global DB Identifier
    global_db_identifier = 'your-global-db-identifier'

    # Monitor periodically, interval in seconds
    monitor_periodically(global_db_identifier, interval_seconds=60)
```

### Key Features:
1. **Failover Script:**
   - The script initiates a failover to the specified global cluster in the target region.
   - You must specify the **GlobalClusterIdentifier** and the **TargetDbClusterIdentifier** (region cluster) for the failover.
   - It uses the `failover_global_cluster` API for Aurora PostgreSQL Global Database failover.

2. **Monitoring Script:**
   - The `describe_global_clusters` API call fetches detailed information about the global cluster.
   - It checks the status of the cluster and each of its members (across regions), including which cluster is the writer and their current health status.
   - The results are formatted as JSON, which can be used in dashboards for monitoring.
   - You can set the monitoring interval by adjusting `interval_seconds`.

### Integration with a Dashboard:
- The `monitor_periodically` function outputs the health status as JSON, which can be parsed and displayed in your dashboard.
- To ensure continuous monitoring, you can run this script as a background process using tools like cron, systemd, or AWS Lambda (with CloudWatch Events triggering it periodically).

### Example JSON Output:
The output from the monitoring script will look like this:

```json
{
    "GlobalClusterIdentifier": "your-global-db-identifier",
    "Status": "available",
    "Members": [
        {
            "DBClusterArn": "arn:aws:rds:us-east-1:123456789012:cluster:my-db-cluster",
            "Region": "us-east-1",
            "IsWriter": true,
            "Status": "available"
        },
        {
            "DBClusterArn": "arn:aws:rds:us-west-2:123456789012:cluster:my-db-cluster-secondary",
            "Region": "us-west-2",
            "IsWriter": false,
            "Status": "available"
        }
    ]
}
```

### Scheduling the Scripts:
- **Failover**: The failover script should be run manually or triggered automatically in response to a failure event.
- **Monitoring**: You can use a job scheduler like **cron** or set up a **CloudWatch** rule to trigger the monitoring script every minute or at your desired frequency for continuous status checks.

This setup ensures you can failover and monitor your Aurora PostgreSQL Global Database effectively.
