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
            while 1:
                t = os.popen('ffmpeg -v 5 -i "%s" -f null - 2>&1' % vid).read()
                t = re.sub(r"frame=.+?\r", "", t)
                t = re.sub(r"\[(.+?) @ 0x.+?\]", "[\\1]", t)
                print(t)
                if 'damaged' not in t:
                    break
            print("added : {}".format(vid))
    before = after
