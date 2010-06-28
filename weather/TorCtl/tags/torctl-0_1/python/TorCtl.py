#!/usr/bin/python
# TorCtl.py -- Python module to interface with Tor Control interface.
# Copyright 2005 Nick Mathewson -- See LICENSE for licensing information.
#$Id: TorCtl.py 6843 2005-07-14 20:26:11Z nickm $

"""
TorCtl -- Library to control Tor processes.  See TorCtlDemo.py for example use.
"""

import os
import struct
import sys

class TorCtlError(Exception):
    "Generic error raised by TorControl code."
    pass

class ProtocolError(TorCtlError):
    "Raised on violations in Tor controller protocol"
    pass

class ErrorReply(TorCtlError):
    "Raised when Tor controller returns an error"
    pass

class EventHandler:
    """An 'EventHandler' wraps callbacks for the events Tor can return."""
    def __init__(self):
        """Create a new EventHandler."""
        from TorCtl0 import EVENT_TYPE
        self._map0 = {
            EVENT_TYPE.CIRCSTATUS : self.circ_status,
            EVENT_TYPE.STREAMSTATUS : self.stream_status,
            EVENT_TYPE.ORCONNSTATUS : self.or_conn_status,
            EVENT_TYPE.BANDWIDTH : self.bandwidth,
            EVENT_TYPE.NEWDESC : self.new_desc,
            EVENT_TYPE.DEBUG_MSG : self.msg,
            EVENT_TYPE.INFO_MSG : self.msg,
            EVENT_TYPE.NOTICE_MSG : self.msg,
            EVENT_TYPE.WARN_MSG : self.msg,
            EVENT_TYPE.ERR_MSG : self.msg,
            }
        self._map1 = {
            "CIRC" : self.circ_status,
            "STREAM" : self.stream_status,
            "ORCONN" : self.or_conn_status,
            "BW" : self.bandwidth,
            "DEBUG" : self.msg,
            "INFO" : self.msg,
            "NOTICE" : self.msg,
            "WARN" : self.msg,
            "ERR" : self.msg,
            "NEWDESC" : self.new_desc,
            "ADDRMAP" : self.address_mapped
            },

    def handle0(self, evbody):
        """Dispatcher: called from Connection when an event is received."""
        evtype, args = self.decode0(evbody)
        self._map0.get(evtype, self.unknownEvent)(evtype, *args)

    def decode0(self, body):
        """Unpack an event message into a type/arguments-tuple tuple."""
        if len(body)<2:
            raise ProtocolError("EVENT body too short.")
        evtype, = struct.unpack("!H", body[:2])
        body = body[2:]
        if evtype == EVENT_TYPE.CIRCSTATUS:
            if len(body)<5:
                raise ProtocolError("CIRCUITSTATUS event too short.")
            status,ident = struct.unpack("!BL", body[:5])
            path = _unterminate(body[5:]).split(",")
            args = status, ident, path
        elif evtype == EVENT_TYPE.STREAMSTATUS:
            if len(body)<5:
                raise ProtocolError("STREAMSTATUS event too short.")
            status,ident = struct.unpack("!BL", body[:5])
            target = _unterminate(body[5:])
            args = status, ident, target
        elif evtype == EVENT_TYPE.ORCONNSTATUS:
            if len(body)<2:
                raise ProtocolError("ORCONNSTATUS event too short.")
            status = ord(body[0])
            target = _unterminate(body[1:])
            args = status, target
        elif evtype == EVENT_TYPE.BANDWIDTH:
            if len(body)<8:
                raise ProtocolError("BANDWIDTH event too short.")
            read, written = struct.unpack("!LL",body[:8])
            args = read, written
        elif evtype == EVENT_TYPE.OBSOLETE_LOG:
            args = (_unterminate(body),)
        elif evtype == EVENT_TYPE.NEWDESC:
            args = (_unterminate(body).split(","),)
        elif EVENT_TYPE.DEBUG_MSG <= evtype <= EVENT_TYPE.ERR_MSG:
            args = (EVENT_TYPE.nameOf[evtype], _unterminate(body))
        else:
            args = (body,)

        return evtype, args

    def handle1(self, lines):
        """Dispatcher: called from Connection when an event is received."""
        for code, msg, data in lines:
            evtype, args = self.decode1(msg)
            self._map1.get(evtype, self.unknownEvent)(evtype, *args)

    def decode1(self, body):
        """Unpack an event message into a type/arguments-tuple tuple."""
        if " " in body:
            evtype,body = body.split(" ",1)
        else:
            evtype,body = body,""
        evtype = evtype.upper()
        if evtype == "CIRC":
            m = re.match(r"(\S+)\s+(\S+)(\s\S+)?", body)
            if not m:
                raise ProtocolError("CIRC event misformatted.")
            status,ident,path = m.groups()
            if path:
                path = path.strip().split(",")
            else:
                path = []
            args = status, ident, path
        elif evtype == "STREAM":
            m = re.match(r"(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", body)
            if not m:
                raise ProtocolError("STREAM event misformatted.")
            ident,status,circ,target = m.groups()
            args = status, ident, target, circ
        elif evtype == "ORCONN":
            m = re.match(r"(\S+)\s+(\S+)", body)
            if not m:
                raise ProtocolError("ORCONN event misformatted.")
            target, status = m.groups()
            args = status, target
        elif evtype == "BW":
            m = re.match(r"(\d+)\s+(\d+)", body)
            if not m:
                raise ProtocolError("BANDWIDTH event misformatted.")
            read, written = map(long, m.groups())
            args = read, written
        elif evtype in ("DEBUG", "INFO", "NOTICE", "WARN", "ERR"):
            args = evtype, body
        elif evtype == "NEWDESC":
            args = ((" ".split(body)),)
        elif evtype == "ADDRMAP":
            m = re.match(r'(\S+)\s+(\S+)\s+(\"[^"]+\"|\w+)')
            if not m:
                raise ProtocolError("BANDWIDTH event misformatted.")
            fromaddr, toaddr, when = m.groups()
            if when.upper() == "NEVER":
                when = None
            else:
                when = time.localtime(
                    time.strptime(when[1:-1], "%Y-%m-%d %H:%M:%S"))
            args = fromaddr, toaddr, when
        else:
            args = (body,)

        return evtype, args

    def circ_status(self, status, circID, path):
        """Called when a circuit status changes if listening to CIRCSTATUS
           events.  'status' is a member of CIRC_STATUS; circID is a numeric
           circuit ID, and 'path' is the circuit's path so far as a list of
           names.
        """
        raise NotImplemented

    def stream_status(self, status, streamID, target, circID="0"):
        """Called when a stream status changes if listening to STREAMSTATUS
           events.  'status' is a member of STREAM_STATUS; streamID is a
           numeric stream ID, and 'target' is the destination of the stream.
        """
        raise NotImplemented

    def or_conn_status(self, status, target):
        """Called when an OR connection's status changes if listening to
           ORCONNSTATUS events. 'status' is a member of OR_CONN_STATUS; target
           is the OR in question.
        """
        raise NotImplemented

    def bandwidth(self, read, written):
        """Called once a second if listening to BANDWIDTH events.  'read' is
           the number of bytes read; 'written' is the number of bytes written.
        """
        raise NotImplemented

    def new_desc(self, identities):
        """Called when Tor learns a new server descriptor if listenting to
           NEWDESC events.
        """
        raise NotImplemented

    def msg(self, severity, message):
        """Called when a log message of a given severity arrives if listening
           to INFO_MSG, NOTICE_MSG, WARN_MSG, or ERR_MSG events."""
        raise NotImplemented

    def address_mapped(self, fromAddr, toAddr, expiry=None):
        """Called when Tor adds a mapping for an address if listening
           to ADDRESSMAPPED events.
        """
        raise NotImplemented

