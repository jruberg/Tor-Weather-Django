/*
 * File TorControlException.cs
 * 
 * Copyright (C) 2005 Oliver Rau (olra0001@student-zw.fh-kl.de)
 * 
 * See LICENSE file for copying information 
 * 
 * Created on 08.08.2005 20:37
 * 
 * $Id: TorControlException.cs 6862 2005-11-09 21:47:04Z nickm $
 */

using System;

namespace Tor.Control
{
	/// <summary>
	/// Description of TorControlException.
	/// </summary>
	public class TorControlException : Exception
	{
		int errorType;
		public TorControlException(int type, String s) : base(s)
		{
			errorType = type;
		}
		
		public TorControlException(string s) : this(-1, s)
		{
		}
		
		public int ErrorType {
			get { return errorType; }
		}
		
		public string ErrorMsg {
			get {
				try {
					if (errorType == -1)
						return null;
					
					return TorControl.ErrorMsgs[errorType];
				} catch (IndexOutOfRangeException ex) {
					return "Unrecognized error #" + errorType;
				}
			}
		}
	}
}
