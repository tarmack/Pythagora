#!/usr/bin/python
# -*- coding: utf-8 -*

usage= "\
Usage: Pythagora [Qt-options] [KDE-options] [options]\n\
\n\
KDE/Qt mpd Client\n\
\n\
Generic options:\n\
  -h,   --help              Show help about options\n\
        --help-qt           Show Qt specific options\n\
  -v,   --verbose           Make some noise\n\
  -d,   --debug             Make a lot of noise\n\
  -q,   --quiet             Don't print anything\n\
        --nokde             Don't even try to import any KDE module\n\
\n"

qtOptions = "\
Qt options:\n\
\n\
  --display <displayname>   Use the X-server display 'displayname'\n\
  --session <sessionId>     Restore the application for the given 'sessionId'\n\
  --cmap                    Causes the application to install a private color\n\
                            map on an 8-bit display\n\
  --ncols <count>           Limits the number of colors allocated in the color\n\
                            cube on an 8-bit display, if the application is\n\
                            using the QApplication::ManyColor color\n\
                            specification\n\
  --nograb                  tells Qt to never grab the mouse or the keyboard\n\
  --dograb                  running under a debugger can cause an implicit\n\
                            -nograb, use -dograb to override\n\
  --sync                    switches to synchronous mode for debugging\n\
  --fn, --font <fontname>   defines the application font\n\
  --bg, --background <color> sets the default background color and an\n\
                            application palette (light and dark shades are\n\
                            calculated)\n\
  --fg, --foreground <color> sets the default foreground color\n\
  --btn, --button <color>   sets the default button color\n\
  --name <name>             sets the application name\n\
  --title <title>           sets the application title (caption)\n\
  --visual TrueColor        forces the application to use a TrueColor visual on\n\
                            an 8-bit display\n\
  --inputstyle <inputstyle> sets XIM (X Input Method) input style. Possible\n\
                            values are onthespot, overthespot, offthespot and\n\
                            root\n\
  --im <XIM server>         set XIM server\n\
  --noxim                   disable XIM\n\
  --reverse                 mirrors the whole layout of widgets\n\
  --stylesheet <file.qss>   applies the Qt stylesheet to the application widgets\n\
  --graphicssystem <system> use a different graphics system instead of the\n\
                            default one, options are raster and opengl\n\
                            (experimental)\n"
