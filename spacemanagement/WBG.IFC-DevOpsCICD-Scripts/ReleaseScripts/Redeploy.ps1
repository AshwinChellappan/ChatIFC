param(
#Parameters for this script
[string] $Releasestatus,
[string] $IISsitepath,
[string] $RedeployArtifacts
)
if($Releasestatus -eq "failed")
{
 Copy-Item ($RedeployArtifacts+"\*") $IISsitepath -Recurse -Force   
}
Else
{
 Write-Output "Release is successful" 
}