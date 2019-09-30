import os, time
path_to_watch = "."
before = dict ([(f, None) for f in os.listdir (path_to_watch)])
while 1:
    time.sleep (1)
    after = dict ([(f, None) for f in os.listdir (path_to_watch)])
    added = [f for f in after if not f in before]
    removed = [f for f in before if not f in after]
    if added:
        for vid in added:
            file_size = -1
            while file_size != os.path.getsize(event.src_path):
                file_size = os.path.getsize(event.src_path)
                time.sleep(1)
            print("added : {}".format(vid))
    before = after