class DebugEventHandler(EventHandler):
    """Trivial event handler: dumps all events to stdout."""
    def __init__(self, out=None):
        if out is None:
            out = sys.stdout
        self._out = out

    def handle0(self, body):
        evtype, args = self.decode0(body)
        print >>self._out,EVENT_TYPE.nameOf[evtype],args

    def handle1(self, lines):
        for code, msg, data in lines:
            print >>self._out, msg

def detectVersion(s):
    """Helper: sends a trial command to Tor to tell whether it's running
       the first or second version of the control protocol.
    """
    s.sendall("\x00\x00\r\n")
    m = s.recv(4)
    v0len, v0type = struct.unpack("!HH", m)
    if v0type == '\x00\x00':
        s.recv(v0len)
        return 0
    if '\n' not in m:
        while 1:
            c = s.recv(1)
            if c == '\n':
                break
    return 1

def parseHostAndPort(h):
    """Given a string of the form 'address:port' or 'address' or
       'port' or '', return a two-tuple of (address, port)
    """
    host, port = "localhost", 9100
    if ":" in h:
        i = h.index(":")
        host = h[:i]
        try:
            port = int(h[i+1:])
        except ValueError:
            print "Bad hostname %r"%h
            sys.exit(1)
    elif h:
        try:
            port = int(h)
        except ValueError:
            host = h

    return host, port

