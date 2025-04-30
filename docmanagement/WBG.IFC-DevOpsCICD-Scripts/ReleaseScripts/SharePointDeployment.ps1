param ($ArtifactPath,$WSPFilename,$SharePointSiteURL)
Add-PSSnapin "Microsoft.SharePoint.PowerShell"
Get-PSSnapin "Microsoft.SharePoint.PowerShell"
Write-Output "Starting deployment____________________________________action"
$usersolutionscollection = Get-SPUserSolution -Site "$SharePointSiteURL"
Foreach ($i in $usersolutionscollection)
{
	if($i.Name -eq $WSPFilename)
{
Write-Output 'solution available'
 Write-Output "Uninstalling previous WSP"
    Uninstall-SPUserSolution -Identity "$WSPFilename" -confirm:$false –Site "$SharePointSiteURL"
        Remove-SPUserSolution -Identity "$WSPFilename" -confirm:$false –Site "$SharePointSiteURL"
}
else
{

Write-Output 'solution unavailable'
}
}
Write-Output "Installing solution"
add-SPUserSolution -LiteralPath "$ArtifactPath" -Site "$SharePointSiteURL"
install-SPUserSolution –Identity "$WSPFilename" –Site "$SharePointSiteURL"