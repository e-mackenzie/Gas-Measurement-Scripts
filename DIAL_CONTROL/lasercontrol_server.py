import asyncio
import websockets
from toptica.lasersdk.client import Client, NetworkConnection

laser_ip = '192.168.120.151'

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
    try:
        with Client(NetworkConnection(laser_ip)) as client:
            client.set('laser1:dl:tc:temp-set', value )
    except:
        laser_reply = 'No connection to DLC Pro'
    return laser_reply

    

#Handler for each connection
async def handler(websocket, path):
    data = await websocket.recv()
    if (data == 'test'):
        await websocket.send('Attempting to connect to DLCPro')
        reply = laser_com_test(laser_ip)
        print(reply)
        await websocket.send(reply)

    elif (data == 'set_low'):
        await websocket.send('Setting Low')
        laser_set_tc(19)

    elif (data == 'set_high'):
        await websocket.send('Setting High')
        laser_set_tc(20)
    else:
        reply = 'Not a command'
        print(reply)
        await websocket.send(reply)





#Start the websockets server
start_server = websockets.serve(handler, "localhost", 8000)
asyncio.get_event_loop().run_until_complete(start_server)
print('Server running...')
asyncio.get_event_loop().run_forever()