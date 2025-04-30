#!powershell
Param
(
    [Parameter(Mandatory=$true)]
    [string]$apiId,

    [Parameter(Mandatory=$true)]
    [string]$apiKey
)



$file = $env:FILEPATH
$app = $env:APPNAME
$sandbox = $env:SANDBOXNAME
$teams = $env:TEAMS
$business_criticality = $env:CRITICALITY
$casenumber = $env:CASE_NUMBER
$policy_name = $env:POLICY_NAME
$buildnumber = $env:BUILDNUMBER
$buildname = $env:BUILDNAME
$hookname = "CR"
$hookuser = $env:HookUsername
$hookpass = $env:HookPassword


$scan = $buildnumber + " - " + $buildname

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12


# Veracode Configuration Settings
$prescanSleepTime = 60
$scanSleepTime = 120

$download_url = "https://search.maven.org/remotecontent?filepath=com/veracode/vosp/api/wrappers/vosp-api-wrappers-java/23.4.11.2/vosp-api-wrappers-java-23.4.11.2-dist.zip"
$output_file = 'Veracode_wrappers.zip'
Invoke-WebRequest -Uri $download_url -OutFile $output_file
Expand-Archive -Path $output_file -DestinationPath . -Force
$javaWrapper = "VeracodeJavaAPI.jar"
[string]$randomName = Get-Random
$outputFileName = $randomName + ".log"


$proxyInfo = ""

Function Get-ScanName($scan) {
    If ($scan -eq $null -or $scan -eq "") {
        $scan = Get-Date -UFormat "%Y-%m-%d-%T"
        Write-Host "[INFO] No scan name provided. Using $scan."
    }
    Else {
        Write-Host "[INFO] Scan name: $scan"
    }
    return $scan
}

Function Assert-ArtifactExists($file) {
    If ((Test-Path $file) -eq $false) {
        Write-Host "[ERROR] File does not exist."
        Exit 1
    }
    Else {

        Write-Host "[INFO] File to upload: $file."
    }
}

Function Assert-AppIdExists($app) {

    Try {

        Write-Host "[INFO] Fetching App Details If already existing ......................."
        Write-Host "[INFO] App Name: $app"
        [xml]$appIdXml = java -jar $javaWrapper -vid $apiId -vkey $apiKey $proxyInfo -action GetAppList | Select-String -Pattern $app

        $appId = $appIdXml.app.app_id
        Write-Host "[INFO] App ID: $appId"
        $global:global_app_id  = $appId
        Update-App $app
        return $appId
    }
    Catch {
        Write-Host "[INFO] App ID does not exist."
        return $Null
    }
}

Function New-AppId($app) {

    Try {
    Write-Host "[INFO] Creating App: $app"
    $result = java -jar $javaWrapper -vid $apiId -vkey $apiKey $proxyInfo -action createApp -appname "$app" -criticality $business_criticality -teams $teams -tags $casenumber -policy $policy_name
    Write-Host "[INFO] App Created ......................."
    $appId = Assert-AppIdExists $app
    return $appId
}
    Catch {
        Write-Host "[Error] Unable to create the new app, Please re-run the build again or contact oisdevsecopssupport1@worldbankgroup.org "
        return $Null
    }
}


