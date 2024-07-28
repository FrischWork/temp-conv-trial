from confluent_kafka.admin import AdminClient, NewTopic

kafka_config = {
    'bootstrap.servers': 'kafka:9092'
}

topics = [
    {
        "name": 'test_topic',
        "num_partitions": 1,
        "replication_factor": 1
    },
    {
        "name": 'messages_requests',
        "num_partitions": 1,
        "replication_factor": 1
    },
    {
        "name": 'messages_responses',
        "num_partitions": 1,
        "replication_factor": 1
    }
]

admin_client = AdminClient(kafka_config)
topic_metadata = admin_client.list_topics(timeout=10)

for topic in topics:
    # Check if the topic already exists
    if topic["name"] not in topic_metadata.topics:
        # Create the topic
        new_topic = NewTopic(topic["name"], topic["num_partitions"], topic["replication_factor"])
        admin_client.create_topics([new_topic])

    print(f"Topic '{topic['name']}' created successfully or already exists.")
