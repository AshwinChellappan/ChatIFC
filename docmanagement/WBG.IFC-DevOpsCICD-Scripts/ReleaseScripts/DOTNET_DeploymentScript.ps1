param(
#Parameters for this script
[string] $ArtifactZipPath,
[string] $UnzippedArtifacts,
[string] $IISsitepath
)

Write-Output " _________________________________________________________________ Begin PS script"
#---------------------------- BEGIN Expand-ZIPFile function
function Expand-ZIPFile($file, $destination)
{
    $zip = $shell.NameSpace($file)#get the handle of ZIP file and traverse each item in it. (item can be a folder or file)
    foreach($item in $zip.items())
    {
        if($item.IsFolder)
        {
            $recursive_destination = $destination+"\"+$item.name

            if($item.name -eq "PackageTmp")#PackageTmp is the folder where the binaries are packed. Right Catch!
            {
                $UA_Temp_Var = $shell.Namespace($UnzippedArtifacts)
                $UA_Temp_Var.copyhere($item)
            }
            else
            {
                Expand-ZIPFile -file $item -destination $recursive_destination
            }
        }
    }
}#---------------------------- END Expand-ZIPFile function

# Initialize 
if( -not (Test-Path $UnzippedArtifacts)  ){New-Item -ItemType directory -Path $UnzippedArtifacts}
$shell = new-object -com shell.application -Verbose

Write-Output " _________________________________________________________________ Begin calling Expand"
Expand-ZIPFile –File  $ArtifactZipPath –Destination $UnzippedArtifacts

Write-Output " _________________________________________________________________ Begin removing old"

#$ErrorActionPreference = Continue
Remove-Item ($IISsitepath+"\*") -Recurse -Force -Verbose

Write-Output " _________________________________________________________________ Beign filtering"

$res_obj = Get-ChildItem $UnzippedArtifacts -recurse | Where-Object {$_.Name -like 'PackageTmp'}

Write-Output " _________________________________________________________________ Begin copy to IIS"

Copy-Item ($res_obj.FullName+"\*") $IISsitepath -Recurse

Remove-Item $UnzippedArtifacts -Recurse -Verbose -Force