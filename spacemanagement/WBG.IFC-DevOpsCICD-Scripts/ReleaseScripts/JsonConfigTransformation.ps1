param(
[string] $EnvironmentName,
[string] $ReactJSConfigFilename
)

$default_file = Get-Item $ReactJSConfigFilename
$default_file_name = [io.path]::GetFileNameWithoutExtension($default_file.FullName)
$extension = $default_file.Extension

$Parent_path = $default_file.DirectoryName

Remove-Item $default_file -Force

$targetfile_name = $Parent_path +"\"+ $default_file_name + "_" + $EnvironmentName + $extension
#Write-Host "targetfile_name-" $targetfile_name

$targetfile = Get-Item $targetfile_name
Rename-Item $targetfile ($default_file_name + $extension)
Remove-Item ($Parent_path +"\"+ $default_file_name + "_*.js")