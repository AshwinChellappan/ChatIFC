param ($BackupArtifacts,$WSPFilename,$SharePointSiteURL)
Add-PSSnapin "Microsoft.SharePoint.PowerShell"
Get-PSSnapin "Microsoft.SharePoint.PowerShell"
Write-Output "Taking________________________________ Backup"
$SharePointSiteURL = Get-SPSite $SharePointSiteURL
$listTemplate = [Microsoft.SharePoint.SPListTemplateType]::SolutionCatalog
$solGallery = $SharePointSiteURL.GetCatalog($listTemplate)
$solGallery.Items | % {

if($_.File.Name -eq $WSPFilename)
{
    [System.IO.FileStream]$outStream = New-Object System.IO.FileStream(($BackupArtifacts+"\"+$_.File.Name), [System.IO.FileMode]::Create);
    $fileData = $_.File.OpenBinary();
    $outStream.Write($fileData, 0, $fileData.Length);
    $outStream.Close();
    }
}