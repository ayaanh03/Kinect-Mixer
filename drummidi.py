from midiutil import MIDIFile
import pygame
import time
pygame.mixer.init()
times=[]
endf=""
midi=MIDIFile(2)
def play(i):
    if pygame.mixer.get_busy():
        return
    if i==4 or i==0:
        pygame.mixer.music.load("Drum.mid") #35
        pygame.mixer.music.play(1)
    elif i==2:
        pygame.mixer.music.load("Clap.mid") #39
        pygame.mixer.music.play(1)
    elif i==3 or i==1:
        pygame.mixer.music.load("Cymbal.mid") #42
        pygame.mixer.music.play(1)
def record(i,t):
    global midi
    if i==4 or i==0:
        i=35
    elif i==2:
        i=39     
    elif i==3 or i==1:
        i=42
    if i==4 or i==2 or i==3:
        c=0
    else:
         c=1
    if (int(t)+.5,i) in times:
        v=0
    else:
        v=100

    midi.addNote(c,9,i,t,1/2,v)
    times.append((int(t)+.5,i))

    print(t)
    global endf
    endf=midi
