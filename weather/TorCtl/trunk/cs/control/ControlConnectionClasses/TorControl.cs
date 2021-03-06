/*
 * File ITorControlCommands.cs
 * 
 * Copyright (C) 2005 Oliver Rau (olra0001@student-zw.fh-kl.de)
 * 
 * See LICENSE file for copying information 
 * 
 * Created on 08.08.2005 20:37
 * 
 * $Id: TorControl.cs 6862 2005-11-09 21:47:04Z nickm $
 */

using System;

namespace Tor.Control
{
	/// <summary>
	/// This class holds basic constants and values needed for communication with to.
	/// </summary>
	public class TorControl
	{
		public enum Commands {
			Error      = 0x0000,
			Done       = 0x0001,
			SetConf    = 0x0002,
			GetConf    = 0x0003,
			ConfValue  = 0x0004,
			SetEvents  = 0x0005,
			Event      = 0x0006,
			Auth       = 0x0007,
			SaveConf   = 0x0008,
			Signal     = 0x0009,
			MapAddress = 0x000A,
			GetInfo    = 0x000B,
			InfoValue  = 0x000C,
			ExtendCircuit  = 0x000D,
			AttachStream   = 0x000E,
			PostDescriptor = 0x000F,
			FragmentHeader = 0x0010,
			Fragment       = 0x0011,
			RedirectStream = 0x0012,
			CloseStream    = 0x0013,
			CloseCircuit   = 0x0014
		}

		public static string[] CommandNames = {
			"ERROR",
			"DONE",
			"SETCONF",
			"GETCONF",
			"CONFVALUE",
			"SETEVENTS",
			"EVENT",
			"AUTH",
			"SAVECONF",
			"SIGNAL",
			"MAPADDRESS",
			"GETINFO",
			"INFOVALUE",
			"EXTENDCIRCUIT",
			"ATTACHSTREAM",
			"POSTDESCRIPTOR",
			"FRAGMENTHEADER",
			"FRAGMENT",
			"REDIRECTSTREAM",
			"CLOSESTREAM",
			"CLOSECIRCUIT"
		};

		public enum Event {
			CircSatus     = 0x0001,
			StreamStatus  = 0x0002,
			OrConnStatus  = 0x0003,
			Bandwidth     = 0x0004,
			NewDescriptor = 0x0005,
			MsgDebug      = 0x0007,
			MsgInfo       = 0x0008,
			MsgNotice     = 0x0009,
			MsgWarn       = 0x000A,
			MsgError      = 0x000B
		}

		public static string[] EventNames = {
			"(0)",
			"CIRC",
			"STREAM",
			"ORCONN",
			"BW",
			"OLDLOG",
			"NEWDESC",
			"DEBUG",
			"INFO",
			"NOTICE",
			"WARN",
			"ERR"
		};
		
		public enum CircStatus {
			Launched = 0x01,
			Built    = 0x02,
			Extended = 0x03,
			Failed   = 0x04,
			Closed   = 0x05
		}
		
		public string[] CircStatusNames = {
			"LAUNCHED",
			"BUILT",
			"EXTENDED",
			"FAILED",
			"CLOSED"
		};
		
		public enum StreamStatus {
			SentConnect = 0x00,
			SentResolve = 0x01,
			Succeeded   = 0x02,
			Failed      = 0x03,
			Closed      = 0x04,
			NewConnect  = 0x05,
			NewResolve  = 0x06,
			Deatched    = 0x07
		}

		public static string[] StreamStatusNames = {
			"SENT_CONNECT",
			"SENT_RESOLVE",
			"SUCCEEDED",
			"FAILED",
			"CLOSED",
			"NEW_CONNECT",
			"NEW_RESOLVE",
			"DETACHED"
		};

		public enum ORConnStatus {
			Launched  = 0x00,
			Connected = 0x01,
			Failed    = 0x02,
			Closed    = 0x03
		}

		public static string[] ORConnStatusNames = {
			"LAUNCHED","CONNECTED","FAILED","CLOSED"
		};

		public enum Signal {
			Hup  = 0x01,
			Int  = 0x02,
			Usr1 = 0x0A,
			Usr2 = 0x0C,
			Term = 0x0F
		}

		public static string[] ErrorMsgs = {
			"Unspecified error",
			"Internal error",
			"Unrecognized message type",
			"Syntax error",
			"Unrecognized configuration key",
			"Invalid configuration value",
			"Unrecognized byte code",
			"Unauthorized",
			"Failed authentication attempt",
			"Resource exhausted",
			"No such stream",
			"No such circuit",
			"No such OR"
		};

	}
}
