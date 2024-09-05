import boto3
import time

# Initialize the Kinesis client
kinesis_client = boto3.client('kinesis', region_name='your-region')  # Replace 'your-region' with the appropriate AWS region

stream_name = 'test-stream'

def create_kinesis_stream():
    """Creates a Kinesis data stream."""
    try:
        response = kinesis_client.create_stream(
            StreamName=stream_name,
            ShardCount=1  # Number of shards; you can change based on your requirements
        )
        print(f"Stream {stream_name} is being created.")
    except kinesis_client.exceptions.ResourceInUseException:
        print(f"Stream {stream_name} already exists.")
    except Exception as e:
        print(f"Error creating stream: {e}")

def wait_for_stream_to_become_active():
    """Waits for the stream to become active."""
    print(f"Waiting for stream {stream_name} to become active...")
    while True:
        response = kinesis_client.describe_stream(StreamName=stream_name)
        stream_status = response['StreamDescription']['StreamStatus']
        if stream_status == 'ACTIVE':
            print(f"Stream {stream_name} is now active.")
            break
        time.sleep(5)

def put_records_into_stream():
    """Puts some test records into the stream."""
    for i in range(5):
        data = f"Record {i}"
        response = kinesis_client.put_record(
            StreamName=stream_name,
            Data=data.encode('utf-8'),  # Data must be bytes
            PartitionKey='partition-key'
        )
        print(f"Put record {i} into stream: {response}")

def get_records_from_stream():
    """Gets records from the stream."""
    shard_iterator = kinesis_client.get_shard_iterator(
        StreamName=stream_name,
        ShardId='shardId-000000000000',  # The Shard ID can be fetched programmatically
        ShardIteratorType='TRIM_HORIZON'
    )['ShardIterator']

    print("Getting records from stream...")
    response = kinesis_client.get_records(
        ShardIterator=shard_iterator,
        Limit=5
    )
    for record in response['Records']:
        print(f"Retrieved record: {record['Data'].decode('utf-8')}")

def main():
    create_kinesis_stream()
    wait_for_stream_to_become_active()
    put_records_into_stream()
    get_records_from_stream()

if __name__ == "__main__":
    main()
