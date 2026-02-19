from tkinter import *
import sqlite3
import re
import time
import serial
import serial.tools.list_ports


#collection of variables to make the GUI work
tempValue = "A1024B1024C1024D1024E1024"
currentValue = "A1B1C1D1E1"
numbers = [float(num) for num in re.findall(r'\d+\.?\d*', currentValue)]
voltMax = [float(num) for num in re.findall(r'\d+\.?\d*', tempValue)]
percents = [0,0,0,0,0]
root = Tk()
root.title('The Hand Tracking Gloves')
root.geometry("700x700")
arduino = serial.Serial(baudrate=115200, timeout=.1)
update = 0
myLabel = Label(root)
stringLabel = Label(root)
pinkyLabel = Label(root)
ringLabel = Label(root)
middleLabel = Label(root)
indexLabel = Label(root)
thumbLabel = Label(root)

#start updating the values
def run():
    global update
    update = 1
    runButton.config(state=DISABLED)
    stopButton.config(state=NORMAL)

#stop updating the values
def stop():
    global update
    update = 0
    runButton.config(state=NORMAL)
    stopButton.config(state=DISABLED)

#break down recieved string to displayable values
def stringtoValues():
    global pinkyLabel
    global ringLabel
    global middleLabel
    global indexLabel
    global thumbLabel
    global currentValue
    global stringLabel
    global voltMax
    global percents

    #test GUI case, display the sliders for creating test strings
    if(update):
        numbers = [float(num) for num in re.findall(r'\d+\.?\d*', currentValue)]
        percents[0] = (numbers[0]/voltMax[0])*100 #pinky
        percents[1] = (numbers[1]/voltMax[1])*100 #ring
        percents[2] = (numbers[2]/voltMax[2])*100 #middle
        percents[3] = (numbers[3]/voltMax[3])*100 #index
        percents[4] = (numbers[4]/voltMax[4])*100 #thumb

        arrayCheck = [0,1,2,3,4]
        for x in arrayCheck:
            if percents[x] > 100:
                voltMax[x] = numbers[x]


        pinkyLabel.destroy()
        ringLabel.destroy()
        middleLabel.destroy()
        indexLabel.destroy()
        thumbLabel.destroy() 
        pinkyLabel = Label(text="Pinky:"+ str(percents[0])+"%",font=("Arial", 20))
        ringLabel = Label(text="Ring:"+str(percents[1])+"%",font=("Arial", 20))
        middleLabel = Label(text="Middle:"+str(percents[2])+"%",font=("Arial", 20))
        indexLabel = Label(text="Index:"+str(percents[3])+"%",font=("Arial", 20))
        thumbLabel = Label(text="Thumb:"+str(percents[4])+"%",font=("Arial", 20))
        pinkyLabel.grid(row=3, column=5, pady=10)
        ringLabel.grid(row=4, column=5, pady=10)
        middleLabel.grid(row=5, column=5, pady=10)
        indexLabel.grid(row=6, column=5, pady=10)
        thumbLabel.grid(row=7, column=5, pady=10) 
    root.after(100,stringtoValues)

caliLabel = Label(text="Keep fingers fully bent for 5 seconds",font=("Arial", 20))
#calibrate the max V for bending of fingers
def caliClick():
    global caliLabel
    caliLabel= Label(text="Keep fingers fully bent for 5 seconds",font=("Arial", 20))
    caliLabel.grid(row=13,column=5)
    root.after(5000,bendMax)

def bendMax():
    global currentValue
    global tempValue
    global caliLabel
    global voltMax
    caliLabel.destroy()
    tempValue = currentValue
    voltMax = [float(num) for num in re.findall(r'\d+\.?\d*', tempValue)]

#Sync the choosen port in GUI to be able to recieve strings from the aurdino program
def sync():
    global arduino
    global currentValue
    global myLabel
    global syncButton
    global runButton
    global stopButton
    global calibrateButton
    myLabel.destroy()
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if p.pid == 32855:
            try:
                arduino = serial.Serial(port=p.device,  baudrate=115200, timeout=.1)
                time.sleep(3)
                root.after(100,sync2)
                 

            except Exception as e:
                texts = f"{p.name} failed due to {e}"
                myLabel= Label(text=texts)
                myLabel.grid(row=2,column=5)
    


def sync2():
    global arduino
    global currentValue
    global myLabel
    global syncButton
    global runButton
    global stopButton
    global calibrateButton

    code = "58912"
    arduino.write(bytes(code,   'utf-8'))
    time.sleep(0.05)
    data = arduino.readline()
    data = data.decode("utf-8")
    if (data == "415"):
        myLabel= Label(text="Connected to the Hand Tracking Gloves")
        myLabel.grid(row=2,column=5)
        runButton.config(state=NORMAL)
        stopButton.config(state=NORMAL)
        calibrateButton.config(state=NORMAL)
        root.after(100,stringtoValues)


#Buttons 
calibrateButton = Button(root, text="Calibrate", state=NORMAL, command=caliClick,fg="blue",bg="white")
runButton = Button(root, text="Run",state=NORMAL,fg="blue",bg="white",command=run)
stopButton = Button(root, text="Stop",state=DISABLED,fg="blue",bg="white",command=stop)
syncButton = Button(root,text="Sync",state=NORMAL,fg="blue",bg="white",command=sync)

#removes labels as you update
#def deleteLabel():
    #myLabel.grid_forget() #grids
    # myLabel.destroy() other method



# initialize function of testGUI


#myLabel.destroy()
#myLabel = Label(text=clicked.get())
#myLabel.grid(row=4, column =0, pady=10)


# initialize real GUI
def realGUI():
    global syncButton
    global runButton
    global stopButton
    global calibrateButton
    syncButton.grid(row=0,column=1,padx=5)
    runButton.grid(row=0,column=2,padx=5)
    runButton.config(state=DISABLED)
    stopButton.grid(row=0,column=3,padx=5)
    stopButton.config(state=DISABLED)
    calibrateButton.grid(row=0,column=4,padx=5)
    calibrateButton.config(state=DISABLED)




# drop down selection for GUI's
realGUI()


# creating label widget




stringtoValues()


# Shoving it in onto the screen


root.mainloop()