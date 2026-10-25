@echo off
rem ------------------------------------------------------------------
rem run_cspect_incredible_shrinking_fireman-add-OPUS.bat
rem Runs The Incredible Shrinking Fireman sprite build in CSpect.
rem
rem Keep this file in the same folder as
rem   incredible_shrinking_fireman-add-OPUS_sprites.nex   (5f7e59ed, the sprite build)
rem and double-click it. To run another .nex (e.g. the plain build
rem incredible_shrinking_fireman-add-OPUS.nex, or a recoloured
rem ..._sprites_painted.nex), drag it onto this file.
rem ------------------------------------------------------------------
setlocal

rem ==== Settings - edit these to match your PC ====================
rem CSpect 3.3.1.0 in C:\CSpect3_3_1_0; if it is not there, a CSpect3_3_1_0 folder next to this
rem file or one folder up is used.
set "CSPECT=C:\CSpect3_3_1_0\CSpect.exe"
if not exist "%CSPECT%" if exist "%~dp0CSpect3_3_1_0\CSpect.exe" set "CSPECT=%~dp0CSpect3_3_1_0\CSpect.exe"
if not exist "%CSPECT%" if exist "%~dp0..\CSpect3_3_1_0\CSpect.exe" set "CSPECT=%~dp0..\CSpect3_3_1_0\CSpect.exe"

rem CSpect options:
rem   -zxnext   emulate the Next hardware (NextRegs, MMU, sprites)
rem   -nextrom  use the real Next ROMs (enNextZX.rom and enNxtmmc.rom
rem             must be in the CSpect folder); needed for the 48K ROM
rem             and the alt ROM the hooks run from
rem   -w3       window scale x3
rem   -tv       turn off the TV scanline effect
set "CSPECT_OPTS=-zxnext -nextrom -w3 -tv"
rem =================================================================

set "NEXFILE=%~dp0incredible_shrinking_fireman-add-OPUS_sprites.nex"
if not "%~1"=="" set "NEXFILE=%~f1"

if not exist "%NEXFILE%" (
    echo .nex not found: %NEXFILE%
    echo Put this batch file next to incredible_shrinking_fireman-add-OPUS_sprites.nex.
    goto :fail
)
if not exist "%CSPECT%" (
    echo CSpect not found at: %CSPECT%
    echo Edit the CSPECT line at the top of this batch file.
    goto :fail
)

echo Starting CSpect with %NEXFILE%
rem CSpect looks for its ROM files in its own folder, so run it from there
for %%I in ("%CSPECT%") do set "CSPECTDIR=%%~dpI"
start "" /D "%CSPECTDIR%" "%CSPECT%" %CSPECT_OPTS% "%NEXFILE%"
goto :eof

:fail
pause
exit /b 1
