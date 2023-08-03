if ($Args[1] -in (90, 270)){
	$FilePath = $Args[0]
	$Rotation = "Rotate{0}FlipNone" -f $Args[1]

	[Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms"); 
	$Image = New-Object System.Drawing.Bitmap $FilePath
	$Image.RotateFlip($Rotation)
	$Image.Save($FilePath, "jpeg")
}
Exit