# ================================================================
# Dynamic Scanning PowerShell Script.
# ================================================================

# Param([string]$ACN, [string]$TARGETURL, [string]$APPLICATIONNAME,[string]$HookUsername, [string]$HookPassword, [string]$UserEmail, [string]$UserPass, [string]$AuthType)

$TARGETURL = $env:TARGETURL
$APPLICATIONNAME = $env:APPLICATIONNAME
$ACN = $env:ACN
$HookUsername = $env:HookUsername
$HookPassword = $env:HookPassword
$UserEmail = $env:UserEmail
$UserPass = $env:UserPass
$AuthType = $env:AuthType
$DAC = $env:DAC
$InternetStatus = $env:InternetStatus


Write-Host $ACN $TARGETURL $APPLICATIONNAME $HookUsername $HookPassword $UserEmail $AuthType $DAC $InternetStatus


Write-Host "Started"

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

For ($i=0; $i -lt 18; $i++){
    Try{
        Write-Host "Started 1 "
        If ($ACN[-1] -eq "0"){
            Write-Host "Matching 0 - Endpoint https://devsecops.worldbank.org/rapid1"
            $response = $null
                        $response = (curl -Method POST 'https://devsecops.worldbank.org/rapid1' -ContentType application/x-www-form-urlencoded -Body "url=$TARGETURL&application_name=$APPLICATIONNAME&acn=$ACN&hu=$HookUsername&hp=$HookPassword&user_email=$UserEmail&user_pass=$UserPass&auth_type=$AuthType&dac=$DAC&int_access=$InternetStatus" -UseBasicParsing -TimeoutSec 21600);

                        If ($response.Content.contains("flag = Go")) {
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
        ElseIf($ACN[-1] -eq "1"){
            Write-Host "Matching 1  - Endpoint https://devsecops.worldbank.org/rapid2"
            $response = $null
                        $response = (curl -Method POST 'https://devsecops.worldbank.org/rapid2' -ContentType application/x-www-form-urlencoded -Body "url=$TARGETURL&application_name=$APPLICATIONNAME&acn=$ACN&hu=$HookUsername&hp=$HookPassword&user_email=$UserEmail&user_pass=$UserPass&auth_type=$AuthType&dac=$DAC&int_access=$InternetStatus" -UseBasicParsing -TimeoutSec 21600);

                        If ($response.Content.contains("flag = Go")) {
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
        ElseIf($ACN[-1] -eq "2"){
            Write-Host "Matching 2 - Endpoint https://devsecops.worldbank.org/rapid3"
            $response = $null
                        $response = (curl -Method POST 'https://devsecops.worldbank.org/rapid3' -ContentType application/x-www-form-urlencoded -Body "url=$TARGETURL&application_name=$APPLICATIONNAME&acn=$ACN&hu=$HookUsername&hp=$HookPassword&user_email=$UserEmail&user_pass=$UserPass&auth_type=$AuthType&dac=$DAC&int_access=$InternetStatus" -UseBasicParsing -TimeoutSec 21600);

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
        ElseIf($ACN[-1] -eq "3"){
            Write-Host "Matching 3 - - Endpoint https://devsecops.worldbank.org/rapid4"
            $response = $null
                        $response = (curl -Method POST 'https://devsecops.worldbank.org/rapid4' -ContentType application/x-www-form-urlencoded -Body "url=$TARGETURL&application_name=$APPLICATIONNAME&acn=$ACN&hu=$HookUsername&hp=$HookPassword&user_email=$UserEmail&user_pass=$UserPass&auth_type=$AuthType&dac=$DAC&int_access=$InternetStatus" -UseBasicParsing -TimeoutSec 21600);

                        If ($response.Content.contains("flag = Go")) {
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
        ElseIf($ACN[-1] -eq "4"){
            Write-Host "Matching 4 - Endpoint https://devsecops.worldbank.org/rapid1"
            $response = $null
                        $response = (curl -Method POST 'https://devsecops.worldbank.org/rapid1' -ContentType application/x-www-form-urlencoded -Body "url=$TARGETURL&application_name=$APPLICATIONNAME&acn=$ACN&hu=$HookUsername&hp=$HookPassword&user_email=$UserEmail&user_pass=$UserPass&auth_type=$AuthType&dac=$DAC&int_access=$InternetStatus" -UseBasicParsing -TimeoutSec 21600);

                        If ($response.Content.contains("flag = Go")) {
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
        ElseIf($ACN[-1] -eq "5"){
            Write-Host "Matching 5 - Endpoint https://devsecops.worldbank.org/rapid2"
            $response = $null
                        $response = (curl -Method POST 'https://devsecops.worldbank.org/rapid2' -ContentType application/x-www-form-urlencoded -Body "url=$TARGETURL&application_name=$APPLICATIONNAME&acn=$ACN&hu=$HookUsername&hp=$HookPassword&user_email=$UserEmail&user_pass=$UserPass&auth_type=$AuthType&dac=$DAC&int_access=$InternetStatus" -UseBasicParsing -TimeoutSec 21600);

                        If ($response.Content.contains("flag = Go")) {
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
        ElseIf($ACN[-1] -eq "6"){
            Write-Host "Matching 6 - Endpoint https://devsecops.worldbank.org/rapid3"
            $response = $null
                        $response = (curl -Method POST 'https://devsecops.worldbank.org/rapid3' -ContentType application/x-www-form-urlencoded -Body "url=$TARGETURL&application_name=$APPLICATIONNAME&acn=$ACN&hu=$HookUsername&hp=$HookPassword&user_email=$UserEmail&user_pass=$UserPass&auth_type=$AuthType&dac=$DAC&int_access=$InternetStatus" -UseBasicParsing -TimeoutSec 21600);

                        If ($response.Content.contains("flag = Go")) {
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
        ElseIf($ACN[-1] -eq "7"){
            Write-Host "Matching 7 - Endpoint https://devsecops.worldbank.org/rapid4"
            $response = $null
                        $response = (curl -Method POST 'https://devsecops.worldbank.org/rapid4' -ContentType application/x-www-form-urlencoded -Body "url=$TARGETURL&application_name=$APPLICATIONNAME&acn=$ACN&hu=$HookUsername&hp=$HookPassword&user_email=$UserEmail&user_pass=$UserPass&auth_type=$AuthType&dac=$DAC&int_access=$InternetStatus" -UseBasicParsing -TimeoutSec 21600);

                        If ($response.Content.contains("flag = Go")) {
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
        ElseIf($ACN[-1] -eq "8"){
            Write-Host "Matching 8 - Endpoint https://devsecops.worldbank.org/rapid1"
            $response = $null
                        $response = (curl -Method POST 'https://devsecops.worldbank.org/rapid1' -ContentType application/x-www-form-urlencoded -Body "url=$TARGETURL&application_name=$APPLICATIONNAME&acn=$ACN&hu=$HookUsername&hp=$HookPassword&user_email=$UserEmail&user_pass=$UserPass&auth_type=$AuthType&dac=$DAC&int_access=$InternetStatus" -UseBasicParsing -TimeoutSec 21600);

                        If ($response.Content.contains("flag = Go")) {
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
        ElseIf($ACN[-1] -eq "9"){
            Write-Host "Matching 9 - Endpoint https://devsecops.worldbank.org/rapid2"
            $response = $null
                        $response = (curl -Method POST 'https://devsecops.worldbank.org/rapid2' -ContentType application/x-www-form-urlencoded -Body "url=$TARGETURL&application_name=$APPLICATIONNAME&acn=$ACN&hu=$HookUsername&hp=$HookPassword&user_email=$UserEmail&user_pass=$UserPass&auth_type=$AuthType&dac=$DAC&int_access=$InternetStatus" -UseBasicParsing -TimeoutSec 21600);

                        If ($response.Content.contains("flag = Go")) {
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
        Else{
            Write-Host "Unable to process the request"
            Write-Host $ACN "ACN"
            Write-Host $APPLICATIONNAME "applcation name"
            Write-Host $AuthType "Auth"
            Write-Host $HookPassword "hpass"
            Write-Host $HookUsername "huser"
            Write-Host $TARGETURL "tgt"
            }
    }
    Catch [Exception] {
        echo $_.Exception.Message
        exit 1
    }
	Write-Error $response.Content
	exit 1
}