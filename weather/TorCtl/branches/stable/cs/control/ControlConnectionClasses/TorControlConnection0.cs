/*
 * File TorControlConnection0.cs
 * 
 * Copyright (C) 2005 Oliver Rau (olra0001@student-zw.fh-kl.de)
 * 
 * See LICENSE file for copying information 
 * 
 * Created on 16.09.2005 20:46
 * 
 * $Id: TorControlConnection0.cs 6862 2005-11-09 21:47:04Z nickm $
 */

using System;
using System.Collections;
using System.IO;
using System.Net.Sockets;
using System.Text;
using System.Threading;

namespace Tor.Control
{
	/// <summary>
	/// A connection to a running Tor process.
	/// </summary>
	public class TorControlConnection0 : TorControlConnectionBase
	{
		#region Events
		public override event CircuitStatusEventHandler  CircuitStatus;
		public override event StreamStatusEventHandler   StreamStatus;
		public override event OrConnStatusEventHandler   OrConnStatus;
		public override event BandwidthUsedEventHandler  BandwidthUsed;
		public override event NewDescriptorsEventHandler NewDescriptors;
		public override event MessageEventHandler        Message;
		public override event UnrecognizedEventHandler   Unrecognized;
		#endregion
		
		BigEndianReader input;
		BigEndianWriter output;
		
		public TorControlConnection0(TcpClient connection) : this(connection.GetStream())
		{}
		
		public TorControlConnection0(Stream s) : this(new BigEndianReader(s), 
		                                              new BigEndianWriter(s))
		{}
		
		public TorControlConnection0(BigEndianReader i, BigEndianWriter o)
		{
			this.output = o;
			this.input  = i;
			
			// Synchronize the internal queue by default
			this.waiters = Queue.Synchronized(new Queue());
		}
		
		protected void SendCommand0(TorControl.Commands type, byte[] cmd)
		{
			int length = cmd == null ? 0 : cmd.Length;
			
			output.WriteShort(length);
			output.WriteShort((int)type);
			
			if (cmd != null && cmd.Length > 0)
				output.Write(cmd);
		}
		
		protected void SendCommand(TorControl.Commands type, byte[] cmd)
		{
			lock (output) {
				if (cmd == null || cmd.Length <= 65535) {
					SendCommand0(type, cmd);
					return;
				}
				
				int length = cmd.Length;
				output.WriteShort(65535);
				output.WriteShort((int)TorControl.Commands.FragmentHeader);
				output.WriteShort((int)type);
				output.WriteInt(length);
				output.Write(cmd, 0, 65535);
				
				for (int pos = 65535; pos < length; pos += 65535) {
					int flen = length-pos < 65535 ? length -pos : 65535;
					output.WriteShort(flen);
					output.WriteShort((int)TorControl.Commands.Fragment);
					output.Write(cmd, pos, flen);
				}
			}
		}
		
		protected Cmd ReadCommand0()
		{
			int len = input.ReadUInt16();
			int cmd = input.ReadUInt16();
			
			byte[] result;
			
			if (len > 0)
				result = input.ReadBytes(len);
			else
				result = new byte[0];
			
			return new Cmd((TorControl.Commands)cmd, result);
		}
		
		protected Cmd ReadCommand()
		{
			lock (input) {
				Cmd c = ReadCommand0();
				if (c.Type != TorControl.Commands.Fragment && 
				    c.Type != TorControl.Commands.FragmentHeader)
					return c;
				
				if (c.Type == TorControl.Commands.Fragment)
					throw new TorControlSyntaxException("Fragment without header");
				
				int realType = Bytes.GetU16(c.Body, 0);
				int realLen  = Bytes.GetU32(c.Body, 2);
				
				Cmd outCmd = new Cmd((TorControl.Commands)realType, realLen);
				Array.Copy(c.Body, 6, outCmd.Body, 0, c.Body.Length - 6);
				
				int pos = c.Body.Length-6;
				
				while (pos < realLen) {
					c = ReadCommand0();
					if (c.Type != TorControl.Commands.Fragment)
						throw new TorControlSyntaxException("Incomplete fragmented message");
					
					Array.Copy(c.Body, 0, outCmd.Body, pos, c.Body.Length);
					pos += c.Body.Length;
				}
				
				return outCmd;
			}
		}
		
