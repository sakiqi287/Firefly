Add-Type -AssemblyName System.Drawing

$files = @(
    'src/content/posts/images/1_1.jpg',
    'src/content/posts/images/1_2.jpg',
    'src/content/posts/images/1_3.jpg',
    'src/content/posts/images/1_4.jpg',
    'src/content/posts/images/1_5.jpg'
)

foreach ($file in $files) {
    if (Test-Path $file) {
        $fullPath = (Resolve-Path $file).Path
        $img = [System.Drawing.Image]::FromFile($fullPath)
        $width = $img.Width
        $height = $img.Height
        
        Write-Host "Processing: $file ($width x $height)"
        
        if ($width -gt 1920 -or $height -gt 1920) {
            $ratio = [Math]::Min(1920/$width, 1920/$height)
            $newWidth = [int]($width * $ratio)
            $newHeight = [int]($height * $ratio)
            
            $newImg = New-Object System.Drawing.Bitmap($newWidth, $newHeight)
            $g = [System.Drawing.Graphics]::FromImage($newImg)
            $g.DrawImage($img, 0, 0, $newWidth, $newHeight)
            
            $img.Dispose()
            $g.Dispose()
            
            $newImg.Save($fullPath, [System.Drawing.Imaging.ImageFormat]::Jpeg)
            $newImg.Dispose()
            
            Write-Host "Compressed to ${newWidth}x${newHeight}"
        } else {
            Write-Host "Already small enough"
            $img.Dispose()
        }
    }
}

Write-Host "Done!"