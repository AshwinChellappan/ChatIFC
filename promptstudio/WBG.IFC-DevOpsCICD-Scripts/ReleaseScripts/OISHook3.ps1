#param(
#[string] $UserName
#[string] $Password
#[string] $ProjectName
#[string] $ProjectURL
#[string] $HookUser
#[string] $HookPassword
#[string] $ProjectProperties
#[string] $NetworkExposure
#[string] $numberofusers
#[string] $numberofadmins
#[string] $ProjectDataSenstivity
#[string] $SystemEnvironment
#[string] $ProjectCaseNumber

#)
#(Invoke-webrequest -URI "http://10.169.16.162:5001/CR?u=$UserName&p=$Password&pn=$ProjectName&pu=$ProjectURL&hu=$HookUser&hp=$HookPassword&pp=$ProjectProperties&nex=$NetworkExposure&nu=$numberofusers&na=$numberofadmins&ps=$ProjectDataSenstivity&e=$SystemEnvironment&pc=$ProjectCaseNumber
#").Content | out-file -filepath "C:\iPortal-AST\iPortal-AST\Scripts\SecureAssist\$Projectname.html"
#$Check = Get-Content -path C:\iPortal-AST\iPortal-AST\Scripts\SecureAssist\$Projectname.html | Select-String "flag = go" -quiet
#Write-Output $Check
#If ($Check="flag = go") 
#{
Write-Output "flag=go"
#} 
#else
#{
#Write-Output flag=nogo
#throw "error"
#}
#================================================================================================================================================
#DS Powershall Script for On-prem
# ==========================================================================================================================================

<#For ($i=0; $i -lt 18; $i++){
    Try{
        if (-not ([System.Management.Automation.PSTypeName]'ServerCertificateValidationCallback').Type)
{
$certCallback = @"
    using System;
    using System.Net;
    using System.Net.Security;
    using System.Security.Cryptography.X509Certificates;
    public class ServerCertificateValidationCallback
    {
        public static void Ignore()
        {
            if(ServicePointManager.ServerCertificateValidationCallback ==null)
            {
               ServicePointManager.ServerCertificateValidationCallback += 
                    delegate
                    (
                        Object obj, 
                        X509Certificate certificate, 
                        X509Chain chain, 
                        SslPolicyErrors errors
                    )
                    {
                        return true;
                    };
            }
        }
    }
"@
    Add-Type $certCallback
}
[ServerCertificateValidationCallback]::Ignore()
	$response = $null

$response =(curl -H @{"Content-Type" = "application/x-www-form-urlencoded"} -Method POST 'https://oisdevsecopsdev.worldbank.org/dynhook' -ContentType application/x-www-form-urlencoded -Body "pc=ACN-2019-14562&u=webgoat&p=webgoat&hu=one&hp=One&t=http%3A%2F%2Foishooktest-env.pyigngh4mc.us-east-1.elasticbeanstalk.com%2F&lu=http%3A%2F%2Foishooktest-env.pyigngh4mc.us-east-1.elasticbeanstalk.com%2F&lou=lou&lfu=exampleInputEmail1&lfp=exampleInputPassword1&pc=ACN-2019-14562" -UseBasicParsing);
if($response.Content -contains "Calculated Result for this application : [flag = go ]"){Write-Host $response.content}
else
{Write-Host $response.content}
    }
    Catch [Exception] { 
        echo $_.Exception.Message 
        break #exit 1
    }
#}#>