		protected override void React()
		{
			while (true) {
				Cmd c = ReadCommand();
				if (c.Type == TorControl.Commands.Event)
					HandleEvent(c);
				else {
					Waiter w;
					lock (waiters.SyncRoot) {
						w = (Waiter) waiters.Dequeue();
					}
					w.Response = c;
				}
			}
		}
		
		protected Cmd _SendAndWaitForResponse(TorControl.Commands type, byte[] cmd)
		{
			CheckThread();
			Waiter w = new Waiter();
			
			lock (waiters.SyncRoot) {
				SendCommand(type, cmd);
				waiters.Enqueue(w);
			}
			return (Cmd) w.Response;
		}
		
		protected Cmd SendAndWaitForResponse(TorControl.Commands type, byte[] cmd,
		                                     TorControl.Commands exType1, TorControl.Commands exType2,
		                                     TorControl.Commands exType3, TorControl.Commands exType4)
		{
			Cmd c = _SendAndWaitForResponse(type, cmd);
			if (c.Type == TorControl.Commands.Error)
				throw new TorControlException(Bytes.GetU16(c.Body, 0),
				                              Bytes.GetNulTerminatedStr(c.Body,2));
			
			if (c.Type == exType1 || c.Type == exType2 || c.Type == exType3 ||
			    c.Type == exType4)
				return c;
			
			throw new TorControlSyntaxException("Unexpected reply type: " + c.Type);
		}
		
		protected Cmd SendAndWaitForResponse(TorControl.Commands type, byte[] cmd)
		{
			return SendAndWaitForResponse(type, cmd, 
			                              TorControl.Commands.Done, TorControl.Commands.Done, 
			                              TorControl.Commands.Done, TorControl.Commands.Done);
		}
		
		protected Cmd SendAndWaitForResponse(TorControl.Commands type, byte[] cmd, 
		                                     TorControl.Commands exType1)
		{
			return SendAndWaitForResponse(type, cmd, exType1, exType1, exType1, exType1);
		}
		
		protected Cmd SendAndWaitForResponse(TorControl.Commands type, byte[] cmd, 
		                                     TorControl.Commands exType1, TorControl.Commands exType2)
		{
			return SendAndWaitForResponse(type, cmd, exType1, exType2, exType2, exType2);
		}
		
		protected Cmd SendAndWaitForResponse(TorControl.Commands type, byte[] cmd, 
		                                     TorControl.Commands exType1, TorControl.Commands exType2, 
		                                     TorControl.Commands exType3)
		{
			return SendAndWaitForResponse(type, cmd, exType1, exType2, exType3, exType3);
		}
		
