import sys
import xbmcplugin
import xbmcgui
import xbmc
from navigation import Navigation


if __name__ == '__main__':
    navigation = Navigation(xbmc, xbmcplugin, xbmcgui, sys.argv)
    navigation.dispatch()
