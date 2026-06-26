Write-Host "================================================"
Write-Host "  Verifying Infrastructure"
Write-Host "================================================"

# Check Redis
Write-Host "`n[1] Redis..."
try {
  $ping = redis-cli ping
  if ($ping -eq "PONG") {
    Write-Host "  Redis: RUNNING" -ForegroundColor Green
  }
} catch {
  Write-Host "  Redis: NOT RUNNING" -ForegroundColor Red
}

# Check Java
Write-Host "`n[2] Java..."
try {
  $java = java -version 2>&1
  Write-Host "  Java: OK - $($java[0])" -ForegroundColor Green
} catch {
  Write-Host "  Java: NOT FOUND" -ForegroundColor Red
}

# Check Python packages
Write-Host "`n[3] Python packages..."
python -c "import kafka; import redis; import fastapi; import mlflow; import sklearn; print('  Packages: OK')"

Write-Host "`n================================================"
