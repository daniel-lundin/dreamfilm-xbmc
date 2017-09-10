from navigation import Navigation
from mocks import Xbmc, Xbmcgui, Xbmcplugin

if __name__ == '__main__':
    argv = ['./offline_tester.py', 1]
    history = []
    history.append(argv)
    while True:
        xbmc = Xbmc()
        xbmcplugin = Xbmcplugin()
        xbmcgui = Xbmcgui()
        navigation = Navigation(xbmc, xbmcplugin, xbmcgui, argv)
        ret = navigation.dispatch()
        if ret == Xbmc.BACK:
            history = history[:-1]
            argv = history[-1]
            continue

        if not xbmcplugin.dir_items:
            continue

        for idx, item in enumerate(xbmcplugin.dir_items):
            print "%d) %s" % (idx, item[2].caption)
        print "Enter number for menu option or '..' to go back"
        inp = raw_input('>> ')
        if inp == "..":
            history = history[:-1]
            argv = history[-1]
            continue

        url = xbmcplugin.dir_items[int(inp)][1]
        url = url[url.find('?'):]
        argv = ['./offline.py', 1, url]
        history.append(argv)
