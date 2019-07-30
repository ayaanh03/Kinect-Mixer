Beethoven but not Quite:

Description:
We have a classical music attribute controller under the "classic" section and a midi sample creator under the sample section that accepts patterns from the user and saves it as a midi file which can be played back later on. The classical music section allows you to control the volume and tempo of various instrument clusters in beethoven's fifth symphony.

Put all the python files in a folder along with the Assets and Samples folder in the same folder and run the Main.py file in any compiler.
Assets can be found at: https://drive.google.com/drive/folders/1-Zyxt3ZQlvv0scJ5qGxWr8UXZf4ZxMCs?usp=sharing

Libraries:
You'll need 
PyKinect2
ctypes
pygame
midiutil
Microsoft Kinect SDK

All python modules can be installed using pip in this project
Ex. "pip install pygame" or "pip install <module name as listed above>"

Skipping to different parts:
One can skip to midi or classic mode by changing self.gm variable to "mix" or "classic" respectively.
