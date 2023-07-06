Option Explicit

Dim lngWidth, lngHeight, lngBottomCrop
Dim objShell, objArgs, objXmlHttp, objStream, objImageFile, objImageProcess, objFSO, objFile
Dim strImageURL, strImageFile

	'On Error Resume Next
    Set objShell = CreateObject("WScript.Shell")
    Set objFSO = CreateObject("Scripting.FileSystemObject")
    
    Set objArgs = WScript.Arguments
    strImageURL = objArgs.Item(0)
    strImageFile = objArgs.Item(1)
    lngWidth = CLng(objArgs.Item(2))
    lngHeight = CLng(objArgs.Item(3))

    Set objXmlHttp = CreateObject("Microsoft.XMLHTTP")
	With objXmlHttp
    	.Open "GET", strImageURL, False
    	.Send
    End With 
    
    Set objStream = CreateObject("Adodb.Stream")
    With objStream
        .Type = 1 '//binary
        .Open
        .Write objXmlHttp.responseBody 
        .SaveToFile strImageFile, 2 '//overwrite
    End With

    Set objImageFile = CreateObject("WIA.ImageFile")
    objImageFile.LoadFile strImageFile 							' load image
    If objImageFile.Height < lngHeight Then lngHeight = 0		' to cover for images which do not have image height attributes set
    lngBottomCrop = objImageFile.Height - lngHeight
    
    Set objImageProcess = CreateObject("WIA.ImageProcess") 
    objImageProcess.Filters.Add objImageProcess.FilterInfos("Crop").filterid 'setup filter
    With objImageProcess.Filters(1)
        .Properties("Left") = 0
        .Properties("Top") = 0
        .Properties("Right") = 0 
        .Properties("Bottom") = lngBottomCrop
    End With
    
    Set objImageFile = objImageProcess.Apply(objImageFile) 'apply change
    objFSO.DeleteFile strImageFile ' delete original downloaded image
    objImageFile.SaveFile strImageFile 'save cropped image version

    ' delete temp files created by cropping
    On Error Resume Next 
    objFSO.DeleteFile objShell.ExpandEnvironmentStrings("%TEMP%") & "\Img*.tmp", True 

    Set objArgs = Nothing
    Set objShell = Nothing
    Set objFSO = Nothing
    Set objXmlHttp = Nothing
    Set objStream = Nothing
    
	WScript.Quit
	
'---------------------------------------------------------------------------------------------------------------------