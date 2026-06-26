Write-Host "Starting ZooKeeper..."
$KAFKA_HOME = "D:\kafka\kafka_2.13-3.7.0"
& "$KAFKA_HOME\bin\windows\zookeeper-server-start.bat" "$KAFKA_HOME\config\zookeeper.properties"
