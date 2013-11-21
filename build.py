import os
import shutil
import zipfile

files = [
    'LICENSE.txt',
    'addon.xml',
    'changelog.txt',
    'default.py',
    'dreamfilm.py',
    'icon.png',
    'navigation.py'
]

with open("addon.xml") as f:
    line = f.readline()
    ver_start = line.find("version=")
    ver_end = line.find("\"", ver_start + 9)
    version = line[ver_start + 9:ver_end]

    dirname = "plugin.video.dreamfilm"
    zipname = "plugin.video.dreamfilm-%s.zip" % version
    os.mkdir(dirname)

    for f in files:
        shutil.copyfile(f, os.path.join(dirname, f))

    with zipfile.ZipFile(zipname, 'w') as z:
        for root, dirs, files in os.walk(dirname):
            for f in files:
                z.write(os.path.join(root, f))
