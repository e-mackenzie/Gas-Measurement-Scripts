import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import csv
import os
import matplotlib.pyplot as plt
import time
import QuTAG
import numpy as np
from toptica.lasersdk.client import Client, NetworkConnection


"""
Laser and TCSPC control for DIAL measurments
Presents a basic interface for setting up devices and perforiming a dial measurment. 
Current TCSPC is QuTAG and laser is TOPICA DFB PRO

TO DO:
    Laser control
    Add trimming to data as time.sleep is not an accurate way to control aquistion time..
    Repeating measurment
    Nicer plotting
    HydraHarp support
    Timeres support

"""


file_path = os.path.dirname(os.path.abspath(__file__))
print(file_path)

class mainpage(tk.Frame):
    def __init__(self, parent):
        self.qutag_connect = True
        self.parent = parent
        self.init_window(parent)
        self.populate()
        
    def init_window(self, parent):
        parent.title('DIAL Control')
        #Main frame holding everything
        self.main_frame = tk.Frame(parent, bg="#708090", height=431, width=626)
        self.main_frame.pack(fill="both", expand="true")
        self.title_styles = {"font": ("Trebuchet MS Bold", 16), "background": "grey"}
        self.text_styles = {"font": ("Verdana", 14),"background": "grey","foreground": "#E1FFFF"}
        
        #Laser control frame
        self.frame_laser = tk.Frame(self.main_frame, bg="grey", relief="groove", bd=2)
        self.frame_laser.place(rely=0.1, relx=0.1, height=200, width=250)
        
        self.label_title_laser = tk.Label(self.frame_laser, self.title_styles, text="Laser Control")
        self.label_title_laser.grid(row=0, column=0, columnspan=1)
        
        self.label_ip = tk.Label(self.frame_laser, self.text_styles, text="IP addr:")
        self.label_ip.grid(row=1, column=0)
        
        self.entry_ip = tk.Entry(self.frame_laser, width=10, cursor="xterm")
        self.entry_ip.grid(row=1, column=1)
        
        self.label_t1 = tk.Label(self.frame_laser, self.text_styles, text="T1:")
        self.label_t1.grid(row=2, column=0)
        
        self.label_t2 = tk.Label(self.frame_laser, self.text_styles, text="T2:")
        self.label_t2.grid(row=3, column=0)
        
        self.entry_t1 = tk.Entry(self.frame_laser, width=10, cursor="xterm")
        self.entry_t1.grid(row=2, column=1)
        
        self.entry_t2 = tk.Entry(self.frame_laser, width=10, cursor="xterm")
        self.entry_t2.grid(row=3, column=1)
        
        self.test_button = tk.Button(self.frame_laser, text="Test Connection", command= self.laser_test_connection)
        self.test_button.place(rely=0.8, relx=0.2)

        self.manual_laser = tk.IntVar()
        self.manual_laser.set(0)
        self.c1 = tk.Checkbutton(self.frame_laser, text='Manual',variable=self.manual_laser, onvalue=1, offvalue=0)
        self.c1.place(rely=0.6,relx=0.2)


        #Time tagger control frame
        self.frame_timetag = tk.Frame(self.main_frame, bg="grey", relief="groove", bd=2)
        self.frame_timetag.place(rely=0.1, relx=0.5, height=200, width=300)
        
        self.label_title_timetag = tk.Label(self.frame_timetag, self.title_styles, text="Time Tagger")
        self.label_title_timetag.grid(row=0, column=0, columnspan=1)
        
        self.label_start = tk.Label(self.frame_timetag, self.text_styles, text="Start Channel")
        self.label_start.grid(row=1, column=0)
        
        self.label_stop = tk.Label(self.frame_timetag, self.text_styles, text="Stop Channel")
        self.label_stop.grid(row=2, column=0)
        
        self.label_binw = tk.Label(self.frame_timetag, self.text_styles, text="Bin width")
        self.label_binw.grid(row=3, column=0)
        
        self.label_binc = tk.Label(self.frame_timetag, self.text_styles, text="Bin Count")
        self.label_binc.grid(row=4, column=0)
        
        self.label_int = tk.Label(self.frame_timetag, self.text_styles, text="Capture time (each)")
        self.label_int.grid(row=5, column=0)
        
        self.entry_binw = tk.Entry(self.frame_timetag, width=10, cursor="xterm")
        self.entry_binw.grid(row=3, column=1)
        
        self.entry_binc = tk.Entry(self.frame_timetag, width=10, cursor="xterm")
        self.entry_binc.grid(row=4, column=1)
        
        self.entry_int = tk.Entry(self.frame_timetag, width=10, cursor="xterm")
        self.entry_int.grid(row=5, column=1)
        
        self.entry_start = tk.Entry(self.frame_timetag, width=10, cursor="xterm")
        self.entry_start.grid(row=1, column=1)
        
        self.entry_stop = tk.Entry(self.frame_timetag, width=10, cursor="xterm")
        self.entry_stop.grid(row=2, column=1)
        
        #Main controls
        self.frame_control = tk.Frame(self.main_frame, bg="grey", relief="groove", bd=2)
        self.frame_control.place(rely=0.7, relx=0.25, height=80, width=300)
        
        self.start_button = tk.Button(self.frame_control, text="Start", command= self.run_meas)
        self.start_button.place(rely=0.5, relx=0.1)


        self.progress = ttk.Progressbar(self.main_frame,orient = 'horizontal',length = 100, mode = 'determinate')
        self.progress.place(rely=0.9, relx=0.1, height=10, width=500)
        self.progress['value'] = 0

        #Try initialize qutag DLL wrapper 
        try:
            self.qutag = QuTAG.QuTAG()
            #Check device is responsive
            try:
                print('Device Version: ',str(self.qutag.getVersion()))
            except Exception as e:
                self.qutag_connect = False
                print('--------------')
                print('Error connecting to QuTAG device: ')
                print(e)

                print('--------------')
        except Exception as e:
            self.qutag_connect = False
            print('--------------')
            print('Unable to initialize QuTAG wrapper:')
            print(e)
            print('--------------')
        if self.qutag_connect == False:
            self.label_timetag_warn = tk.Label(self.frame_timetag, {"font": ("Trebuchet MS Bold", 12), "background": "red"}, text="Could not connect to QuTAG!")
            self.label_timetag_warn.grid(row=6, column=0, columnspan=1)

    def laser_com_test(self,laser_ip):
        #Test connection to laser 
        try:
            with Client(NetworkConnection(laser_ip)) as client:
                laser_reply = client.get('system-label', str)
        except:
            laser_reply = 'No connection to DLC Pro'
        return laser_reply

    def laser_set_tc(self,laser_ip,value):
        #Chnage Tc of laser (Does feed forard work here?)
        with Client(NetworkConnection(laser_ip)) as client:
            client.set('laser1:dl:tc:temp-set', value )

    def laser_set_ic(self,laser_ip,value):
        #Chnage Ic of laser (Does feed forard work here? - No)
        with Client(NetworkConnection(laser_ip)) as client:
            client.set('laser1:dl:cc:current-offset', value )

    def laser_test_connection(self):
        print('Checking Laser Connection')
        reply = self.laser_com_test(self.entry_ip.get())
        print(reply)

    def histo(self, ch_start, ch_stop, int_t, bin_w, bin_c):
        #Grab a histogram and update progress bar 
        #Note: sleep is used to time capture time, trimming should be added or a better timing method

        self.qutag.addHistogram(ch_start,ch_stop,True)
        self.qutag.setHistogramParams(bin_w,bin_c)

        #Not a huge fan of this...
        intermediate_sleep = int_t/5
        for i in range(0,5):
            time.sleep(intermediate_sleep)
            self.progress['value'] += 10
            self.parent.update()

        data = self.qutag.getHistogram(ch_start, ch_stop, True)
        return data

    def validate_int(self, entry):
        #Simply entry validation for form - integers
        value = entry.get()
        if len(value) == 0:
            messagebox.showerror('Error', 'Entry cant be empty')
            raise Exception("")
        else:
            try:
                val = int(value)
            except ValueError as ve:
                messagebox.showerror('Error', 'Numbers only!')
                raise Exception("")

    def validate_float(self, entry):
        #Simply entry validation for form - floats 
        value = entry.get()
        if len(value) == 0:
            messagebox.showerror('Error', 'Entry cant be empty')
            raise Exception("")
        else:
            try:
                val = float(value)
            except ValueError as ve:
                messagebox.showerror('Error', 'Numbers only!')
                raise Exception("")


    def save_fields(self):
        #Save fields to file so they dont need to be entered every time
        ip = self.entry_ip.get()
        t1 = self.entry_t1.get()
        t2 = self.entry_t2.get()
        ch_start = self.entry_start.get()
        ch_stop= self.entry_stop.get()
        bin_c = self.entry_binc.get()
        bin_w = self.entry_binw.get()
        int_t = self.entry_int.get()

        dir_name = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(dir_name,'settings' + "." + 'set')

        f = open(file_path,'w', encoding='UTF8', newline='')
        writer = csv.writer(f)
        writer.writerow([ip,t1,t2,ch_start,ch_stop,bin_c,bin_w,int_t])

    def populate(self):
        #Populate fields from file
        dir_name = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(dir_name,'settings' + "." + 'set')
        data = []
        with open(file_path) as csv_file:
            csv_read = csv.reader(csv_file, delimiter=',')
            for index, row in enumerate(csv_read):
                data = row[:]

        ip = data[0]
        t1 = data[1]
        t2 = data[2]
        ch_start = data[3]
        ch_stop= data[4]
        bin_c = data[5]
        bin_w = data[6]
        int_t = data[7]

        self.entry_ip.insert(0, ip)
        self.entry_t1.insert(0, t1)
        self.entry_t2.insert(0, t2)
        self.entry_start.insert(0, ch_start)
        self.entry_stop.insert(0, ch_stop)
        self.entry_binc.insert(0, bin_c)
        self.entry_binw.insert(0, bin_w)
        self.entry_int.insert(0, int_t)

    def run_meas(self):
        #Measurment capture script
        valid = True
        try:
            self.validate_float(self.entry_t1)
            self.validate_float(self.entry_t2)
            self.validate_int(self.entry_start)
            self.validate_int(self.entry_stop)
            self.validate_int(self.entry_binc)
            self.validate_int(self.entry_binw)
            self.validate_int(self.entry_int)
        except:
            valid = False
        if valid == True:

            self.save_fields()
            
            ip = self.entry_ip.get()
            t1 = float(self.entry_t1.get())
            t2 = float(self.entry_t2.get())
            ch_start = int(self.entry_start.get())
            ch_stop= int(self.entry_stop.get())
            bin_c = int(self.entry_binc.get())
            bin_w = int(self.entry_binw.get())
            int_t = int(self.entry_int.get())
            self.progress['value'] = 0

            #Setup laser
            '''
            Add Laser initial ic setting
            Tidy up progress bar
            Figure out histo format
            Add timeres file option?
            '''

            self.progress['value'] = 0
            var = self.manual_laser.get()
            if var == True:
                #Manual laser control - promt user to chnage temp
                data1 = self.histo(ch_start, ch_stop,int_t, bin_w, bin_c)
                data1_ar = np.asarray(data1[0], dtype=np.float64)
                messagebox.showinfo('Change Laser Tune','Change the laser tune')
                data2 = self.histo(ch_start, ch_stop,int_t, bin_w, bin_c)
                data2_ar = np.asarray(data2[0], dtype=np.float64)
            else:
                #Automatic Laser control
                #Add adjustable settling time
                print('starting...')
                self.laser_set_tc(ip,t1)
                time.sleep(3)
                data1 = self.histo(ch_start, ch_stop,int_t, bin_w, bin_c)
                data1_ar = np.asarray(data1[0], dtype=np.float64)
                self.laser_set_tc(ip,t2)
                time.sleep(3)
                data2 = self.histo(ch_start, ch_stop,int_t, bin_w, bin_c)
                data2_ar = np.asarray(data2[0], dtype=np.float64)


            #Plot results
            diff = abs(data1_ar[:] - data2_ar[:])
            plt.figure(0)
            plt.clf()
            plt.title('Histograms')
            plt.plot(data1_ar)
            plt.plot(data2_ar)
            plt.legend(['t1','t2'])
            plt.xlim(0,bin_c)

            plt.figure(1)
            plt.clf()
            plt.title('Absolute Difference')
            plt.plot(diff)
            plt.xlim(0,bin_c)

            plt.show()
            self.progress['value'] = 0


            #Save data
            timestr = time.strftime("%Y%m%d-%H%M%S")
            header = ['Histogram','T1:',t1,'T2:',t2, 'Bin Width: (ps)',bin_w]
            key = ['Histo t1','Histo t2' ,'Difference']
            
            dir_name = os.path.dirname(os.path.abspath(__file__))
            file = 'DIAL' + '_' +timestr + '.csv'
            file_path = os.path.join(dir_name,'DATA',file)
            # WRITE DATA
            with open(file_path, 'w', encoding='UTF8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerow(key)
                for i in range(0, len(diff)):
                    writer.writerow([data1_ar[i], data2_ar[i], diff[i]])


root = tk.Tk()
root.geometry("726x426")
root.resizable(0, 0)

def on_closing():
    #Setup close dialog so qutag is deinitialized properly.
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        try:
            qutag.deInitialize()
            print('Closed QuTAG')
        except:
            pass
        root.destroy()

app = mainpage(root)
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
