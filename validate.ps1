$ErrorActionPreference = "Stop"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "   Running Autogen SDLC Test Suite" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

$env:PYTHONPATH = "."
pytest tests/

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "SUCCESS: All tests passed!" -ForegroundColor Green
    Write-Host "The system is fully validated." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "FAILURE: Some tests failed. Please review the output above." -ForegroundColor Red
}
