// $Id: Bytes.java 6831 2005-06-24 18:03:27Z nickm $
// Copyright 2005 Nick Mathewson, Roger Dingledine
// See LICENSE file for copying information
package net.freehaven.tor.control;

import java.util.ArrayList;
import java.util.List;
import java.util.StringTokenizer;

/**
 * Static class to do bytewise structure manipulation in Java.
 */
/* XXXX There must be a better way to do most of this.
 * XXXX The string logic here uses default encoding, which is stupid.
 */
final class Bytes {

    /** Write the two-byte value in 's' into the byte array 'ba', starting at
     * the index 'pos'. */
    public static void setU16(byte[] ba, int pos, short s) {
        ba[pos]   = (byte)((s >> 8) & 0xff);
        ba[pos+1] = (byte)((s     ) & 0xff);
    }

    /** Write the four-byte value in 'i' into the byte array 'ba', starting at
     * the index 'pos'. */
    public static void setU32(byte[] ba, int pos, int i) {
        ba[pos]   = (byte)((i >> 24) & 0xff);
        ba[pos+1] = (byte)((i >> 16) & 0xff);
        ba[pos+2] = (byte)((i >>  8) & 0xff);
        ba[pos+3] = (byte)((i      ) & 0xff);
    }

    /** Return the four-byte value starting at index 'pos' within 'ba' */
    public static int getU32(byte[] ba, int pos) {
        return
            ((ba[pos  ]&0xff)<<24) |
            ((ba[pos+1]&0xff)<<16) |
            ((ba[pos+2]&0xff)<< 8)  |
            ((ba[pos+3]&0xff));
    }

    public static String getU32S(byte[] ba, int pos) {
        return String.valueOf( ((long)getU32(ba,pos))&0xffffffffL );
    }

    /** Return the two-byte value starting at index 'pos' within 'ba' */
    public static int getU16(byte[] ba, int pos) {
        return
            ((ba[pos  ]&0xff)<<8) |
            ((ba[pos+1]&0xff));
    }

    /** Return the string starting at position 'pos' of ba and extending
     * until a zero byte or the end of the string. */
    public static String getNulTerminatedStr(byte[] ba, int pos) {
        int len, maxlen = ba.length-pos;
        for (len=0; len<maxlen; ++len) {
            if (ba[pos+len] == 0)
                break;
        }
        return new String(ba, pos, len);
    }

    /**
     * Read bytes from 'ba' starting at 'pos', dividing them into strings
     * along the character in 'split' and writing them into 'lst'
     */
    public static void splitStr(List lst, byte[] ba, int pos, byte split) {
        while (pos < ba.length && ba[pos] != 0) {
            int len;
            for (len=0; pos+len < ba.length; ++len) {
                if (ba[pos+len] == 0 || ba[pos+len] == split)
                    break;
            }
            if (len>0)
                lst.add(new String(ba, pos, len));
            pos += len;
            if (ba[pos] == split)
                ++pos;
        }
    }

    /**
     * Read bytes from 'ba' starting at 'pos', dividing them into strings
     * along the character in 'split' and writing them into 'lst'
     */
    public static List splitStr(List lst, String str) {
        if (lst == null)
            lst = new ArrayList();
        StringTokenizer st = new StringTokenizer(str);
        while (st.hasMoreTokens())
            lst.add(st.nextToken());
        return lst;
    }

    private static final char[] NYBBLES = {
        '0', '1', '2', '3', '4', '5', '6', '7',
        '8', '9', 'A', 'B', 'C', 'D', 'E', 'F'
    };

    public static final String hex(byte[] ba) {
        StringBuffer buf = new StringBuffer();
        for (int i = 0; i < ba.length; ++i) {
            int b = ((int)ba[i]) & 0xff;
            buf.append(NYBBLES[b >> 4]);
            buf.append(NYBBLES[b&0x0f]);
        }
        return buf.toString();
    }

    private Bytes() {};
}

