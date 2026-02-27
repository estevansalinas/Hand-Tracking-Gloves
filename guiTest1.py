from tkinter import *
import sqlite3
import re
import time
import serial
import serial.tools.list_ports


#collection of variables to make the GUI work
tempValue = "A1024B1024C1024D1024E1024F0.000G0.000H0.000I0.000J0.000K0.000"
currentValue = "A1B1C1D1E1F1.000G3.000H2.000I5.000J6.000K2.000"
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
gxLabel = Label(root)
gyLabel = Label(root)
gzLabel = Label(root)
axLabel = Label(root)
ayLabel = Label(root)
azLabel = Label(root)

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
    global gxLabel
    global gyLabel
    global gzLabel
    global axLabel
    global ayLabel
    global azLabel
    global currentValue
    global stringLabel
    global voltMax
    global percents
    global numbers


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

        pinkyLabel.config(text="Pinky:"+ str(percents[0])+"%",font=("Arial", 15))
        ringLabel.config(text="Ring:"+str(percents[1])+"%",font=("Arial", 15))
        middleLabel.config(text="Middle:"+str(percents[2])+"%",font=("Arial", 15))
        indexLabel.config(text="Index:"+str(percents[3])+"%",font=("Arial", 15))
        thumbLabel.config(text="Thumb:"+str(percents[4])+"%",font=("Arial", 15))
        gxLabel.config(text="Gyroscope X:"+str(numbers[5]),font=("Arial", 15))
        gyLabel.config(text="Gyroscope Y:"+str(numbers[6]),font=("Arial", 15))
        gzLabel.config(text="Gyroscope Z:"+str(numbers[7]),font=("Arial", 15))
        axLabel.config(text="Acceleration X:"+str(numbers[8]),font=("Arial", 15))
        ayLabel.config(text="Acceleration Y:"+str(numbers[9]),font=("Arial", 15))
        azLabel.config(text="Acceleration Z:"+str(numbers[10]),font=("Arial", 15))
        pinkyLabel.grid(row=3, column=3, pady=10)
        ringLabel.grid(row=4, column=3, pady=10)
        middleLabel.grid(row=5, column=3, pady=10)
        indexLabel.grid(row=6, column=3, pady=10)
        thumbLabel.grid(row=7, column=3, pady=10)
        gxLabel.grid(row=3, column=4,pady=10)
        gyLabel.grid(row=4, column=4,pady=10)
        gzLabel.grid(row=5, column=4,pady=10)
        axLabel.grid(row=6, column=4,pady=10)
        ayLabel.grid(row=7, column=4,pady=10)
        azLabel.grid(row=8, column=4,pady=10)
    root.after(100,stringtoValues)

caliLabel = Label(text="Keep fingers fully bent for 5 seconds",font=("Arial", 15))
#calibrate the max V for bending of fingers
def caliClick():
    global caliLabel
    caliLabel= Label(text="Keep fingers fully bent for 5 seconds",font=("Arial", 15))
    caliLabel.grid(row=13,column=3)
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
                myLabel.grid(row=2,column=3)
    


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
        myLabel.grid(row=2,column=3)
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
