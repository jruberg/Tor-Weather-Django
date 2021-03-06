/*
 * File Waiter.cs
 * 
 * Copyright (C) 2005 Oliver Rau (olra0001@student-zw.fh-kl.de)
 * 
 * See LICENSE file for copying information 
 * 
 * Created on 08.08.2005 20:37
 * 
 * $Id: Waiter.cs 6862 2005-11-09 21:47:04Z nickm $
 */

using System;
using System.Threading;


namespace Tor.Control
{
	/// <summary>
	/// Description of Waiter.
	/// </summary>
	public class Waiter
	{
		Guid id;
		
		public Guid Id {
			get {
				return id;
			}
		}
				
		object response;
		
		public Waiter()
		{
			id = Guid.NewGuid();
		}
		
		public object Response {
			get {
				try {
					while (response == null)
						Thread.Sleep(1);
					
				} catch (Exception ex) {
					return null;
				}
					
				return response;
			}
			set {
				response = value;
			}
		}
	}
}