		protected void HandleEvent(Cmd c)
		{
			TorControl.Event type = (TorControl.Event)Bytes.GetU16(c.Body, 0);
			
			switch (type) {
				case TorControl.Event.CircSatus:
					if (this.CircuitStatus != null) {
						CircuitStatusEventArgs args;
						args = new CircuitStatusEventArgs(TorControl.StreamStatusNames[c.Body[2]],
						                                  Bytes.GetU32S(c.Body, 3),
						                                  Bytes.GetNulTerminatedStr(c.Body, 7));
						CircuitStatus(this, args);
					}
					break;
				case TorControl.Event.StreamStatus:
					if (this.StreamStatus != null) {
						StreamStatusEventArgs args;
						args = new StreamStatusEventArgs(TorControl.StreamStatusNames[c.Body[2]],
						                                 Bytes.GetU32S(c.Body, 3).ToString(),
						                                 Bytes.GetNulTerminatedStr(c.Body, 7));
						StreamStatus(this, args);
					}
					break;
				case TorControl.Event.OrConnStatus:
					if (this.OrConnStatus != null) {
						OrConnStatusEventArgs args;
						args = new OrConnStatusEventArgs(TorControl.ORConnStatusNames[c.Body[2]],
						                                 Bytes.GetNulTerminatedStr(c.Body, 3));
						OrConnStatus(this, args);
					}
					break;
				case TorControl.Event.Bandwidth:
					if (this.BandwidthUsed != null) {
						BandwidthUsedEventArgs args;
						args = new BandwidthUsedEventArgs(Bytes.GetU32(c.Body, 2),
						                                  Bytes.GetU32(c.Body, 6));
						BandwidthUsed(this, args);
					}
					break;
				case TorControl.Event.NewDescriptor:
					if (this.NewDescriptors != null) {
						IList lst = new ArrayList();
						Bytes.SplitStr(lst, c.Body, 2, (byte)',');
						NewDescriptorsEventArgs args;
						args = new NewDescriptorsEventArgs(lst);
						
						NewDescriptors(this, args);
					}
					break;
				case TorControl.Event.MsgDebug:
					if (this.Message != null) {
						MessageEventArgs args;
						args = new MessageEventArgs("DEBUG", Bytes.GetNulTerminatedStr(c.Body, 2));
						Message(this, args);
					}
					break;
				case TorControl.Event.MsgInfo:
					if (this.Message != null) {
						MessageEventArgs args;
						args = new MessageEventArgs("INFO", Bytes.GetNulTerminatedStr(c.Body, 2));
						Message(this, args);
					}
					break;
				case TorControl.Event.MsgNotice:
					if (this.Message != null) {
						MessageEventArgs args;
						args = new MessageEventArgs("NOTICE", Bytes.GetNulTerminatedStr(c.Body, 2));
						Message(this, args);
					}
					break;
				case TorControl.Event.MsgWarn:
					if (this.Message != null) {
						MessageEventArgs args;
						args = new MessageEventArgs("WARN", Bytes.GetNulTerminatedStr(c.Body, 2));
						Message(this, args);
					}
					break;
				case TorControl.Event.MsgError:
					if (this.Message != null) {
						MessageEventArgs args;
						args = new MessageEventArgs("ERR", Bytes.GetNulTerminatedStr(c.Body, 2));
						Message(this, args);
					}
					break;
				default:
					if (this.Unrecognized != null) {
						// TODO: Check if this is practicable
						UnrecognizedEventArgs args;
						args = new UnrecognizedEventArgs("UNKNOWN",
						                                 Bytes.GetNulTerminatedStr(c.Body, 3));
						Unrecognized(this, args);
					}
					break;
			}
		}
		
		public override void SetConf(IList kvList)
		{
			StringBuilder sb = new StringBuilder();
			
			foreach (string kv in kvList) {
				sb.Append(kv).Append("\n");
			}
			
			// TODO: here is ASCII fixed, if another charset is used, here should be the magic
			SendAndWaitForResponse(TorControl.Commands.SetConf, Encoding.ASCII.GetBytes(sb.ToString()));
		}
		
		public override IList GetConf(IList keys)
		{
			StringBuilder sb = new StringBuilder();
			foreach (string key in keys) {
				sb.Append(key).Append("\n");
			}
			
			Cmd c = SendAndWaitForResponse(TorControl.Commands.GetConf, Encoding.ASCII.GetBytes(sb.ToString()),
			                               TorControl.Commands.ConfValue);
			
			IList lines = new ArrayList();
			Bytes.SplitStr(lines, c.Body, 0, (byte)'\n');
			IList result = new ArrayList();
			
			foreach (string kv in lines) {
				int idx = kv.IndexOf(" ");
				result.Add(new ConfigEntry(kv.Substring(0, idx),
				                           kv.Substring(idx+1)));
			}
			
			return result;
		}
		
		public override void SetEvents(IList events)
		{
			byte[] ba = new byte[events.Count * 2];
			int i=0;
			foreach (object ev in events) {
				short e = -1;
				if (ev.GetType() == typeof(short)) {
					e = (short)ev;
				} else {
					string s = ((string)ev).ToUpper();
					for (int j = 0; j < TorControl.EventNames.Length; ++j) {
						if (TorControl.EventNames[j] == s) {
							e = (short)j;
							break;
						}
					}
					
					if (e < 0)
						throw new TorControlException("Unkown v0 code for event '" + s +"'");
				}
				
				Bytes.SetU16(ba, i, e);
				i+=2;
			}
			
			SendAndWaitForResponse(TorControl.Commands.SetEvents, ba);
			
		}
		
		public override void Authenticate(byte[] auth)
		{
			if (auth == null)
				auth = new byte[0];
			
			SendAndWaitForResponse(TorControl.Commands.Auth, auth);
		}
		
		public override void SaveConf()
		{
			SendAndWaitForResponse(TorControl.Commands.SaveConf, new byte[0]);
		}
		
