This is some experimental code for decoding the trunking protocol used by
Motorola Type II Smartnet radio systems.  Note that this might not be the
cleanest code at this point.

So far, this demodulates messages and prints them out to the console; no
attempt is yet made to make sense of the address/command/group flag in the
messages.

Use this at your own risk.

# Installation

You should be able to install the block:

```bash
cd gr-trunking
mkdir build
cd build
cmake ..
make install
```

If your gnuradio blocks are not located in /usr/local, you might want to run
ccmake instead so you can update the path before configuring.

Sorry that the block doesn't have the best name or documentation.

# Usage

The included trunk_decoder.grc might work; note that I might have an
oscillator PPM correction on my SDR source.