Function Update-App($app) {

    Try {
    Write-Host "[INFO] Checking if Policy and Criticality is matched in App: $app"
	[xml]$appinfo = java -jar $javaWrapper -vid $apiId -vkey $apiKey $proxyInfo -action getappinfo -appid $appId
    Write-Host java -jar $javaWrapper -vid $apiId -vkey $apiKey $proxyInfo -action getappinfo -appid $appId

	Write-Output "[INFO] Policy in Application $appinfo.appinfo.application.policy"
	Write-Output "[INFO] Criticality in Application $appinfo.appinfo.application.business_criticality"
	If ($policy_name -eq $appinfo.appinfo.application.policy) {
		Write-Host "Policy matched"
    }
    else{
		Write-Host "Policy Didn't matched"
		$update = java -jar $javaWrapper -vid $apiId -vkey $apiKey $proxyInfo -action updateapp -appid $appId -policy $policy_name
		Write-Output $update
		Write-Host "[INFO] Policy Updated in App: $app"
	}
	If ($business_criticality -eq $appinfo.appinfo.application.business_criticality) {
		Write-Host "Criticality matched"
    }
    else{
		Write-Host "Criticality Didn't matched"
		$update = java -jar $javaWrapper -vid $apiId -vkey $apiKey $proxyInfo -action updateapp -appid $appId -criticality $business_criticality
		Write-Output $update
		Write-Host "[INFO] Criticality Updated in App: $app"
	}
    If ($teams -eq $appinfo.appinfo.application.teams) {
		Write-Host "Teams matched"
    }
    else{
		Write-Host "Teams Didn't matched"
		$update = java -jar $javaWrapper -vid $apiId -vkey $apiKey $proxyInfo -action updateapp -appid $appId -teams $teams
		Write-Output $update
		Write-Host "[INFO] Teams Updated in App: $app"
	}
}
    Catch {
        Write-Host "[Error] Unable to create the new app, Please re-run the build again or contact oisdevsecopssupport1@worldbankgroup.org "
        return $Null
    }
}

Function Start-VeracodeScanNoWait($app, $sandbox, $file, $scan) {


    Try{

    Write-Host "[INFO] Upload and start scan ........................"
    If (-not ([string]::IsNullOrEmpty($sandbox))) {
        $result = java -jar $javaWrapper -vid $apiId -vkey $apiKey $proxyInfo -action uploadandscan -appname $app -createprofile false -sandboxname $sandbox -createsandbox true -filepath "$file" -version "$scan -deleteincompletescan 2" > $outputFileName
    } else {
        $result = java -jar $javaWrapper -vid $apiId -vkey $apiKey $proxyInfo -action uploadandscan -appname $app -createprofile false -filepath "$file" -version "$scan" -selectedpreviously true -deleteincompletescan 2
        Write-Host "[INFO] Parsing the upload and scan values  ......................."
        $result > $outputFileName
    }

    # Write-Host $result
    $global:upload_scan_results = Get-Content -raw $outputFileName

    $uploadResult = Get-Content -raw $outputFileName
    If ($uploadResult -like "*Starting pre-scan*") {
        Write-Host ""
        Write-Host "[INFO] File uploaded and Pre-scan started  ......................."
        return $True
    }

    Else {
        Write-Host ""
        Write-Host "[ERROR] Error with upload or scan submission: $uploadResult"
        return $False
    }

}
Catch{

        Write-Host "[Error] Error with upload or scan submission"
        return $Null

}
}

# Provisional Validator
Function Get-Provisional($app,$casenumber,$hookuser,$hookpass,$hookname) {

$data = @{
   "appname" = "$app"
   "acn" = "$casenumber"
   "hu" = "$hookuser"
   "hp" = "$hookpass"
   "hook_name" = "$hookname"
}

$headers = @{
    "content-type" = "application/x-www-form-urlencoded"
}

$resp = Invoke-RestMethod -Uri "https://devsecops.worldbank.org/provisional_validator" -Method Post -Body $data -Headers $headers


Write-Host $resp.status
Write-Host $resp.expiry_date
Write-Host $resp.code

return $resp.expiry_date,$resp.status

}

Function getbuildinfofunc()
{

        Try{
    # write-host "[Info] Fetching the Build info details ......................."
    print($global:upload_scan_results)
    $results = $global:upload_scan_results
    $value = $results -match 'the new analysis is "(\d{8}?)"'
    # Write-Host $value
    Write-Host "Build ID - $Matches[1]"
    $global:global_build_id = $Matches[1]
    [xml]$result = java -jar $javaWrapper -vid $apiId -vkey $apiKey $proxyInfo -action getbuildinfo -appid $global:global_app_id -buildid $global:global_build_id
    $buildinfo_status =  $result.buildinfo.build.analysis_unit.status
    write-host "[INFO] Build Status : $buildinfo_status"
    return $buildinfo_status

}Catch{

        Write-Host "[Error] Error while getting the build info details"
        return $Null

}
}