		public override void Signal(string signal)
		{
			TorControl.Signal sig;
			signal = signal.ToUpper();
			
			if (signal == "HUP" || signal == "RELOAD")
				sig = TorControl.Signal.Hup;
			else if (signal == "INT" || signal == "SHUTDOWN")
				sig = TorControl.Signal.Int;
			else if (signal == "USR1" || signal == "DUMP")
				sig = TorControl.Signal.Usr1;
			else if (signal == "USR2" || signal == "DEBUG")
				sig = TorControl.Signal.Usr2;
			else if (signal == "TERM" || signal == "HALT")
				sig = TorControl.Signal.Term;
			else
				throw new TorControlException("Unrecognized value for signal()");
			
			byte[] ba = { (byte) sig};
			SendAndWaitForResponse(TorControl.Commands.Signal, ba);
		}
		
		public override Hashtable MapAddresses(IList kvLines)
		{
			StringBuilder sb = new StringBuilder();
			foreach (string line in kvLines) {
				sb.Append(line).Append("\n");
			}
			Cmd c = SendAndWaitForResponse(TorControl.Commands.MapAddress, Encoding.ASCII.GetBytes(sb.ToString()));
			Hashtable result = new Hashtable();
			IList lst = new ArrayList();
			
			Bytes.SplitStr(lst, c.Body, 0, (byte)'\n');
			foreach (string kv in lst) {
				int idx = kv.IndexOf(" ");
				result.Add(kv.Substring(0, idx), kv.Substring(idx+1));
			}
			
			return result;
		}
		
		public override Hashtable GetInfo(IList keys)
		{
			StringBuilder sb = new StringBuilder();
			
			foreach (string key in keys) {
				sb.Append(key).Append("\n");
			}
			
			Cmd c = SendAndWaitForResponse(TorControl.Commands.GetInfo, Encoding.ASCII.GetBytes(sb.ToString()),
			                               TorControl.Commands.InfoValue);
			
			Hashtable m = new Hashtable();
			IList lst = new ArrayList();
			Bytes.SplitStr(lst, c.Body, 0, (byte)0);
			if ((lst.Count % 2) != 0)
				throw new TorControlSyntaxException("Odd number of substrings from GETINFO");
			
			for (int i =0; i < lst.Count ; i+=2) {
				object k = lst[i];
				object v = lst[i+1];
				
				m.Add(k, v);
			}
			
			return m;
		}
		
		public override string ExtendCircuit(string circID, string path)
		{
			byte[] p = Encoding.ASCII.GetBytes(path);
			byte[] ba = new byte[p.Length+4];
			Bytes.SetU32(ba, 0, int.Parse(circID));
			Array.Copy(p, 0, ba, 4, p.Length);
			Cmd c = SendAndWaitForResponse(TorControl.Commands.ExtendCircuit, ba);
			return Bytes.GetU32(c.Body, 0).ToString();
		}
		
		public override void AttachStream(string streamID, string circID)
		{
			byte[] ba = new byte[8];
			Bytes.SetU32(ba, 0, int.Parse(streamID));
			Bytes.SetU32(ba, 4, int.Parse(circID));
			SendAndWaitForResponse(TorControl.Commands.AttachStream, ba);
		}
		
		public override string PostDescriptor(string desc)
		{
			return Encoding.ASCII.GetString((SendAndWaitForResponse(TorControl.Commands.PostDescriptor, 
			                                                        Encoding.ASCII.GetBytes(desc)).Body));
		}
		
		public override void RedirectStream(string streamID, string address)
		{
			byte[] addr = Encoding.ASCII.GetBytes(address);
			byte[] ba = new byte[addr.Length + 4];
			Bytes.SetU32(ba, 0, int.Parse(streamID));
			Array.Copy(addr, 0, ba, 4, addr.Length);
			SendAndWaitForResponse(TorControl.Commands.RedirectStream, ba);
		}
		
		public override void CloseStream(string streamID, byte reason)
		{
			byte[] ba = new byte[6];
			Bytes.SetU32(ba, 0, int.Parse(streamID));
			ba[4] = reason;
			ba[5] = 0;
			SendAndWaitForResponse(TorControl.Commands.CloseStream, ba);
		}
		
		public override void CloseCircuit(string circID, bool ifUsed)
		{
			byte[] ba = new byte[5];
			Bytes.SetU32(ba, 0, int.Parse(circID));
			ba[4] = (byte)(ifUsed ? 1:0);
			SendAndWaitForResponse(TorControl.Commands.CloseCircuit, ba);
		}
	}
}
