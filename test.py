import os, time
import re
path_to_watch = "/sharepoint/TO_TRANSCODE/"
before = dict ([(f, None) for f in os.listdir (path_to_watch)])
while 1:
    time.sleep (1)
    after = dict ([(f, None) for f in os.listdir (path_to_watch)])
    added = [f for f in after if not f in before]
    removed = [f for f in before if not f in after]
    if added:
        for vid in added:
            vid = path_to_watch + vid
            path = vid
            if os.path.exists(path):
                while True:
                    try:
                        new_path= path + "_"
                        os.rename(path,new_path)
                        os.rename(new_path,path)
                        time.sleep(0.05)
                        print("path: %s " %(path))
                        break
                    except OSError:
                        time.sleep(0.05)
            print("added : {}".format(vid))
    before = after
