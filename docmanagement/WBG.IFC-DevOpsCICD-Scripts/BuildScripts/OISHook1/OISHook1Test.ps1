# ================================================================
# Code Review Scan PowerShell Script. New
# ================================================================
<#Param
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
        $response = (curl -Method POST 'https://devsecops.worldbank.org/crhook' -ContentType application/x-www-form-urlencoded -B "pc=$ProjectCaseID&pn=$ProjectName&hu=$HookUsername&hp=$HookPassword&pu=pu&ps=ps&u=u&p=p&pp=pp&nex=nex&nu=3&na=2&e=e" -UseBasicParsing -TimeoutSec 600);
       #$response = (curl -H @{"Content-Type" = "application/x-www-form-urlencoded"} -Method POST 'https://oisdevsecopsdev.worldbank.org/crhook' -ContentType application/x-www-form-urlencoded -Body "pc=$ProjectCaseID&pn=$ProjectName&hu=hook username&hp=hook password&pu=pu&ps=ps&u=u&p=p&pp=pp&nex=nex&nu=3&na=2&e=e" -UseBasicParsing);
        If ($response.Content.contains("flag = go")) { 
    		Write-Host $response.Content
	    	exit 0
		}
        ElseIf ($response.Content.contains("flag = no")) { 
    		Write-Host $response.Content
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
   }#>

Param
(
  [parameter(Mandatory=$true,
    ValueFromPipeline=$true)]
    $ProjectCaseID,
    [parameter(Mandatory=$true,
    ValueFromPipeline=$true)]
    $Projectname,
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
        $response = (curl -Method POST 'https://devsecops.worldbank.org/crhook' -ContentType application/x-www-form-urlencoded -B "pc=$ProjectCaseID&pn=$Projectname&hu=$HookUsername&hp=$HookPassword&pu=pu&ps=ps&u=u&p=p&pp=pp&nex=nex&nu=3&na=2&e=e" -UseBasicParsing -TimeoutSec 600);
       #$response = (curl -H @{"Content-Type" = "application/x-www-form-urlencoded"} -Method POST 'https://oisdevsecopsdev.worldbank.org/crhook' -ContentType application/x-www-form-urlencoded -Body "pc=$ProjectCaseID&pn=$ProjectName&hu=hook username&hp=hook password&pu=pu&ps=ps&u=u&p=p&pp=pp&nex=nex&nu=3&na=2&e=e" -UseBasicParsing);
        If ($response.Content.contains("flag = go")) { 
    		Write-Host $response.Content
	    	exit 0
		}
        ElseIf ($response.Content.contains("flag = no")) { 
    		Write-Host $response.Content
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








