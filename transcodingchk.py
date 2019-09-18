from ffprobe3 import FFProbe
from dateutil import parser
import pandas as pd
import subprocess
import glob,os
import datetime
import shutil
import argparse
import sys
import pyinotify
import tqdm
from pathlib import Path


class Transcoding_MAM:
    def __init__(self):
        self.path = ""
        self.file_info = []
        self.extension = ""
        self.extension_allowed = ["mp4", "mxf", "mov", "MTS" ,"*"]
        self.file_processing_status = ""
        self.parent_directory = ""
        self.file_path = ""
        
    def make_create_dir(self, user_input):
        os.chdir(self.parent_directory)
        print(user_input)
#         print(os.getcwd())
        p = Path('processing/')
        d = Path('done/')
        e = Path('error/')
        if not d.exists(): 
            os.mkdir(d)
        if not e.exists():
            os.mkdir(e)
        if not p.exists():
            os.mkdir(p)
        os.chdir(p)

    def get_duration(self,file):
        duration = subprocess.check_output(['ffprobe', '-i', file, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=%s' % ("p=0")])
        duration = duration.decode("utf-8")
        duration = float(duration)
        duration = str(datetime.timedelta(seconds=duration))

        return duration

    def get_command_stub(self, file):
        command = ["ffmpeg", "-stats", "-y", "-i", file, "-c:v", "mpeg2video", "-intra", "-dc", "10","-top","-1","-flags:v","+ilme+ildct","-b:v", "50000k", "-minrate", "50000k", "-maxrate","50000k", "-bufsize", "10000k"]

        return (command)

    def video_metatdata(self, stream_name, command, field_order_scan, video_index):
        profile = ""
        command.append("-map")
        profile = profile + stream_name.index + "_" + stream_name.codec_type + "_"
        profile = profile + stream_name.codec_name + "_"
        profile = profile + stream_name.field_order + "_"
        field_order_scan = stream_name.field_order
        video_index = stream_name.index
        profile = profile[:-1]

        return (profile, command, field_order_scan, video_index)

    def audio_metadata(self, stream_name, audio_stream_channel_map, audio_channels, audio_indexes, audio_codec_name ):
        profile = ""
        profile = profile + stream_name.index + "_" + stream_name.codec_type + "_"
        profile = profile + stream_name.codec_name + "_"
        profile = profile + stream_name.channels + "_"
        audio_stream_channel_map[stream_name.index] = stream_name.channels
        audio_channels = stream_name.channels 
        
        if audio_channels is not "":
            audio_channels = int(audio_channels)

        audio_indexes.append(stream_name.index)
        audio_codec_name = "pcm_s" + "16" + "le"
        profile = profile[:-1]

        return (profile, audio_stream_channel_map, audio_channels, audio_indexes, audio_codec_name )

    def data_metadata(self, stream_name):
        profile= ""
        profile = profile + stream_name.index + "_" + stream_name.codec_type + "_"
        profile = profile + stream_name.codec_name + "_"
        profile = profile[:-1]

        return(profile)

    def no_audio(self, command, video_index, output_file):
        video_map_loaction = "0:" + video_index
        command.append(video_map_loaction)

        return (command, video_map_loaction)

    def audio_present(self, command, video_index, audio_indexes, audio_stream_channel_map,audio_codec_name, output_file):
        video_map_loaction = "0:" + video_index
        temp_audio_info = []
        temp_audio_info.append(video_map_loaction)
        for i in range(int(len(audio_indexes))):
            for j in range(int(audio_stream_channel_map[audio_indexes[i]])):
                temp_audio_info.append("-map")
                temp_audio_info.append("0:" + str(int(audio_indexes[i])))
                print(temp_audio_info)

            #keep the count of the channel index already mapped
            map_channel_num = 1
    #         stream_channel_num = 0
            #FOR THE  NUMBER OF STREAMS
        for key in audio_stream_channel_map.keys():
            for i in range(int(audio_stream_channel_map[key])):
                temp_audio_info.append("-map_channel")
                temp_audio_info.append("0." + str(key) + "." + str(i) + ":0." + str(map_channel_num) + ".0" )
                map_channel_num = map_channel_num + 1
        command =  command + temp_audio_info

        return command

    def command_type_check(self, field_order_scan, command):
        if field_order_scan == "progressive" or field_order_scan == "unknown":
            remove_arg = ["-top","-1","-flags:v","+ilme+ildct"]
            list1 = [ele for ele in command if ele not in remove_arg] 
            command = list1
            return command
        else:
            # print(command)
            return command
    
    
    def get_audiocodec_output(self, command, audio_channels, audio_codec_name, output_file):
        if audio_channels == "":
            command.append(output_file)
            
            return command
        else:
            command.append("-c:a")
            command.append(audio_codec_name)
            command.append(output_file)

            return command
        
    def Move_To_Dest(self, output_file, retcode):
        print(output_file)
        if retcode is 0:
            try:
                print(output_file) 
                print(self.parent_directory + "/" + "done")
                shutil.move(output_file, self.parent_directory + "/" +"done" )
            except:
                os.remove(self.parent_directory + "/" + "done" + '/' + output_file.split('/')[-1])
                shutil.move(output_file, self.parent_directory + "/" +  "done")
        else:
            self.file_processing_status = "ERROR"
        
    def add_fileprofile(self, file, file_profile, duration):
        temp = []
        temp.append(file.split("/")[-1])
        temp.append(file_profile)
        temp.append(duration)
        temp.append(self.file_processing_status)
        self.file_info.append(temp)
    
    def dest_files(self):
        if self.extension is "*":
            path = self.path + "/" "*"
        else:
            path = self.path + "/" "*." + self.extension 
        
        return path
    def Transcoding(self):
        destination = self.file_path
        print(destination)
        for file in glob.glob(destination):
            if file.split('.')[-1] not in self.extension_allowed:
                continue
            print(file)
            output_file = os.getcwd() + "/" + ((file.split('/')[-1]).split('.')[0]) + ".mxf"
            print(output_file)
            duration = self.get_duration(file)
            metadata = FFProbe(file)
            streams_metadata = metadata.streams
            field_order_scan = ""
            audio_channels = ""
            video_index = ""
            audio_indexes = []
            audio_stream_channel_map = {}
            audio_codec_name = ""
            file_profile = "" 
            file_processing_status = ""
            command = self.get_command_stub(file)

            for stream_name in streams_metadata:    
                if stream_name.codec_type == "video":
                    profile,command, field_order_scan, video_index= self.video_metatdata(stream_name, command, field_order_scan, video_index)
                    file_profile = file_profile + profile.split('_')[2] + "_" + profile.split('_')[3] + "_"

                elif stream_name.codec_type == "audio":
                    profile, audio_stream_channel_map, audio_channels, audio_indexes, audio_codec_name  = self.audio_metadata(stream_name, audio_stream_channel_map, audio_channels, audio_indexes, audio_codec_name )
                    file_profile = file_profile + "_" + str(audio_channels) 

                elif stream_name.codec_type == "data":
                    profile = self.data_metadata(stream_name)
                
                print(profile)
            if audio_channels == "":
                command, video_index  = self.no_audio(command, video_index, output_file)

            elif ((type(audio_channels) is int) and (audio_channels >= 1)) :
                command = self.audio_present(command, video_index, audio_indexes, audio_stream_channel_map,audio_codec_name, output_file)

            command = self.get_audiocodec_output(command, audio_channels, audio_codec_name, output_file)
            print(field_order_scan)
            command = self.command_type_check(field_order_scan,command)
            print(1)
            print(command)
            
            try:
                self.file_processing_status = "DONE"
                # command = self.command_type_check(field_order_scan)
                # print(command)    
                retcode = subprocess.call(command)
                self.Move_To_Dest(output_file, retcode)
        
            except:
                # print(command)
                self.file_processing_status = "ERROR"
                print("Cannot process file, Error logged.")
        
            self.add_fileprofile(file,file_profile,duration)
            
    def write_output(self):
        data = pd.DataFrame(self.file_info, columns=["Filename", "Profile", "Duration", "Status"])
        data.to_csv('out.csv',mode = 'a',  index = False)
    
    def check_extension(self, extension):
        if extension in self.extension_allowed:
            return True
        else:
            return False
        
#class MyEventHandler(pyinotify.ProcessEvent):
#    def process_IN_CLOSE_WRITE(self, event):
#        if event.pathname.split(".")[-1] in ["mp4", "mxf", "mov", "MTS", 'mts']:
#            print(event.pathname)
#            transcod_obj = Transcoding_MAM()
#            transcod_obj.parent_directory = os.getcwd()
#            transcod_obj.parent_directory = '.'
#            transcod_obj.path = '/sharepoint/TO_TRANSCODE/'
#            transcod_obj.file_path = event.pathname 
#            transcod_obj.make_create_dir(transcod_obj.path)
#            transcod_obj.Transcoding()
#            transcod_obj.write_output()
#            os.chdir(transcod_obj.parent_directory)

#if __name__== "__main__":
#    print("Starting Watcher")
#    wm = pyinotify.WatchManager()
#    wm.add_watch('/sharepoint/TO_TRANSCODE/', pyinotify.ALL_EVENTS, rec=True)
#    eh = MyEventHandler()
#    notifier = pyinotify.Notifier(wm, eh)
#    notifier.loop()


import os, time
path_to_watch = "/sharepoint/TO_TRANSCODE/"
before = dict ([(f, None) for f in os.listdir (path_to_watch)])
while 1:
  time.sleep (2)
  after = dict ([(f, None) for f in os.listdir (path_to_watch)])
  added = [f for f in after if not f in before]
  removed = [f for f in before if not f in after]
  if added:
        fpath = "/sharepoint/TO_TRANSCODE/" + added[0]
        transcod_obj = Transcoding_MAM()
        transcod_obj.parent_directory = os.getcwd()
        transcod_obj.parent_directory = '.'
        transcod_obj.path = '/sharepoint/TO_TRANSCODE/'
        transcod_obj.file_path = fpath
        transcod_obj.make_create_dir(transcod_obj.path)
        transcod_obj.Transcoding()
        transcod_obj.write_output()
        os.chdir(transcod_obj.parent_directory)        
        
  #if removed: print("Removed: ", ", ".join (removed))
  before = after

