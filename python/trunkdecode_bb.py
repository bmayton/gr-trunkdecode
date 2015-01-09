#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# 
# Copyright 2015 Brian D. Mayton.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
# 
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
# 

import numpy
import time
from gnuradio import gr

class TrunkControlPacket:

    def __init__(self, bits):
        self.raw_bits = self.deinterleave_bits(bits)

        # split the information and parity bits into two separate arrays
        self.info_bits = self.raw_bits[::2]
        self.parity_bits = self.raw_bits[1::2]

        # This calculates the parity bits from the information bits that were actually
        # received, and computes the "syndrome", which are the parity bits whose calculated
        # values differ from their received value.
        padded_info = [0] + self.info_bits
        self.calculated_parity_bits = []
        for i in xrange(len(self.info_bits)):
            self.calculated_parity_bits.append(padded_info[i] ^ padded_info[i+1])
        self.syndrome = [x ^ y for x, y in zip(self.parity_bits, 
            self.calculated_parity_bits)]

        # The syndrome can now be used to attempt to recover individual bit errors.  A
        # single bit error will flip the two parity bits that follow, so we look for places
        # where there are consecutive ones in the syndrome and flip the info bit that 
        # precedes them.
        for i in xrange(len(self.info_bits)-1):
            if self.syndrome[i] == 1 and self.syndrome[i+1] == 1:
                self.info_bits[i] = 1 if self.info_bits == 0 else 0

        # Break apart the information bits.  I'm not entirely sure why the inversion is
        # required at this point, but everything works with it.
        self.address =  (binlist2int(self.info_bits[:16]) ^ 0xFFFF) ^ 0x33C7
        self.groupflag = self.info_bits[16] == 0 
        self.command = (binlist2int(self.info_bits[17:27]) ^ 0x3FF) ^ 0x32A
        self.crc = binlist2int(self.info_bits[27:37]) ^ 0x3FF
        self.crc_valid = self.crc == self.compute_crc()

    def show(self, syndrome=True):
        if syndrome:
            print "".join(map(str, self.syndrome)),
        print "0x%04X 0x%03X %d" % (self.address, self.command, self.groupflag),
        if not self.crc_valid:
            print "CRC_ERROR 0x%03X != 0x%03X" % (self.crc, self.compute_crc()),
        print

    def deinterleave_bits(self, bits):
        # This deinterleaves the bits in the received message and returns the result.
        b = 1
        out = []
        for i in xrange(76):
            out.append(bits[b-1])
            b = (b + 19)
            if b > 76:
                b = (b % 76) + 1
        return out

    def compute_crc(self):
        A = 0x36E
        B = 0x393
        info = self.info_bits[:27]
        while len(info) > 0:
            if A & 1 == 1:
                A = (0x225 ^ (A >> 1)) & 0x3FF
            else:
                A = (A >> 1) & 0x3FF
            if info[0] == 1:
                B = (B ^ A) & 0x3FF
            info = info[1:]
        return B

def binlist2int(l):
    """Utility for taking a list of binary digits and turning it into an integer."""
    return int("".join(map(str, l)), 2)

class trunkdecode_bb(gr.sync_block):
    """
    docstring for block trunkdecode_bb
    """

    sync = [1,0,1,0,1,1,0,0]
    stats_interval = 10

    def __init__(self):
        gr.sync_block.__init__(self,
            name="trunkdecode_bb",
            in_sig=[numpy.byte],
            out_sig=[])
        self.pos = 0
        self.buf = []

        self.bits = 0
        self.bit_errors = 0
        self.messages = 0
        self.checksum_errors = 0
        self.last_stats = time.time()

    def update_stats(self, bits, bit_errors, messages, checksum_errors):
        """This periodically prints out statistics about the decoding.  The rate can be
        adjusted with the stats_interval class variable."""
        self.bits += bits
        self.bit_errors += bit_errors
        self.messages += messages
        self.checksum_errors += checksum_errors

        if time.time() - self.last_stats > self.stats_interval:
            bit_error_rate = 100.0
            if self.bits > 0:
                bit_error_rate = float(self.bit_errors) / self.bits * 100
            checksum_error_rate = 100.0
            if self.messages > 0:
                checksum_error_rate = float(self.checksum_errors) / self.messages * 100
            print ( "%0.03f messages/sec, bit error rate %0.05f%%, "
                "checksum error rate %0.02f%%" ) % (
                float(self.messages) / self.stats_interval,
                bit_error_rate, checksum_error_rate)

            self.bits = 0
            self.bit_errors = 0
            self.messages = 0
            self.checksum_errors = 0
            self.last_stats = time.time()

    def handle_packet(self, bits):
        """This gets called with the raw, still-interleaved bits every time a full packet
        gets demodulated."""
        pkt = TrunkControlPacket(bits)
        pkt.show()
        self.update_stats(len(pkt.syndrome), sum(pkt.syndrome), 1, 
            1 if not pkt.crc_valid else 0)

    def work(self, input_items, output_items):
        """This is the main work function for the block, which takes the incoming bits,
        synchronizes based on the packet header, and assembles chunks of bits that should
        form packets."""
        in0 = input_items[0]
        for b in in0:
            if self.pos < 8:
                # We're in the header, compare against our known header of self.sync
                if b == self.sync[self.pos]:
                    self.pos += 1
                else:
                    self.pos = 0
                self.buf = []
            elif self.pos < 8 + 76:
                # Past the header, these are data bits
                self.buf.append(b)
                self.pos += 1
                if self.pos == 8+76:
                    self.handle_packet(self.buf)
                    self.pos = 0
        return len(input_items[0])

