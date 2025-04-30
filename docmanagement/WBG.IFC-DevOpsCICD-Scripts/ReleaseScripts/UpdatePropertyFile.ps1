[CmdletBinding()]
Param(
[string] $AgentDirectory,
[string] $UnzippedArtifacts,
[string] $PropertyFile
)
$ZIPFile=Get-ChildItem $AgentDirectory -recurse | Where-Object {$_.Name -like 'target'} | Get-ChildItem -recurse -Force
#Get-ChildItem -Path "C:\ReleaseAgent\WAgent1\r24\a" -Filter "*.zip" -Recurse -ErrorAction SilentlyContinue -Force 
$ZIPFilePath=$ZIPFile.FullName
$DestPath=$ZIPFile.Directory.FullName
$ZIPFileName=$ZIPFile.Name
#write-output $ZIPFile
write-output $ZIPFilePath
write-output $DestPath

Add-Type -assembly "system.io.compression.filesystem"

#[io.compression.zipfile]::ExtractToDirectory($ZIPFilePath, $DestPath)
Remove-Item –path $DestPath -include *.zip -Force -Recurse 
Copy-item $PropertyFile\*.properties $UnzippedArtifacts\Classes
#[io.compression.zipfile]::CreateFromDirectory($DestPath, ("$AgentDirectory\"+"$ZIPFileName"))