from midiutil import MIDIFile
import midiutil

#creates midi from array and instrument
def run(instrument,notes):
        o=instrument
        if instrument=="Piano":
                instrument=2
        elif instrument=="Guitar":
                instrument=26
        elif instrument=="Bass":
                instrument=34
        midi=MIDIFile(1)
        midi.addProgramChange(0,0,0,instrument)
        k=len(notes)
        if instrument==2:
                s=51
        elif instrument==26:
                s=40
        else:
                s=30
        for i in range(k):
                for j in range(6):
                        if notes[i][j]==1:
                                midi.addNote(0,0,s+i,j,1,100)
        
        with open("Samples/%s.mid"%(o), "wb") as output_file:
                midi.writeFile(output_file)
