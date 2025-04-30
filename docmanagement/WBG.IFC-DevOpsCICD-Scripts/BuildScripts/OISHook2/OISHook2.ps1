Param
(
 [parameter(Mandatory=$true,
 ValueFromPipeline=$true)]
$ProjectCaseID,
 [parameter(Mandatory=$true,
 ValueFromPipeline=$true)]
$ProjectName,
 [parameter(Mandatory=$true,
 ValueFromPipeline=$true)]
$HookUsername,
 [parameter(Mandatory=$true,
 ValueFromPipeline=$true)]
$HookPassword
)
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
For ($i=0; $i -lt 18; $i++){
Try{
$response = $null
$response = (curl -Method POST 'https://devsecops.worldbank.org/blackduck/scan' -ContentType application/x-www-form-urlencoded -Body "scan_file_name=$ProjectName&version=8.3&policy= &acn_number=$ProjectCaseID&hook_username=$HookUsername&hook_password=$HookPassword" -UseBasicParsing -TimeoutSec 600);
If ($response.Content.contains("Flag = Go")) { 
        Write-Host $response.Content
         exit 0
        }
ElseIf ($response.Content.contains("Flag = No-Go")) { 
        Write-Host $response.Content
echo $(Flag)
         exit 1
        }       
Else { sleep 10}
}
Catch [Exception] { 
echo $_.Exception.Message 
exit 1
}
  Write-Error $response.Content   
    exit 1
}