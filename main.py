# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import time
import PySimpleGUI as sg
import pyautogui
import numpy as np
import cv2
from win32api import GetSystemMetrics
from PIL import ImageGrab
import datetime
import dxcam
import pyaudio
import wave
import threading
import subprocess
import os
import ffmpeg
import errno
import webbrowser
from moviepy.editor import *

#(Unused)Check if ffmpeg was installed
def check_ffmpeg():
    try:
        devnull = open(os.devnull)
        subprocess.Popen(["ffmpeg"], stdout=devnull, stderr=devnull).communicate()
    except OSError as e:
        if e.errno == errno.ENOENT:
            return False
    return True

#Video capture
def beginvid(values):
    framerate = int(values["-nfps-"])
    window["status"].update("Status: Recording", text_color='yellow')
    w = GetSystemMetrics(0)
    h = GetSystemMetrics(1)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    captured = cv2.VideoWriter("tempvid.mp4", fourcc, framerate, (w, h))
    camera = dxcam.create(output_idx=0, output_color="BGR")
    camera.start(target_fps=framerate, video_mode=True)
    while True:
        captured.write(camera.get_latest_frame())
        if is_recording == False:
            camera.stop()
            captured.release()
            vid_completed=True
            break

#Audio capture
def beginaudio(values):
    device_index=devicedic[values["-device-"]]
    audio=pyaudio.PyAudio()
    stream=audio.open(format=pyaudio.paInt16,
                      channels=2,
                      rate=44100,
                      input=True,
                      input_device_index=device_index,
                      frames_per_buffer = 1024)

    frames=[]
    while True:
        data=stream.read(1024)
        frames.append(data)
        if is_recording==False:
            stream.stop_stream()
            stream.close()
            audio.terminate()

            wavefile=wave.open("tempaudio.wav",'wb')
            wavefile.setnchannels(2)
            wavefile.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
            wavefile.setframerate(44100)
            wavefile.writeframes(b''.join(frames))
            wavefile.close()
            audio_completed=True
            break

#Replace video file's audio
def mux():
    print=sg.Print
    videoclip = VideoFileClip("tempvid.mp4")
    audioclip = AudioFileClip("tempaudio.wav")

    outputvideo=videoclip.set_audio(audioclip)
    outputvideo.write_videofile(vidname)
    local_path = os.getcwd()
    if os.path.exists(str(local_path) + "/tempvid.mp4"):
        os.remove(str(local_path) + "/tempvid.mp4")
    if os.path.exists(str(local_path) + "/tempaudio.wav"):
        os.remove(str(local_path) + "/tempaudio.wav")
    done_encoding=True
    return 69420

#if check_ffmpeg()==False:
#    sg.popup("FFMPEG not found. Please install ffmpeg")
#    webbrowser.open('https://ffmpeg.org/', new=2)
#   exit()

#Get audio device list
au=pyaudio.PyAudio()
devicelist=[]
devicedic={}
#print(au.get_device_info_by_index(1))
#cv2.waitKey(100000)
for i in range(au.get_device_count()):
    inf=au.get_device_info_by_index(i)
    if inf['hostApi']==0:
        devicelist.append(inf['name'])
        devicedic[inf['name']]=inf['index']

layout=[
    [sg.Text('Screen rec',key="-title-")],
    [sg.Text('Audio device:'),sg.Combo(devicelist,key="-device-")],
    [sg.Text("FPS:            "), sg.Input(key="-nfps-",default_text=30)],
    [sg.Text("Output folder:"),sg.Input(key="-OUT-",default_text="D:"),sg.FolderBrowse()],
    [sg.Button("Record",button_color=('white','red')),sg.Button("Stop"),sg.Exit()],
    [sg.Text("Status: Not recording",key="status")],
]
window=sg.Window('Screen rec',layout)

audio_completed=False
vid_completed=False

is_recording=False
#Event loop
while True:
    event, values = window.read(timeout=10)
    if event in ("Exit",sg.WINDOW_CLOSED):
        break
    elif event=="Record":
        is_recording=True
        window.perform_long_operation(lambda:beginaudio(values),'-audio completed-')
        window.perform_long_operation(lambda:beginvid(values),'-vid completed-')

    elif event == "Stop":
        if is_recording==True:
            is_recording=False
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
            vidname = values["-OUT-"] + '/' + f'{timestamp}.mp4'

            done_encoding=False
            window["status"].update("Status: Muxing...", text_color='yellow')
            while threading.active_count() > 1:
                window.read(timeout=100)
            window.perform_long_operation(mux,"-encode completed-")
            local_path = os.getcwd()
            audio_completed=False
            vid_completed=False
            if done_encoding==True:
                window["status"].update("Status: Done", text_color='yellow')
                done_encoding=False
    elif event=="-encode completed-":
        window["status"].update("Status: Done", text_color='yellow')
        sg.popup("Muxing completed")

window.close()
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
