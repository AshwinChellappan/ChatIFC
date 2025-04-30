
 [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
 $api = "https://anypoint.mulesoft.com/accounts/login"
   
    $creds = @{
        username = "IFCdevopsdeploy"
        password = "IFCD@v@2(8gTFSd#"
   
    } 

$result = Invoke-RestMethod $api -Method Post -body $creds
$token =  $result.access_token
$tok = "bearer" + " " + $token
write-host $tok