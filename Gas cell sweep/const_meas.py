from toptica.lasersdk.client import Client, NetworkConnection
import numpy as np
import csv
import os
from WebSQControl import WebSQControl
import argparse
import time
import scipy
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

#t0 = time.time()
#deltat = time.time()-t0
'''


'''
os.chdir(os.path.dirname(__file__))
print(os.getcwd())


snspd_ip = '192.168.35.236'
laser_ip = '130.237.35.68'	

#Temp tune settings
on_tc = 17.83
off_tc = 19.3
ic = 90
#Current tune settings
on_ic = 87.5
off_ic = 66.1
tc = 17.83


int_time = 1
current_tune = True
detector = 1
log_file = '1atm_co2_air_nitrogen_constT17p83_87.5mA_66.1mA_2Ssettle.csv'

control_port = 12000
counts_port = 12345
websq = WebSQControl(
    TCP_IP_ADR=snspd_ip,
    CONTROL_PORT=control_port,
    COUNTS_PORT=counts_port)

def laser_com_test(laser_ip):
    #Test connection to laser 
    try:
        with Client(NetworkConnection(laser_ip)) as client:
            laser_reply = client.get('system-label', str)
    except:
        laser_reply = 'No connection to DLC Pro'
    return laser_reply

def laser_set_tc(laser_ip,value):
    #Chnage Tc of laser (Does feed forard work here?)
    with Client(NetworkConnection(laser_ip)) as client:
        client.set('laser1:dl:tc:temp-set', value )

def laser_set_ic(laser_ip,value):
    #Chnage Ic of laser (Does feed forard work here? - No)
    with Client(NetworkConnection(laser_ip)) as client:
        client.set('laser1:dl:cc:current-offset', value )


def get_counts(snspd_ip, time):
    n = round(time/0.1)
    websq.set_measurement_periode(100)   # Time in ms
    counts = websq.acquire_cnts(n)
    count_rate = 0
    for i in range(0,len(counts)):
        count_rate += counts[i][detector]
    count_rate = count_rate / n 
    return count_rate


#Main
websq.connect()
data = np.zeros(4)
start_time=time.time()

with open(log_file, 'a') as logging_file:
    writer_log = csv.writer(logging_file)
    writer_log.writerow(['timestamp', 'Difference (Hz)' ])
timestamp=[]; difference = [];
print(['timestamp', 'Difference (Hz)' ])

i = 0

#Set laser wavelength intial
if current_tune == True:
    data[0] = tc
    laser_set_tc(laser_ip,round(tc,3))
else:
    current = ic
    data[0] = current
    laser_set_ic(laser_ip,current)
while(1):
    #Main 
    if (i < 1):
        #Set laser wavelength
        if current_tune == True:
            laser_set_ic(laser_ip,round(on_ic,3))
        else:
            laser_set_tc(laser_ip,round(on_tc,3))
        time.sleep(3) 

        #Get Counts
        data[1] = get_counts(snspd_ip, int_time)
        i = 1
    else:
        #Set laser wavelength
        if current_tune == True:
            laser_set_ic(laser_ip,round(off_ic,3))
        else:
            laser_set_tc(laser_ip,round(off_tc,3))
        time.sleep(3) 
        
        #Get Counts
        data[2] = get_counts(snspd_ip, int_time)
        data[3] = data[1] - data[2]
        difference.append(data[3])
        timestamp.append(float(time.time()-start_time)/60)
        i = 0

        #Save data 
        temp_data_str = [timestamp[-1], data[1], data[2] ,difference[-1]]
        with open(log_file, 'a') as logging_file:
            writer_log = csv.writer(logging_file)
            writer_log.writerow(temp_data_str)
            
        print(temp_data_str)

        #Plot data
        plt.plot(timestamp,difference,'r.-')


    #Update figures
    plt.legend([ 'Difference'], bbox_to_anchor=(1.0, 1.0))
    plt.xlabel("Time (mins)")
    plt.ylabel("Counts (Hz)")
    plt.pause(0.5)


websq.close()




