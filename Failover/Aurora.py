import boto3
import time

def get_cluster_status(cluster_arn, region):
    client = boto3.client('rds', region_name=region)
    response = client.describe_db_clusters(DBClusterIdentifier=cluster_arn)
    return response['DBClusters'][0]['Status']

def monitor_primary_cluster(cluster_arn, region):
    while True:
        status = get_cluster_status(cluster_arn, region)
        if status != 'available':
            print(f"Cluster {cluster_arn} in {region} is down. Initiating failover...")
            initiate_failover(cluster_arn, region)
        else:
            print(f"Cluster {cluster_arn} in {region} is healthy.")
        time.sleep(60)  # Check every 60 seconds

def initiate_failover(primary_cluster_arn, primary_region):
    # Assuming failover to us-west-2
    promote_read_replica('your-read-replica-arn', 'us-west-2')

def promote_read_replica(replica_arn, region):
    client = boto3.client('rds', region_name=region)
    response = client.failover_db_cluster(DBClusterIdentifier=replica_arn)
    print(f"Failover initiated for {replica_arn} in {region}. Response: {response}")

if __name__ == "__main__":
    primary_cluster_arn = 'your-primary-cluster-arn'
    primary_region = 'us-east-1'
    monitor_primary_cluster(primary_cluster_arn, primary_region)
