import sys
import xbmcplugin
import xbmcgui
import xbmc
from navigation import Navigation
import dreamfilm


if __name__ == '__main__':
    navigation = Navigation(dreamfilm.Dreamfilm(), xbmc, xbmcplugin, xbmcgui, sys.argv)
    navigation.dispatch()
