@echo off

set ArtifactLocation=C:\DevOps_Artifacts\
cd %ArtifactLocation%
set jsonfile=%1

echo Uploading Artifact________________________________________into Mule
curl -s --basic -u %7:%8 -F file=@%2 -F name=%3 -F version=3.0 --header "Content-Type: multipart/form-data" %9/repository > %jsonfile%
for /f "tokens=*" %%i in ('Powershell -ExecutionPolicy Bypass -Command "& '%AGENT_RELEASEDIRECTORY%/%RELEASE_DEFINITIONNAME%/ReleaseScripts/GettingAppId.ps1' -jsonfile '%jsonfile%' -a 1"') do set ArtifactId=%%i
echo %ArtifactId%

echo Creating Deployment_______________________________________into MMC
curl -s --basic -u %7:%8 -d  "{\"name\" : \"%3\" , \"servers\": [ \"%4\" ], \"applications\": [ \"%ArtifactId%\" ]}" --header "Content-Type: application/json" %9/deployments > %jsonfile%

echo Undeploying Previous Artifact_____________________________in MMC
set /a var = %6 - 1
echo %var%
set Prevjsonfile=C:\DevOps_Artifacts\%RELEASE_DEFINITIONNAME%_%VAR%.json
for /f "tokens=*" %%i in ('Powershell -ExecutionPolicy Bypass -Command "& '%AGENT_RELEASEDIRECTORY%/%RELEASE_DEFINITIONNAME%/ReleaseScripts/GettingAppId.ps1' -jsonfile '%Prevjsonfile%' -a 2"') do set PrevDeploymentId=%%i
echo %PrevDeploymentId%
set urlstring=%9/deployments/%PrevDeploymentId%/undeploy
curl -s --basic -u %7:%8 -X POST %9/deployments/%PrevDeploymentId%/undeploy 

echo Performing Deploy action__________________________________into MMC
for /f "tokens=*" %%i in ('Powershell -ExecutionPolicy Bypass -Command "& '%AGENT_RELEASEDIRECTORY%/%RELEASE_DEFINITIONNAME%/ReleaseScripts/GettingAppId.ps1' -jsonfile '%jsonfile%' -a 2"') do set DeploymentId=%%i
echo %DeploymentId%
set urlstring=%9/deployments/%DeploymentId%/%5
echo %urlstring%
curl -s --basic -u %7:%8 -X POST %urlstring%

echo Getting Deployment details__________________________________into MMC
set urlstring=%9/deployments/%DeploymentId%/
curl -s --basic -u %7:%8 %urlstring% > %jsonfile%
for /f "tokens=*" %%i in ('Powershell -ExecutionPolicy Bypass -Command "& '%AGENT_RELEASEDIRECTORY%/%RELEASE_DEFINITIONNAME%/ReleaseScripts/GettingAppId.ps1' -jsonfile '%jsonfile%' -a 3"') do set DeploymentStatus=%%i

echo Post deployment Action Based on Deployment status
if %DeploymentStatus% equ FAILED (
 echo %DeploymentId%
 echo %DeploymentStatus%
 
::set urlstring=%9/deployments/%DeploymentId%/undeploy
::curl --basic -u %7:%8 -X POST %9/deployments/%DeploymentId%/undeploy 
echo Deployment failed
goto :Failure
) else (
  echo Deployment Successfull
)