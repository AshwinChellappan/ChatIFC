try
{
$jsonobject = ConvertFrom-Json $env:Release_Tasks
}
catch
{
Write-Verbose -Verbose “Error parsing Release_Tasks environment variable”
Write-Verbose -Verbose $Error
}
$overallStatus ="Success"
foreach ($task in $jsonobject | Get-Member -MemberType NoteProperty) {    
    $taskproperty = $jsonobject.$($task.Name) | ConvertFrom-Json
    write-output $taskproperty.name
    write-output $taskproperty.status
    if ($taskproperty.status -eq "failed")
    {
       $statuscode = "$($taskproperty.Status)"
        Write-Host ("##vso[task.setvariable variable=Releasestatus;]$statuscode")
        break
    }
    else
    {
     $statuscode = "$($taskproperty.Status)"
        Write-Host ("##vso[task.setvariable variable=Releasestatus;]$statuscode")   
    }
    }
write-output $statuscode