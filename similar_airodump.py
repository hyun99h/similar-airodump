import socket
import sys
import time
import os
import re
from struct import *

def packetcapture(interface_name):
    try:
        rawSocket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
        rawSocket.bind((interface_name,0))
        rawSocket.settimeout(1.0)
        # if 
        packet = rawSocket.recvfrom(2048)
        # 인터페이스 패킷 캡처
    except:
        return None

    radiotap_header_length = unpack('>bb', packet[0][2:4])[0]
    radiotap_header = packet[0][0:radiotap_header_length]
    if radiotap_header_length == 0:
        return None # 가끔 오류나는 것 때문에
    antenna_signal = unpack('b',radiotap_header[-2:-1])[0]
    #radiotap 헤더 - 안테나 세기 확인

    frame_data = packet[0][radiotap_header_length:]
    beacon_check = frame_data[0:1]

    if beacon_check == b'\x80' :
        bssid = ':'.join(f'{x:02x}' for x in frame_data[16:22])
        # BSSID 확인

        wireless_data = frame_data[24:]
        # beacon frame - 24byte

        tagged_parameters = wireless_data[12:]
        # fixed parameters - 12byte

        ssid_length = unpack('>b',tagged_parameters[1:2])[0]
        ssid = unpack(str(ssid_length)+'s',tagged_parameters[2:2+ssid_length])[0].decode('utf-8')
        # SSID 확인

        support_length = unpack('>b',tagged_parameters[3+ssid_length:4+ssid_length])[0]
        bych = 2 + ssid_length + 2 + support_length + 2
        channel = unpack('b',tagged_parameters[bych:bych+1])[0]
        # 채널 확인
        return {"BSSID" : bssid.upper(), "PWR" : str(antenna_signal), "Beacons" : "1", "CH" : str(channel), "ESSID" : ssid}
    else :
        return None
# Beacon frame만 체크


if len(sys.argv) ==  2:
	interface_name = str(sys.argv[1])
else:
	interface_name = "mon0"
    # 인터페이스 명 지정


iwlist = os.popen('iwlist ' + interface_name + ' channel').read()
pattern = "Channel\s\d\d\s:"
iwlist_str = re.findall(pattern, iwlist)
channel_list = []
for i in iwlist_str:
    temp = i.replace("Channel ", "")
    temp = temp.replace(" :", "")
    channel_list.append(temp)
channel_list = list(map(int, channel_list))
# 채널 확인

strFormat = "%-20s%5s%10s%5s  %-30s"
strOut = strFormat % ("BSSID", "PWR", "Beacons", "CH", "ESSID")
packet_list = []

line = os.get_terminal_size().lines
while 1:
    for i in channel_list :
        time.sleep(0.01)
        print("\x1B[H\x1B[J", end='') # 화면 깔끔하게
        sys.stdout.write('\r' + strOut)
        for j, l in enumerate(packet_list):
            if j >= line-2 :
                break
            sys.stdout.write('\r\n' + strFormat % (l["BSSID"], l["PWR"], l["Beacons"], l["CH"], l["ESSID"]))
        os.system("iwconfig " + interface_name + " channel " + str(i))
        result = packetcapture(interface_name)
        if result is None:
            continue
        else:   
            result["BSSID"]
            check = next((item for item in packet_list if item["BSSID"] == result["BSSID"]), False)
            if check == False :
                # packet_list.append(result)
                packet_list.insert(0, result)
                # 새로운 신호는 추가
            else:
                check["Beacons"]=str(int(check["Beacons"]) + 1)
                check["PWR"]=result["PWR"]
                check["CH"]=result["CH"]
                check["ESSID"]=result["ESSID"]
                del packet_list[packet_list.index(check)]
                packet_list.insert(0, check)
                # 기존 신호는 업데이트
