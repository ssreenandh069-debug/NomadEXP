# NomadEXP
NomadEXP is a file explorer which is faster and better than default windows file explorer


# Currently in development
# Update
added a gui to have a better search feature

# How to run?
Save the main.c file in a folder and open terminal to that folder. Make sure you have GCC to create a DLL file.
```bash
gcc -shared -o -s nomadexp.dll main.c
```
After creating the DLL file
open the python main.py file either run the python script or do the following 
# for fast launch
```bash
python -m PyInstaller --noconsole --onedir --add-data "nomadexp.dll;." main.py
```
#for single file but a slower launcher 
```bash
python -m PyInstaller --noconsole --onefile --add-data "nomadexp.dll;." main.py
```
run the exe and hit |alt+space| to start it 
when windows warn about admin, simply click more info and run anyway
to close, open the system tray and exit the application from there
