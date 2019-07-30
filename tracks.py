import pygame
import time


pygame.mixer.init()
x="Assets/Instruments/"
#seperates instruments into channels for individual control
pygame.mixer.set_num_channels(5)
#array to store all channels in one place
channels=["",pygame.mixer.Channel(1),
pygame.mixer.Channel(2),
pygame.mixer.Channel(3),
pygame.mixer.Channel(4)]
#loading all instrument sound files
A=pygame.mixer.Sound(x+"Brass.wav")
B=pygame.mixer.Sound(x+"Per.wav")
C=pygame.mixer.Sound(x+"Strings.wav")
D=pygame.mixer.Sound(x+"Woods.wav")

#playing all sounds in unison
def play(tempo=100):
    if 85<tempo<112:
        y=""
    elif tempo > 112:
        y="2"
    else:
        y="1"

    A=pygame.mixer.Sound(x+"Brass"+y+".wav")
    B=pygame.mixer.Sound(x+"Per"+y+".wav")
    C=pygame.mixer.Sound(x+"Strings"+y+".wav")
    D=pygame.mixer.Sound(x+"Woods"+y+".wav")
    channels[1].play(A)
    channels[2].play(B)
    channels[3].play(C)
    channels[4].play(D)


def setvol(group,vol):
    channels[group].set_volume(vol)
time.sleep(5)