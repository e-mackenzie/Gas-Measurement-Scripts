from toptica.lasersdk.dlcpro.v2_2_0 import DLCpro, NetworkConnection
import time
#Open a network connection to DLCPro and allow for thermal tuning

class laser_control():
	def __init__(self,ip):
		self.ip = str(ip)
		self.dlc = DLCpro(NetworkConnection(self.ip))
		self.dlc.Open()
		print(dlc.uptime_txt.get())
		self.dlc.Close()

	def set_therm(self,temp):
		self.dlc.Open()
		#Set temperature
		self.client.exec('laser1:dl:tc:temp_set 28')
		self.dlc.Close()

		time.sleep(5)

		self.dlc.Open()
    	#Set temperature
		self.client.exec('laser1:dl:tc:temp_set 21')
		self.dlc.Close()


