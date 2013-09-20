import os
import sys
curr_dir, _ = os.path.split(os.path.realpath(__file__))
print curr_dir
sys.path.append(os.path.join(curr_dir, 'resources/lib'))
import xbmcplugin
import xbmcgui
import xbmc
from navigation import Navigation


xbmc.log(', '.join(sys.argv), xbmc.LOGERROR)
if __name__ == '__main__':
    navigation = Navigation(xbmc, xbmcplugin, xbmcgui, sys.argv)
    navigation.dispatch()
