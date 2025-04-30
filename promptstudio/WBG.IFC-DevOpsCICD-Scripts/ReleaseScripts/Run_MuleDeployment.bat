@echo off

for /f "delims=" %%i in ('powershell -ExecutionPolicy Bypass -Command  "& %AGENT_RELEASEDIRECTORY%/_%RELEASE_DEFINITIONNAME%/ReleaseScripts/GetToken.ps1"') do set "Tok=%%i"
echo %Tok%
set urlstring=https://anypoint.mulesoft.com/hybrid/api/v1/applications
set jsonfile=%1
set jsonfile1=%2

::echo Undeploying-Deleting Previous Artifact_____________________________in ARM
::set Prevjsonfile=C:\DevOps_Artifacts\%RELEASE_DEFINITIONNAME%-%RELEASE_ENVIRONMENTNAME%.json
::for /f "tokens=*" %%i in ('Powershell -ExecutionPolicy Bypass -Command "& '%AGENT_RELEASEDIRECTORY%/_%RELEASE_DEFINITIONNAME%/ReleaseScripts/GettingAppId.ps1' -jsonfile '%Prevjsonfile%' -a 2"') do set PrevDeploymentId=%%i
::curl -X DELETE "https://anypoint.mulesoft.com/hybrid/api/v1/applications/%SPrevDeploymentId%" -H "authorization:%Tok%" -H "x-anypnt-env-id:%3" -H "x-anypnt-org-id:%4" 
::SLEEP 300
echo %SPrevDeploymentId%
if %SPrevDeploymentId% equ null (
 echo Deploying New Artifact_______________________________________________in ARM
 curl -X POST "https://anypoint.mulesoft.com/hybrid/api/v1/applications" -H "authorization:%Tok%" -H "content-type:multipart/form-data;boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW" -H "x-anypnt-env-id:%3" -H "x-anypnt-org-id:%4" -F file="@%8" -F artifactName="%5" -F targetId=%6 > %jsonfile%

) else (
 echo Updating The Artifact_______________________________________________in ARM
 curl -X PATCH "https://anypoint.mulesoft.com/hybrid/api/v1/applications/%SPrevDeploymentId%" -H "authorization:%Tok%" -H "content-type:multipart/form-data;boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW" -H "x-anypnt-env-id:%3" -H "x-anypnt-org-id:%4" -F file="@%8" -F targetId=%6 > %jsonfile%
)

::echo Deploying-new Artifact______________________________________________in ARM
::curl -X POST "https://anypoint.mulesoft.com/hybrid/api/v1/applications" -H "authorization:%Tok%" -H "content-type:multipart/form-data;boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW" -H "x-anypnt-env-id:%3" -H "x-anypnt-org-id:%4" -F file="@%8" -F artifactName="%5" -F targetId=%6 > %jsonfile%
::curl -X PATCH "https://anypoint.mulesoft.com/hybrid/api/v1/applications/%SPrevDeploymentId%" -H "authorization:%Tok%" -H "content-type:multipart/form-data;boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW" -H "x-anypnt-env-id:%3" -H "x-anypnt-org-id:%4" -F file="@%8" -F targetId=%6 > %jsonfile%
SLEEP 480
echo Status of current deployed Artifact_________________________________in ARM
set Curjsonfile=C:\DevOps_Artifacts\%RELEASE_DEFINITIONNAME%-%RELEASE_ENVIRONMENTNAME%.json
echo %Curjsonfile%
for /f "tokens=*" %%i in ('Powershell -ExecutionPolicy Bypass -Command "& '%AGENT_RELEASEDIRECTORY%/_%RELEASE_DEFINITIONNAME%/ReleaseScripts/GettingAppId.ps1' -jsonfile '%Curjsonfile%' -a 2"') do set DeploymentId=%%i
echo %DeploymentId%
curl -X GET "https://anypoint.mulesoft.com/hybrid/api/v1/applications/%DeploymentId%" -H "authorization:%Tok%" -H "content-type:application/json" -H "Accept:application/json" -H "x-anypnt-env-id:%3" -H "x-anypnt-org-id:%4" > %jsonfile1%

for /f "tokens=*" %%i in ('Powershell -ExecutionPolicy Bypass -Command "& '%AGENT_RELEASEDIRECTORY%/_%RELEASE_DEFINITIONNAME%/ReleaseScripts/GettingAppId.ps1' -jsonfile '%jsonfile1%' -a 3"') do set DeploymentStatus=%%i
for /f "tokens=*" %%i in ('Powershell -ExecutionPolicy Bypass -Command "& '%AGENT_RELEASEDIRECTORY%/_%RELEASE_DEFINITIONNAME%/ReleaseScripts/GettingAppId.ps1' -jsonfile '%jsonfile1%' -a 4"') do set DeploymentStatus1=%%i

echo Status of the deployment_____________________________________________in ARM
if %DeploymentStatus% equ False (
 echo %DeploymentStatus%
 echo Deployment failed with below error message or Check Application status in ARM Console 
 echo %DeploymentStatus1%

goto :Failure
) else (
  echo Deployment Successful
)