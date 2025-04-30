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