def get_connection(sock):
    """Given a socket attached to a Tor control port, detect the version of Tor
       and return an appropriate 'Connection' object."""
    v = detectVersion(sock)
    if v == 0:
        import TorCtl0
        return TorCtl0.Connection(sock)
    else:
        import TorCtl1
        return TorCtl1.Connection(sock)

def secret_to_key(secret, s2k_specifier):
    """Used to generate a hashed password string. DOCDOC."""
    c = ord(s2k_specifier[8])
    EXPBIAS = 6
    count = (16+(c&15)) << ((c>>4) + EXPBIAS)

    d = sha.new()
    tmp = s2k_specifier[:8]+secret
    slen = len(tmp)
    while count:
        if count > slen:
            d.update(tmp)
            count -= slen
        else:
            d.update(tmp[:count])
            count = 0
    return d.digest()

def urandom_rng(n):
    """Try to read some entropy from the platform entropy source."""
    f = open('/dev/urandom', 'rb')
    try:
        return f.read(n)
    finally:
        f.close()

def s2k_gen(secret, rng=None):
    """DOCDOC"""
    if rng is None:
        if hasattr(os, "urandom"):
            rng = os.urandom
        else:
            rng = urandom_rng
    spec = "%s%s"%(rng(8), chr(96))
    return "16:%s"%(
        binascii.b2a_hex(spec + secret_to_key(secret, spec)))

def s2k_check(secret, k):
    """DOCDOC"""
    assert k[:3] == "16:"

    k =  binascii.a2b_hex(k[3:])
    return secret_to_key(secret, k[:9]) == k[9:]

def run_example(host,port):
    print "host is %s:%d"%(host,port)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host,port))
    c = Connection(s)
    c.set_event_handler(DebugEventHandler())
    th = c.launchThread()
    c.authenticate()
    print "nick",`c.get_option("nickname")`
    print c.get_option("DirFetchPeriod\n")
    print `c.get_info("version")`
    #print `c.get_info("desc/name/moria1")`
    print `c.get_info("network-status")`
    print `c.get_info("addr-mappings/all")`
    print `c.get_info("addr-mappings/config")`
    print `c.get_info("addr-mappings/cache")`
    print `c.get_info("addr-mappings/control")`
    print `c.map_address([("0.0.0.0", "Foobar.com"),
                        ("1.2.3.4", "foobaz.com"),
                        ("frebnitz.com", "5.6.7.8"),
                        (".", "abacinator.onion")])`
    print `c.extend_circuit(0,["moria1"])`
    try:
        print `c.extend_circuit(0,[""])`
    except ErrorReply:
        print "got error. good."
    #send_signal(s,1)
    #save_conf(s)

    #set_option(s,"1")
    #set_option(s,"bandwidthburstbytes 100000")
    #set_option(s,"runasdaemon 1")
    #set_events(s,[EVENT_TYPE.WARN])
    c.set_events([EVENT_TYPE.ORCONNSTATUS, EVENT_TYPE.STREAMSTATUS,
                  EVENT_TYPE.CIRCSTATUS, EVENT_TYPE.INFO_MSG,
                  EVENT_TYPE.BANDWIDTH])

    th.join()
    return

if __name__ == '__main__':
    if len(sys.argv) > 2:
        print "Syntax: TorControl.py torhost:torport"
        sys.exit(0)
    else:
        sys.argv.append("localhost:9051")
    sh,sp = parseHostAndPort(sys.argv[1])
    run_example(sh,sp)

