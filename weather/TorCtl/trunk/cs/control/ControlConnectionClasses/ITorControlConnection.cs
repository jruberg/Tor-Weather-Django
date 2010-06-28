/*
 * File ITorControlConnection
 * 
 * Copyright (C) 2005 Oliver Rau (olra0001@student-zw.fh-kl.de)
 * 
 * See LICENSE file for copying information 
 * 
 * Created on 08.08.2005 20:37
 * 
 * $Id: ITorControlConnection.cs 6862 2005-11-09 21:47:04Z nickm $
 */

using System;
using System.Collections;
using System.IO;
using System.Threading;

namespace Tor.Control
{
	/// <summary>
	/// Defines the methods for all Tor Control Connections.
	/// </summary>
	public interface ITorControlConnection
	{
		event CircuitStatusEventHandler  CircuitStatus;
		event StreamStatusEventHandler   StreamStatus;
		event OrConnStatusEventHandler   OrConnStatus;
		event BandwidthUsedEventHandler  BandwidthUsed;
		event NewDescriptorsEventHandler NewDescriptors;
		event MessageEventHandler        Message;
		event UnrecognizedEventHandler   Unrecognized;
		
		Thread LaunchThread(bool daemon);
		
		void EnableDebug();
		void EnableDebug(Stream debug);
		
		void DisableDebug();
		
		void SetConf(string key, string value);
		void SetConf(IList kvList);
		
		IList GetConf(string key);
		IList GetConf(IList keys);
		
		void SetEvents(IList events);
		
		void Authenticate(byte[] auth);
		
		void SaveConf();
		
		void Signal(string signal);
		
		Hashtable MapAddresses(IList kvLines);
		Hashtable MapAddresses(Hashtable addresses);
		
		Hashtable GetInfo(IList keys);
		string    GetInfo(string key);
		
		string ExtendCircuit(string circID, string path);
		void   CloseCircuit(string circID, bool ifUnused);
		
		void AttachStream(string streamID, string circID);
		void RedirectStream(string streamID, string address);
		void CloseStream(string streamID, byte reason);
		
		string PostDescriptor(string desc);
		

	}
}
