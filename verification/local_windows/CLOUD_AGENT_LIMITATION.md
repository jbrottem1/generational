# Cloud agent limitation

This certification package was prepared in a Cursor cloud Linux environment.

That environment **cannot**:
- install Blender on the user's Windows PC
- run `winget`
- query the local NVIDIA GPU / drivers
- produce an honest PASS for local workstation certification

Only a run of `INSTALL_AND_CERTIFY.bat` on the Windows workstation can generate a valid
`WORKSTATION_CERTIFICATION_REPORT.md` for Generational 3D production.
