param ($jsonfile ,$a)
write-output $jsonfile
#$jsonfile = "C:\Script\mule-integration.json"
$parsed = get-Content $jsonfile | ConvertFrom-Json 
switch ($a) 
    { 
        1 {$id = $parsed.versionId
write-output $id
return $id} 
        2 {
$id = $parsed.data.id
write-output $id
return $id} 
        3 {
$id = $parsed.data.started
write-output $id
return $id} 
        4 {
$id = $parsed.data.serverArtifacts.message
write-output $id
return $id} 
}