#!/bin/bash
# Run this from D:\kafka\kafka_2.13-3.7.0\ in Git Bash
# This script starts ZooKeeper and Kafka, then creates required topics

KAFKA_HOME="D:/kafka/kafka_2.13-3.7.0"

echo ">>> Starting ZooKeeper..."
start "" "$KAFKA_HOME/bin/windows/zookeeper-server-start.bat" "$KAFKA_HOME/config/zookeeper.properties"

echo ">>> Waiting 10 seconds for ZooKeeper to initialize..."
sleep 10

echo ">>> Starting Kafka Broker..."
start "" "$KAFKA_HOME/bin/windows/kafka-server-start.bat" "$KAFKA_HOME/config/server.properties"

echo ">>> Waiting 10 seconds for Kafka to initialize..."
sleep 10

echo ">>> Creating topics..."
"$KAFKA_HOME/bin/windows/kafka-topics.bat" --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 1 \
  --partitions 3 \
  --topic raw-events

"$KAFKA_HOME/bin/windows/kafka-topics.bat" --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 1 \
  --partitions 3 \
  --topic computed-features

echo ">>> Listing all topics:"
"$KAFKA_HOME/bin/windows/kafka-topics.bat" --list --bootstrap-server localhost:9092

echo ">>> Kafka setup complete."