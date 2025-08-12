set OSGE04W_ROOT=C:\OSGeo4W
set PYTHON_ROOT="C:/Program Files/Python39"
set GDAL_DATA=%OSGE04W_ROOT%\SHARE\gdal
set PROJ_LIB=%OSGE04W_ROOT%\SHARE\proj
set PATH=%PATH%;%PYTHON_ROOT%;%OSGE04W_ROOT%\bin
reg ADD "HKLM\SYSTEN\CurrentControlSet\Control\Session Manager\Environment" /v Path /t REG_EXPAND_SZ /f /d "%PATH%"
reg ADD "HKLM\SYSTEN\CurrentControlSet\Control\Session Manager\Environment" /v GDAL_DATA /t REG_EXPAND_SZ /f /d "%GDAL_DATA%"
reg ADD "HKLM\SYSTEN\CurrentControlSet\Control\Session Manager\Environment" /v PROJ_LIB /t REG_EXPAND_SZ /f /d "%PROJ_LIB%"