Function getsummery(){
    Try{

    write-host "[Info] Downloading the summart results ......................."
    [string]$randomName = Get-Random
    $summary_report_file_name = $randomName + ".log"
    $summary_results = java -jar $javaWrapper -vid $apiId -vkey $apiKey $proxyInfo -action summaryreport -appid $global_app_id -buildid $global:global_build_id -outputfilepath $summary_report_file_name
    sleep(3)
    $global:Document = [xml] (Get-Content $summary_report_file_name)
    $summary_status = $global:Document.summaryreport.policy_compliance_status
    return $summary_status

}Catch{

        Write-Host "[Error] Error while getting the summary report details"
        return $Null

}
}


Function main()
{


    Try{
        $provisional = Get-Provisional $app $casenumber $hookuser $hookpass $hookname
        if ($provisional[0] -ne $null -and $provisional[1] -eq "go"){
            Write-Host "[Info] Provisional Validation passed. Scan summary will be validated every week for any new code vulnerabilities."
            $scan = Get-ScanName $scan
            Assert-ArtifactExists $file
            If ((Assert-AppIdExists $app) -eq $Null) {
                New-AppId $app
            }

            $didScanStart = Start-VeracodeScanNoWait $app $sandbox $file $scan
            If ($didScanStart -eq $False) {
                Write-Host "[Error] Error in pre scan"
            }
            else{
                Write-host  "[Info] Provisional Scan Initiated for Application: $app File: $file ......................."
            
            exit 0}
        }
        else{

            $scan = Get-ScanName $scan
            Assert-ArtifactExists $file
            If ((Assert-AppIdExists $app) -eq $Null) {
                New-AppId $app
            }

            $didScanStart = Start-VeracodeScanNoWait $app $sandbox $file $scan
            If ($didScanStart -eq $False) {
                Write-Host "[Error] Error in pre scan"
            }
            else{
                Write-host  "[Info] Pre Scan Initiated ......................."

                for($i = 0; $i -lt 420 ; $i++){

                    if ( (getbuildinfofunc) -eq "Results Ready"){
                        write-host "[Info] Results ready and Initiated the download process ......................."
                        break }

                    else{
                        # write-host $i
                        sleep(30) } }

                if ( (getbuildinfofunc) -eq "Results Ready"){
                    write-host "[Info] Results ready to download from the veracode portal ......................."
                }
                else{
                    Write-Host "[Error] Unable to fetch the results from the veracode portal, Please re-run the build again or contact oisdevsecopssupport1@worldbankgroup.org "
                    exit 1
                }

                $summary_status = getsummery

                if ( $summary_status -eq "Did Not Pass"){
                    Write-Host "[Info] Policy Compliance Status: $summary_status"
                    Write-Host "[Info] Build Failed"
                    Write-Host "[Info] Number of Issues reported:" +  $global:Document.summaryreport.total_flaws
                    $veracode_sast_report_url = "https://analysiscenter.veracode.com/auth/index.jsp#ViewReportsResultSummary:" + $global:Document.summaryreport.account_id +":" + $global:Document.summaryreport.app_id + ":" + $global:Document.summaryreport.build_id +":" + $global:Document.summaryreport.sandbox_id
                    write-host "Step #1: Please login to veracode SAST portal with the FURL http://wbgsast/"
                    write-host "Step #2: Please access the Veracode report summary URL  $veracode_sast_report_url"
                    exit 1 }

                elseif ( $summary_status -eq "Pass") {

                    Write-Host "[Info] Policy Compliance Status: $summary_status"
                    Write-Host "Build Success" }

                elseif ( $summary_status -eq "Not Assessed") {

                    Write-Host "[Info] Policy Compliance Status: Not Assesed, The application has not yet had a scan published."
                    Write-Host "Build Failed"
                    exit 1  }

                elseif ( $summary_status -eq "Conditional Pass") {

                    Write-Host "[Info] Policy Compliance Status: Conditional Pass, The application has one or more policy relevant flaws that have not yet exceeded the grace period to fix."
                    Write-Host "Build Success" }

                else{
                    Write-Host "[Error] Exception: Pipeline task error, Please re-run the build again or contact oisdevsecopssupport1@worldbankgroup.org 2"
                    exit 1 }

            }
        } }

        Catch{
        Write-Host "[Error] Exception in Pipeline task, Please re-run the build again or contact oisdevsecopssupport1@worldbankgroup.org 1"
        Write-Output "Caught an error: $_"
        exit 1
        }
}


main
