param(
#Parameters for this script
[string] $IISsitepath,
[string] $BackupArtifacts
)
Write-Output " _________________________________________________________________ Begin taking the backup"

if( -not (Test-Path $BackupArtifacts)  ){New-Item -ItemType directory -Path $BackupArtifacts}
Copy-Item $IISsitepath $BackupArtifacts -Recurse -Force