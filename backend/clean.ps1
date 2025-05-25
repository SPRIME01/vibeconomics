# Clear Python cache files
Write-Host "Clearing Python cache files..."
Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Include *.pyc -Recurse -Force | Remove-Item -Force
Write-Host "Done!"
