'''
A lazy variation of count_sweep.py to sweep current instead of temperature.
ould recommend using count_sweep.

Ewan MacKenzie 2021
'''

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

'''
Set Laser 
Save Ic, and Tc
loop for all tunes
	Get couunts 
	change tune
repeat for co2 in cell

TO DO:
    Get counts from snspd driver
    Add ic control?
    Ic feed forward?

'''
os.chdir(os.path.dirname(__file__))
print(os.getcwd())

snspd_ip = '192.168.35.236'
control_port = 12000
counts_port = 12345

websq = WebSQControl(
    TCP_IP_ADR=snspd_ip,
    CONTROL_PORT=control_port,
    COUNTS_PORT=counts_port)
websq.connect()

ic_correct_x = [21, 20.9, 20.6, 20.3, 20.1, 19.8, 19.6, 19.4, 19.2, 19]
ic_correct_y = [81.12, 82.14, 89.14, 90.64, 93.8, 98.95, 103.7, 109.49, 111.72, 115.77]

feed_forward_factor = -18.67

#correction_factor = interp1d(ic_correct_x, ic_correct_y, kind='cubic')

laser_ip = '130.237.35.68'
start_t = 60	
stop_t = 110
step_t = 0.1
int_time = 1
settle_time = 1
ic = 17.83
detector = 1
feed_forward = False
correct_interp = False
filename = 'sweepco21atm_current_17p83_55_115'

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
    count_rate = count_rate /(n*0.1)
    return count_rate


#Main
#print(laser_com_test(laser_ip))
temps = np.arange(start_t, stop_t, step_t)
temps = temps[::-1]
np.round(temps,3)
data = np.zeros((len(temps), 6))
print(temps)
#correct_curs = correction_factor(temps)

for i in range(0,1):
    for c, t in enumerate(temps):
        current = ic
        
        cent_diff = round( abs(start_t + abs(start_t-stop_t)/2 - t)  ,4)
        forward_cur = round( (cent_diff * feed_forward_factor) ,4)
        
        #correct_cur = round(correct_curs[c],4)
        
        if feed_forward == True:
            current = current + forward_cur
        elif correct_interp == True:
            current = correct_cur
            
        laser_set_tc(laser_ip,current)
        laser_set_ic(laser_ip,float(round(t,3)))
        time.sleep(settle_time)
        data[c,i+2] = get_counts(snspd_ip, int_time)
        data[:,1] = current
        print(round(t,3), current, data[c,i+2], cent_diff, feed_forward, forward_cur)
        
    if (i < 1):
        prompt = input('Switch gas')

print('Done')
#Save data
data[:,0] = temps
header = ['Ic=' + str(ic)]
key = ['Temp (*C)','Current (mA)' ,'Counts_1 (Hz)', 'Counts_2 (Hz)']
file = filename + '_' +str(ic) + '.csv'
# WRITE DATA
with open(file, 'w', encoding='UTF8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerow(key)
    for i in range(0, len(data)):
        writer.writerow(data[i, :])


plt.figure(0)
plt.plot(data[:,0], data[:,2])
plt.plot(data[:,0], data[:,3])

plt.figure(1)
plt.plot(data[:,0], (data[:,2]/np.max(data[:,2])))
plt.plot(data[:,0], (data[:,3]/np.max(data[:,3])) )
plt.show()


websq.close()




