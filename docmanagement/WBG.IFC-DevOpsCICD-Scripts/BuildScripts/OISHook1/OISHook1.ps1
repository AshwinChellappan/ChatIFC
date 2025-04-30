# ================================================================
# Code Review Scan PowerShell Script.
# ================================================================

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
        $response = (curl -Method POST 'https://devsecops.worldbank.org/crhook' -ContentType application/x-www-form-urlencoded -Body "pc=$ProjectCaseID&pn=$ProjectName&hu=$HookUsername&hp=$HookPassword" -UseBasicParsing -TimeoutSec 600);
        If ($response.Content.contains("flag = no")) { 
     Write-Host $response.Content
	      exit 1
	}
        ElseIf ($response.Content.contains("flag = go")) {
     Write-Host $response.Content 
	    exit 0
	} 
        Else { sleep 10}
    }
    Catch [Exception] { 
        echo $_.Exception.Message 
        exit 1
    }
	#Write-Error $response.Content
	exit 1
}
