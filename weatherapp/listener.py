from TorCtl import TorCtl
import socket
import config
import urllib2
"""A module for listening to TorCtl for new consensus events. When one occurs,
initializes checker"""

class MyEventHandler(TorCtl.EventHandler):
    def new_consensus_event(self, event):
        urllib2.urlopen(config.run_updaters)

def main():
    ctrl_host = "127.0.0.1"
    ctrl_port = 9051
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ctrl_host, ctrl_port))
    ctrl = TorCtl.Connection(sock)
    ctrl.launch_thread(daemon=0)
    ctrl.authenticate(config.authenticator)
    ctrl.set_event_handler(MyEventHandler())
    ctrl.set_events([TorCtl.EVENT_TYPE.NEWCONSENSUS])

if __name__ == '__main__':
    main()
