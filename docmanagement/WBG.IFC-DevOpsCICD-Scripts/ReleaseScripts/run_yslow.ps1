param(
[string] $ySlowOutput,
[string] $ySlowSite
)
phantomjs 'C:\phantomjs\yslow-phantomjs\yslow.js' --info basic --format plain $ySlowSite > $ySlowOutput

$Check = Get-Content -path $ySlowOutput | Select-String '(overall score: B)|(overall score: A)' -quiet
$Check1 = Get-Content -path $ySlowOutput
If ($Check) 
{
Write-Output $Check1
} 
else
{
Write-Output $Check1
throw "error"
}