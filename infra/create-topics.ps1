$KAFKA_HOME = "D:\kafka\kafka_2.13-3.7.0"

Write-Host "Creating Kafka topics..."

& "$KAFKA_HOME\bin\windows\kafka-topics.bat" --create `
  --bootstrap-server localhost:9092 `
  --replication-factor 1 `
  --partitions 3 `
  --topic raw-events

& "$KAFKA_HOME\bin\windows\kafka-topics.bat" --create `
  --bootstrap-server localhost:9092 `
  --replication-factor 1 `
  --partitions 3 `
  --topic computed-features

Write-Host "Listing all topics:"
& "$KAFKA_HOME\bin\windows\kafka-topics.bat" --list --bootstrap-server localhost:9092
