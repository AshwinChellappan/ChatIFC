param(
[string] $EnvironmentName,
[string] $ConfigFilenames,
[string] $ConfigPath
)


$FilesArray = $ConfigFilenames.Split(",")
$Parent_path = $ConfigPath
foreach ($ConfigFilename in $FilesArray)
{
    $ConfigFilename = $ConfigFilename.trim()
    $ConfigFilename = $Parent_path + "\" + $ConfigFilename
    $default_file = Get-Item $ConfigFilename
    $default_file_name = [io.path]::GetFileNameWithoutExtension($default_file.FullName)
    $extension = $default_file.Extension

    Remove-Item $default_file -Force
 
    $targetfile_name = $Parent_path +"\"+ $default_file_name + "_" + $EnvironmentName + $extension
    Write-Host "Renaming targetfile_name -" $targetfile_name
 
    $targetfile = Get-Item $targetfile_name
    Rename-Item $targetfile_name ($default_file_name + $extension)
    Remove-Item ($Parent_path +"\"+ $default_file_name + "_*.Config")
}