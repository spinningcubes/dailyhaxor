import dailyhaxor

haxor = dailyhaxor.DailyHaxor("dailyhaxor.html", 365)
haxor.scanRepository("ZeroFps", "../zerofps","Vim")
haxor.scanRepository("git", "DailyHaxor", ".","Spinningcubes")
haxor.WriteHtml()




