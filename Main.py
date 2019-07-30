# FRAMEWORK FROM PyKinectV2 Module Starter

from pykinect2 import PyKinectV2
from pykinect2.PyKinectV2 import *
from pykinect2 import PyKinectRuntime
import ctypes
import _ctypes
import pygame
import sys
import os
import math
import time
import copy

# self class imports
import tracks
import midicreate
import drummidi


if sys.hexversion >= 0x03000000:
    import _thread as thread
else:
    import thread

# colors for drawing different bodies

colors = [pygame.color.THECOLORS["red"],
          pygame.color.THECOLORS["yellow"],
          pygame.color.THECOLORS["green"],
          pygame.color.THECOLORS["white"],
          pygame.color.THECOLORS["blue"]]

instruments = ["Piano", "Drums", "Bass", "Guitar"]


class BodyGameRuntime(object):
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        # Set the width and height of the screen [width, height]
        self._infoObject = pygame.display.Info()
        self._screen = pygame.display.set_mode((self._infoObject.current_w >> 1, self._infoObject.current_h >> 1),
                                               pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE, 32)

        pygame.display.set_caption("Music Maker")

        # Loop until the user clicks the close button.
        self._done = False

        # Used to manage how fast the screen updates
        self._clock = pygame.time.Clock()

        # Kinect runtime object, we want only color and body frames
        self._kinect = PyKinectRuntime.PyKinectRuntime(
            PyKinectV2.FrameSourceTypes_Color | PyKinectV2.FrameSourceTypes_Body)
        # back buffer surface for getting Kinect color frames, 32bit color, width and height equal to the Kinect color frame size
        self._frame_surface = pygame.Surface(
            (self._kinect.color_frame_desc.Width, self._kinect.color_frame_desc.Height), 0, 32)

        # initializing variables
        self._bodies = None
        self.cR = 0, 0
        self.cL = 0, 0
        self.prevtime, self.prevbutton = 0, 0
        self.gm = "main"
        self.instrument = ""
        self.prev = 0
        self.tt = 0
        self.playing = 0
        self.tempo = 0
        self.tempa = []
        self.bootup = 0
        self.selected = 0
        self.recording = 0
        self.start_pos = 0
        self.b = [0]*(77-51)
        self.notes = [0]*(77-51)
        self.drumtime = 0
        self.rN = copy.deepcopy(self.notes)
        self.noteinit()
        self.prevB = 0

        # loading button images and btranforming into size
        self.stepin = pygame.image.load(
            os.path.join("Assets", "Menus", "Frame.png"))
        self.stepin = pygame.transform.scale(self.stepin, (1920, 1080))
        self.mainmenu = pygame.image.load(
            os.path.join("Assets", "Menus", "main.png"))
        self.raisehandimg = pygame.image.load(
            os.path.join("Assets", "Menus", "Raise.png"))
        self.backbutton = pygame.image.load(
            os.path.join("Assets", "Menus", "Back.png"))
        self.recbutton = pygame.image.load(
            os.path.join("Assets", "Menus", "Record.png"))
        self.testB = pygame.image.load(
            os.path.join("Assets", "Menus", "TestB.png"))
        self.testR = pygame.image.load(
            os.path.join("Assets", "Menus", "RecT.png"))
        self.mainmenu = pygame.transform.scale(self.mainmenu, (1920, 1080))
        self.raisehandimg = pygame.transform.scale(
            self.raisehandimg, (1920, 1080))
        self.playb = pygame.image.load(
            os.path.join("Assets", "Menus", "Playbutton.png"))
        self.playb = pygame.transform.scale(self.playb, (200, 75))

    # initializes note storing array
    def noteinit(self):
        for i in range(77-51):
            for j in range(6):
                self.notes[i] = [0]*6
        self.rN = copy.deepcopy(self.notes)
    # checks if button is being pressed

    def checkhover(self, currbutton, t=3):
        if currbutton != self.prevbutton:
            self.prevtime = time.time()
            self.prevbutton = currbutton
            return
        else:
            elapsedT = time.time()-self.prevtime
            pygame.draw.arc(self._frame_surface, colors[2], pygame.Rect(
                1720, 0, 250, 250), 0, (elapsedT/t)*2*math.pi, 10)
            if elapsedT >= t:
                elapsedT = 0
                self.prevtime = time.time()
                return True
    # scales cursor to screen

    def cursor(self, xi, yi):
        x = (int(xi)-960)*2
        y = (int(yi)-540)*2
        x = int(x+xi)
        y = int(y+yi)
        if x > 1920:
            x = 1920
        elif x < 0:
            x = 0
        if y > 1080:
            y = 1080
        elif y < 0:
            y = 0
        return (x, y)

    def draw_body_bone(self, joints, jointPoints, color, joint0):
        joint0State = joints[joint0].TrackingState

        # both joints are not tracked
        if (joint0State == PyKinectV2.TrackingState_NotTracked):
            return

        # both joints are not *really* tracked
        if (joint0State == PyKinectV2.TrackingState_Inferred):
            return

        # ok, at least one is good
        start = (jointPoints[joint0].x, jointPoints[joint0].y)

        c = self.cursor((start[0]), (start[1]))
        if joint0 == PyKinectV2.JointType_HandRight:
            self.cR = c
            self.ocR = ((start[0])//1, (start[1])//1)

        else:
            self.cL = c
            self.ocL = ((start[0])//1, (start[1])//1)

        try:
            pygame.draw.circle(self._frame_surface, color, (c[0], c[1]), 80, 8)

        # need to catch it due to possible invalid positions (with inf)
        except:
            pass

    def draw_body(self, joints, jointPoints, color):

        # Right Arm
        self.draw_body_bone(joints, jointPoints,
                            colors[0], PyKinectV2.JointType_HandRight)

        # Left Arm
        self.draw_body_bone(joints, jointPoints,
                            colors[1], PyKinectV2.JointType_HandLeft)

    def draw_color_frame(self, frame, target_surface):
        target_surface.lock()
        address = self._kinect.surface_as_array(target_surface.get_buffer())
        ctypes.memmove(address, frame.ctypes.data, frame.size)
        del address
        target_surface.unlock()

    def getvol(self, joints, jointPoints):
        if self.cR == (0, 0) or self.cL == (0, 0):
            return

        try:
            # ok, at least one is good
            hand = self.cL[1]
            # checking and determining %age for volume control
            upperlimit = self._screen.get_height()-100
            lowerlimit = 100
            factor = (upperlimit-lowerlimit)
            percent = (hand-100)/factor
            percent *= 100
            percent = 100-percent
            if percent > 100:
                percent = 100
            elif percent < 0:
                percent = 0
            percent /= 100
            pygame.draw.line(
                self._frame_surface, colors[0], (100, 980), (100, 880*(1-percent)+100), 30)
            # print(percent)
            return percent if self.cR[1] > 1920/3 else None

        except:
            # need to catch it due to possible invalid positions (with inf)
            pass

    def gettempo(self, joints, jointPoints):
        joint0State = joints[PyKinectV2.JointType_HandRight].TrackingState

        # both joints are not tracked
        if (joint0State == PyKinectV2.TrackingState_NotTracked):
            return

        # both joints are not *really* tracked
        if (joint0State == PyKinectV2.TrackingState_Inferred):
            return

        # ok, at least one is good
        ypoint = (jointPoints[PyKinectV2.JointType_HandRight].y)
        # storing time when hand reaches region for calculations
        if ypoint < 400:
            self.tempo = time.time()
        if ypoint > 600 and self.tempo != 0:
            self.tempo2 = time.time()
        try:
            a = (self.tempo2-self.tempo)
            if not a <= 0:
                a /= 6
                a = 1/a
                # print(a)
            if not (self.tempo != 0 and self.tempo2 == 0):
                self.tempo, self.tempo2 = 0, 0
            return a

        # need to catch it due to possible invalid positions (with inf)
        except:
            pass

    def showmenu(self):
        self._frame_surface.blit(self.mainmenu, (0, 0))
        self._frame_surface.blit(self.raisehandimg, (0, 0))
        pygame.display.flip()

    def checkselection(self, joints, jointPoints):
        if self.cR == (0, 0) or self.cL == (0, 0):
            return
        # ok, at least one is good
        rect4 = pygame.Rect(0, 540, 960, 810)
        rect3 = pygame.Rect(960, 540, 1920, 810)
        rect2 = pygame.Rect(960, 810, 1920, 1080)
        rect1 = pygame.Rect(0, 810, 960, 1080)
        # cchecking which box the hand is in
        try:
            if rect4.collidepoint(self.cL):
                if self.checkhover("4"):
                    self.selected = 4
            elif rect3.collidepoint(self.cL):
                if self.checkhover("3"):
                    self.selected = 3
            elif rect2.collidepoint(self.cL):
                if self.checkhover("1"):
                    self.selected = 1
            elif rect1.collidepoint(self.cL):
                if self.checkhover("2"):
                    self.selected = 2

        # need to catch it due to possible invalid positions (with inf)
        except:
            pass

    def run(self):

        # -------- Main Program Loop -----------
        while not self._done:
            # --- copy back buffer surface pixels to the screen, resize it if needed and keep aspect ratio
            # --- (screen size may be different from Kinect's color frame size)
            h_to_w = float(self._frame_surface.get_height()) / \
                self._frame_surface.get_width()
            target_height = int(h_to_w * self._screen.get_width())
            surface_to_draw = pygame.transform.scale(
                self._frame_surface, (self._screen.get_width(), target_height))
            self._screen.blit(surface_to_draw, (0, 0))
            surface_to_draw = None

            # --- Main event loop

            for event in pygame.event.get():  # User did something
                if event.type == pygame.QUIT:  # If user clicked close
                    self._done = True  # Flag that we are done so we exit this loop

                elif event.type == pygame.VIDEORESIZE:  # window resized
                    self._screen = pygame.display.set_mode(event.dict['size'],
                                                           pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE, 32)

            # --- Game logic should go here

            # --- Getting frames and drawing
            # --- Woohoo! We've got a color frame! Let's fill out back buffer surface with frame's data
            if self._kinect.has_new_color_frame():
                frame = self._kinect.get_last_color_frame()
                self.draw_color_frame(frame, self._frame_surface)
                frame = None

            # --- Cool! We have a body frame, so can get skeletons
            if self._kinect.has_new_body_frame():
                self._bodies = self._kinect.get_last_body_frame()

            # --- draw skeletons to _frame_surface
            # pygame.draw.arc(self._frame_surface,colors[0],pygame.Rect(1670,0,250,250),0,2*math.pi,10)
            if self._bodies is None:
                self._frame_surface.blit(self.stepin, (0, 0))

            if self._bodies is not None:

                for i in range(0, self._kinect.max_body_count):
                    body = self._bodies.bodies[i]
                    if not body.is_tracked:
                        continue
                    # convert joint coordinates to color space
                    joints = body.joints
                    joint_points = self._kinect.body_joints_to_color_space(
                        joints)
                    self.draw_body(joints, joint_points, colors[0])
                    if self.gm == "main":
                        mixbutton = pygame.Rect(0, 540, 960, 1080)
                        classicbutton = pygame.Rect(960, 540, 1920, 1080)
                        text = pygame.font.SysFont("Ariel", 120)
                        b1 = text.render("MIX", True, colors[3])
                        b2 = text.render("CLASSIC", True, colors[3])
                        pygame.draw.rect(self._frame_surface,
                                         colors[3], mixbutton, 5)
                        pygame.draw.rect(self._frame_surface,
                                         colors[3], classicbutton, 5)
                        self._frame_surface.blit(
                            b1, (480-b1.get_width()//2, 810-b1.get_height()//2))
                        self._frame_surface.blit(
                            b2, (1440-b2.get_width()//2, 810-b2.get_height()//2))
                        if mixbutton.collidepoint(self.cR) or mixbutton.collidepoint(self.cL):
                            if self.checkhover("mixbutton"):
                                self.gm = "mix"
                        if classicbutton.collidepoint(self.cR) or classicbutton.collidepoint(self.cL):
                            if self.checkhover("classicbutton"):
                                self.gm = "classic"
                    elif self.gm == "classic":
                        if self.bootup == 0:
                            temp = self.gettempo(joints, joint_points)
                            if temp != None and temp > 0:
                                self.tempa.append(temp)
                            if len(self.tempa) == 3:
                                self.tempa = sum(self.tempa)/len(self.tempa)
                            if isinstance(self.tempa, float):
                                tracks.play(self.tempa*2)
                                self.bootup = 1
                        elif self.selected == 0:
                            self.showmenu()
                            self.checkselection(joints, joint_points)
                        else:
                            a = self.getvol(joints, joint_points)
                            if a != None:
                                tracks.setvol(self.selected, a)
                                self.selected = 0
                    elif self.gm == "record":
                        isrecording = 0
                        if self.instrument == "Drums":
                            d = [pygame.Rect(200, 540, 1520/5, 270),
                                 pygame.Rect(200+1520*1/5, 540, 1520/5, 270),
                                 pygame.Rect(200+1520*2/5, 540, 1520/5, 270),
                                 pygame.Rect(200+1520*3/5, 540, 1520/5, 270),
                                 pygame.Rect(200+1520*4/5, 540, 1520/5, 270)]
                            self._frame_surface.blit(
                                self.backbutton, (1720, 980))
                            self._frame_surface.blit(
                                self.recbutton, (1720, 880))
                            self._frame_surface.blit(self.playb, (1720, 780))
                            if self.playb.get_rect(topleft=(1720, 780)).collidepoint(self.cR) or self.playb.get_rect(topleft=(1720, 780)).collidepoint(self.cL):
                                if self.checkhover("playDrum"):
                                    try:
                                        pygame.mixer.music.load(
                                            "Samples/DrumsT.mid")
                                        pygame.mixer.music.play(1)
                                    except:
                                        pygame.mixer.music.load(
                                            "Samples/Error.wav")
                                        pygame.mixer.play(1)
                            if self.backbutton.get_rect(topleft=(1720, 980)).collidepoint(self.cR) or self.backbutton.get_rect(topleft=(1720, 980)).collidepoint(self.cL):
                                print("back")
                                if self.checkhover("back"):
                                    midi = drummidi.endf
                                    with open("Samples/DrumsT.mid", "wb") as of:
                                        midi.writeFile(of)
                                    self.drumtime = 0
                                    self.instrument = ""
                                    self.gm = "mix"
                            if self.recbutton.get_rect(topleft=(1720, 880)).collidepoint(self.cR) or self.recbutton.get_rect(topleft=(1720, 880)).collidepoint(self.cL):
                                if self.checkhover("recordD"):
                                    self.drumtime = time.time()
                            font = pygame.font.SysFont("Ariel", 42, 1)
                            for i in range(5):
                                if i == 4 or i == 0:
                                    a = font.render(
                                        "Drum", True, colors[3])  # 35
                                elif i == 2:
                                    a = font.render(
                                        "Clap", True, colors[3])  # 39
                                elif i == 3 or i == 1:
                                    a = font.render(
                                        "Cymbal", True, colors[3])  # 42
                                x = 200+1520*i/5
                                x += a.get_width()//2
                                self._frame_surface.blit(a, (x, 675))
                                pygame.draw.rect(
                                    self._frame_surface, colors[3], d[i], 5)
                                if d[i].collidepoint(self.cR) or d[i].collidepoint(self.cL):
                                    if self.drumtime == 0 and self.prevB != i:
                                        if pygame.mixer.get_busy() == 0:
                                            drummidi.play(i)
                                            self.prevB = i
                                    else:
                                        drummidi.record(
                                            i, time.time()-self.drumtime)
                        if self.instrument in ["Piano", "Bass", "Guitar"]:
                            self._frame_surface.blit(
                                self.backbutton, (1720, 980))
                            if self.backbutton.get_rect(topleft=(1720, 980)).collidepoint(self.cR) or self.backbutton.get_rect(topleft=(1720, 980)).collidepoint(self.cL):
                                if self.checkhover("back"):
                                    isrecording = "done"
                                    self.instrument = ""
                            self._frame_surface.blit(self.playb, (1720, 780))
                            if self.playb.get_rect(topleft=(1720, 780)).collidepoint(self.cR) or self.playb.get_rect(topleft=(1720, 780)).collidepoint(self.cL):
                                if self.checkhover("playI"):
                                    try:
                                        midicreate.run(
                                            self.instrument, self.rN)
                                        self.noteinit()
                                        self.gm = "mix"
                                        isrecording = 0
                                        pygame.mixer.music.load(
                                            "Samples/%s.mid" % (self.instrument))
                                        pygame.mixer.music.play(1)
                                    except:
                                        pygame.mixer.music.load(
                                            "Samples/Error.wav")
                                        pygame.mixer.play(1)
                            k = 77-51
                            a = [0]*k
                            font = pygame.font.SysFont("Ariel", 30, 1)
                            for i in range(k):
                                a[i] = (pygame.Rect(
                                    0, 50+(980//k)*i, 200, 1080//k))
                                pygame.draw.rect(
                                    self._frame_surface, colors[3], a[i], 3)
                                for j in range(6):
                                    t = font.render(
                                        str(j+1)+"s", True, colors[3])
                                    self._frame_surface.blit(
                                        t, (200+(1520//6)*j, 25))
                                    self.notes[i][j] = pygame.Rect(
                                        200+(1520//6)*j, 50+(980//k)*i, 1520//6, 980//k)
                                    c = (colors[2], 3) if self.rN[i][j] == 0 else (
                                        colors[0], 0)
                                    pygame.draw.rect(
                                        self._frame_surface, c[0], self.notes[i][j], c[1])
                                    if self.notes[i][j].collidepoint(self.cL) or self.notes[i][j].collidepoint(self.cR):
                                        if self.checkhover(str(i)+str(j), 2):
                                            self.rN[i][j] = abs(
                                                self.rN[i][j]-1)
                            if isrecording == "done":
                                midicreate.run(self.instrument, self.rN)
                                self.noteinit()
                                self.gm = "mix"
                                isrecording = 0
                    elif self.gm == "mix":
                        instruments = ["Piano", "Drums", "Bass", "Guitar"]
                        if self.instrument == "":
                            a = []
                            text = pygame.font.SysFont("Ariel", 60)
                            b = [0]*4
                            for i in range(4):
                                x1, y1 = (1920//4)*i, 540
                                x2, y2 = 1920//4, 540
                                xc = (x1+x2//2)
                                yc = 1080-270
                                a.append(pygame.Rect(x1, y1, x2, y2))
                                pygame.draw.rect(
                                    self._frame_surface, colors[3], a[i], 10)
                                b[i] = text.render(
                                    instruments[i], True, colors[3])
                                self._frame_surface.blit(
                                    b[i], (xc-(b[i].get_width()//2), yc-(b[i].get_height()//2)))
                                if a[i].collidepoint(self.cR) or a[i].collidepoint(self.cL):
                                    if self.checkhover(instruments[i]):
                                        self.instrument = instruments[i]
                        else:
                            text = pygame.font.SysFont("Ariel", 45)
                            if self.instrument in instruments:
                                test = self.testB
                                record = self.testR
                                self._frame_surface.blit(
                                    test, (960-265, 540-88))
                                self._frame_surface.blit(
                                    record, (960-204, 540+61))
                                self._frame_surface.blit(
                                    self.backbutton, (1720, 980))
                                if self.backbutton.get_rect(topleft=(1720, 980)).collidepoint(self.cR) or self.backbutton.get_rect(topleft=(1720, 980)).collidepoint(self.cL):
                                    if self.checkhover("back"):
                                        self.instrument = ""
                                if test.get_rect(topleft=(960-265, 540-88)).collidepoint(self.cR) or test.get_rect(topleft=(960-265, 540-88)).collidepoint(self.cL):
                                    if self.checkhover("test", 1):
                                        pygame.mixer.music.load(
                                            self.instrument+"T.mid")
                                        pygame.mixer.music.play()
                                elif record.get_rect(topleft=(960-204, 540+61)).collidepoint(self.cR) or record.get_rect(topleft=(960-204, 540+61)).collidepoint(self.cL):
                                    if self.checkhover("record"):
                                        self.gm = "record"

            pygame.display.update()

            # --- Go ahead and update the screen with what we've drawn.
            pygame.display.flip()

            # --- Limit to 60 frames per second
            self._clock.tick(30)

        # Close our Kinect sensor, close the window and quit.
        self._kinect.close()
        pygame.quit()


__main__ = "Loop Maker and Audio Tester"
game = BodyGameRuntime()
game.run()
