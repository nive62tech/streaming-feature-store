Write-Host "Starting Kafka Broker..."
$KAFKA_HOME = "D:\kafka\kafka_2.13-3.7.0"
& "$KAFKA_HOME\bin\windows\kafka-server-start.bat" "$KAFKA_HOME\config\server.properties"
