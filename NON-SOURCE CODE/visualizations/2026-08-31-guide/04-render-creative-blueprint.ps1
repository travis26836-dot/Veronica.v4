$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$outDir = $PSScriptRoot
$bmp = [System.Drawing.Bitmap]::new(2600,1460)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$g.Clear([System.Drawing.Color]::White)
$svg = [System.Text.StringBuilder]::new()
[void]$svg.AppendLine('<svg xmlns="http://www.w3.org/2000/svg" width="2600" height="1460" viewBox="0 0 2600 1460"><title>Veronica creative pipeline blueprint</title><desc>Future concept, not implemented. Owner approval branches into separate image and video lanes, which merge into a versioned asset library and export.</desc><rect width="2600" height="1460" fill="white"/>')
function Ink($hex) { [System.Drawing.ColorTranslator]::FromHtml($hex) }
function Label([string]$value,[float]$x,[float]$y,[float]$w,[float]$h,[float]$size=32,[string]$color='#202b3c',[bool]$center=$false,[bool]$bold=$false) {
    $style = if ($bold) { [System.Drawing.FontStyle]::Bold } else { [System.Drawing.FontStyle]::Regular }
    $font = [System.Drawing.Font]::new('Segoe UI',$size,$style,[System.Drawing.GraphicsUnit]::Pixel)
    $brush = [System.Drawing.SolidBrush]::new((Ink $color))
    $fmt = [System.Drawing.StringFormat]::new()
    $fmt.LineAlignment = [System.Drawing.StringAlignment]::Center
    if ($center) { $fmt.Alignment = [System.Drawing.StringAlignment]::Center }
    $g.DrawString($value,$font,$brush,[System.Drawing.RectangleF]::new($x,$y,$w,$h),$fmt)
    $lines = $value -split "`n"
    $anchor = if($center){'middle'}else{'start'}
    $tx = if($center){$x+$w/2}else{$x}
    $ty = $y+$h/2-($lines.Count-1)*$size*0.65+$size*0.34
    $weight = if($bold){700}else{400}
    foreach($line in $lines){ $safe=[System.Security.SecurityElement]::Escape($line); [void]$svg.AppendLine("<text x='$tx' y='$ty' font-family='Segoe UI,Arial,sans-serif' font-size='$size' font-weight='$weight' fill='$color' text-anchor='$anchor'>$safe</text>"); $ty += $size*1.3 }
    $fmt.Dispose();$font.Dispose();$brush.Dispose()
}
function Box([float]$x,[float]$y,[float]$w,[float]$h,[string]$title,[string]$color,[string]$fill='#ffffff',[float]$size=32) {
    $p=[System.Drawing.Drawing2D.GraphicsPath]::new();$r=24
    $p.AddArc($x,$y,$r,$r,180,90);$p.AddArc($x+$w-$r,$y,$r,$r,270,90);$p.AddArc($x+$w-$r,$y+$h-$r,$r,$r,0,90);$p.AddArc($x,$y+$h-$r,$r,$r,90,90);$p.CloseFigure()
    $brush=[System.Drawing.SolidBrush]::new((Ink $fill));$pen=[System.Drawing.Pen]::new((Ink $color),4)
    $g.FillPath($brush,$p);$g.DrawPath($pen,$p)
    [void]$svg.AppendLine("<rect x='$x' y='$y' width='$w' height='$h' rx='12' fill='$fill' stroke='$color' stroke-width='4'/>")
    Label $title ($x+18) ($y+12) ($w-36) ($h-24) $size '#202b3c' $true $true
    $p.Dispose();$brush.Dispose();$pen.Dispose()
}
function Arrow([float[]]$xy,[string]$color='#45556a',[bool]$dashed=$false) {
    $pen=[System.Drawing.Pen]::new((Ink $color),4)
    if($dashed){$pen.DashPattern=@(4,4)}
    $points=[System.Drawing.PointF[]]@(for($i=0;$i -lt $xy.Count;$i+=2){[System.Drawing.PointF]::new($xy[$i],$xy[$i+1])})
    $g.DrawLines($pen,$points)
    $last=$points[-1];$prev=$points[-2];$angle=[Math]::Atan2($last.Y-$prev.Y,$last.X-$prev.X)
    $left=[System.Drawing.PointF]::new(($last.X-18*[Math]::Cos($angle)+8*[Math]::Sin($angle)),($last.Y-18*[Math]::Sin($angle)-8*[Math]::Cos($angle)))
    $right=[System.Drawing.PointF]::new(($last.X-18*[Math]::Cos($angle)-8*[Math]::Sin($angle)),($last.Y-18*[Math]::Sin($angle)+8*[Math]::Cos($angle)))
    $brush=[System.Drawing.SolidBrush]::new((Ink $color));$g.FillPolygon($brush,[System.Drawing.PointF[]]@($last,$left,$right))
    $coords=($points|ForEach-Object{"$($_.X),$($_.Y)"}) -join ' ';$dash=if($dashed){"stroke-dasharray='16 16'"}else{''}
    [void]$svg.AppendLine("<polyline points='$coords' fill='none' stroke='$color' stroke-width='4' $dash/><polygon points='$($last.X),$($last.Y) $($left.X),$($left.Y) $($right.X),$($right.Y)' fill='$color'/>")
    $pen.Dispose();$brush.Dispose()
}
$blue='#237b9b';$purple='#7860a7';$orange='#b97524';$slate='#45556a'
Label 'VERONICA / CREATIVE PIPELINE BLUEPRINT' 95 65 2420 100 58 '#202b3c' $false $true
Label 'FUTURE CONCEPT — NOT IMPLEMENTED' 100 160 2400 60 34 $orange $false $true
Label '01  SHARED DIRECTION' 100 235 430 50 26 $slate $false $true
Label '02  IMAGE LANE' 600 285 950 55 32 $blue $false $true
Label '03  VIDEO LANE' 600 725 1100 55 32 $purple $false $true
Box 100 310 360 140 "Owner brief +`nreference rights" $slate '#f5f7fa' 32
Box 100 530 360 140 'Creative planner' $slate '#f5f7fa' 32
Box 100 760 360 150 "Owner approval`n+ budget" $orange '#fff8ec' 32
Arrow @(280,450,280,530)
Arrow @(280,670,280,760)
Arrow @(460,835,515,835,515,450,600,450) $blue
Arrow @(460,835,515,835,515,900,600,900) $purple
Box 600 360 400 180 "Image prompt`n+ references" $blue '#f3fafc' 34
Box 1100 360 400 180 "Image provider`nadapter" $blue '#f3fafc' 34
Box 1600 360 400 180 'Review + refine' $blue '#f3fafc' 34
Box 2100 360 400 180 'Approved stills' $blue '#f3fafc' 34
Arrow @(1000,450,1100,450) $blue
Arrow @(1500,450,1600,450) $blue
Arrow @(2000,450,2100,450) $blue
Box 600 800 300 200 "Script +`nstoryboard" $purple '#f8f5fc' 32
Box 1000 800 300 200 "Keyframes /`nclip plan" $purple '#f8f5fc' 32
Box 1400 800 300 200 "Video provider`nadapter" $purple '#f8f5fc' 30
Box 1800 800 300 200 'Edit + audio' $purple '#f8f5fc' 32
Box 2200 800 300 200 "Reviewed`nvideo" $purple '#f8f5fc' 32
Arrow @(900,900,1000,900) $purple
Arrow @(1300,900,1400,900) $purple
Arrow @(1700,900,1800,900) $purple
Arrow @(2100,900,2200,900) $purple
Arrow @(2300,540,2300,640,1150,640,1150,800) $blue $true
Label 'OPTIONAL  ·  approved stills → video keyframes' 1180 655 1200 55 26 $blue
Arrow @(2500,450,2560,450,2560,1110,1300,1110,1300,1190) $blue
Arrow @(2350,1000,2350,1110,1300,1110,1300,1190) $purple
Box 1000 1190 600 140 "Versioned asset library" $slate '#f5f7fa' 36
Box 1880 1190 620 140 'Guide / editor / export' $slate '#f5f7fa' 36
Arrow @(1600,1260,1880,1260)
Label 'Separate generation workers. Owner-gated spending. Reviewed assets. Core-first qualification remains the priority.' 100 1380 2400 45 28 '#45556a'
[void]$svg.AppendLine('</svg>')
$bmp.Save((Join-Path $outDir '04-creative-pipeline-blueprint.png'),[System.Drawing.Imaging.ImageFormat]::Png)
[System.IO.File]::WriteAllText((Join-Path $outDir '04-creative-pipeline-blueprint.svg'),$svg.ToString(),[System.Text.UTF8Encoding]::new($false))
$g.Dispose();$bmp.Dispose()
Get-Item -LiteralPath (Join-Path $outDir '04-creative-pipeline-blueprint.png'),(Join-Path $outDir '04-creative-pipeline-blueprint.svg') | Select-Object Name,Length
