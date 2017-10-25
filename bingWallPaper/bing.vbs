Dim delayer
Set delayer = CreateObject("WScript.Shell")
WScript.sleep 80000
delayer.Run """D:\python\bingWallPaper\bing.bat""", 0
Set delayer = Nothing
WScript.quit