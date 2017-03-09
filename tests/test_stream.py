# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sys

if sys.version_info[0] == 2:
    from cStringIO import StringIO
else:
    from io import StringIO

import pytest

from pyte import control as ctrl, escape as esc
from pyte.screens import Screen
from pyte.streams import Stream, DebugStream


class counter(object):
    def __init__(self):
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1


class argcheck(counter):
    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        super(argcheck, self).__call__()


class argstore(object):
    def __init__(self):
        self.seen = []

    def __call__(self, *args):
        self.seen.extend(args)


def test_basic_sequences():
    for cmd, event in Stream.escape.items():
        screen = Screen(80, 24)
        handler = counter()
        setattr(screen, event, handler)

        stream = Stream(screen)
        stream.feed_str(ctrl.ESC)
        assert not handler.count

        stream.feed_str(cmd)
        assert handler.count == 1, event


def test_linefeed():
    # ``linefeed`` is somewhat an exception, there's three ways to
    # trigger it.
    handler = counter()
    screen = Screen(80, 24)
    screen.linefeed = handler

    stream = Stream(screen)
    stream.feed_str(ctrl.LF + ctrl.VT + ctrl.FF)
    assert handler.count == 3


def test_unknown_sequences():
    handler = argcheck()
    screen = Screen(80, 24)
    screen.debug = handler

    stream = Stream(screen)
    stream.feed_str(ctrl.CSI + "6;Z")
    assert handler.count == 1
    assert handler.args == (6, 0)
    assert handler.kwargs == {}


def test_non_csi_sequences():
    for cmd, event in Stream.csi.items():
        # a) single param
        handler = argcheck()
        screen = Screen(80, 24)
        setattr(screen, event, handler)

        stream = Stream(screen)
        stream.feed_str(ctrl.ESC + "[5" + cmd)
        assert handler.count == 1
        assert handler.args == (5, )

        # b) multiple params, and starts with CSI, not ESC [
        handler = argcheck()
        screen = Screen(80, 24)
        setattr(screen, event, handler)

        stream = Stream(screen)
        stream.feed_str(ctrl.CSI + "5;12" + cmd)
        assert handler.count == 1
        assert handler.args == (5, 12)


def test_set_mode():
    bugger = counter()
    screen = Screen(80, 24)
    handler = argcheck()
    screen.debug = bugger
    screen.set_mode = handler

    stream = Stream(screen)
    stream.feed_str(ctrl.CSI + "?9;2h")
    assert not bugger.count
    assert handler.count == 1
    assert handler.args == (9, 2)
    assert handler.kwargs == {"private": True}


def test_reset_mode():
    bugger = counter()
    screen = Screen(80, 24)
    handler = argcheck()
    screen.debug = bugger
    screen.reset_mode = handler

    stream = Stream(screen)
    stream.feed_str(ctrl.CSI + "?9;2l")
    assert not bugger.count
    assert handler.count == 1
    assert handler.args == (9, 2)


def test_missing_params():
    handler = argcheck()
    screen = Screen(80, 24)
    screen.cursor_position = handler

    stream = Stream(screen)
    stream.feed_str(ctrl.CSI + ";" + esc.HVP)
    assert handler.count == 1
    assert handler.args == (0, 0)


def test_overflow():
    handler = argcheck()
    screen = Screen(80, 24)
    screen.cursor_position = handler

    stream = Stream(screen)
    stream.feed_str(ctrl.CSI + "999999999999999;99999999999999" + esc.HVP)
    assert handler.count == 1
    assert handler.args == (9999, 9999)


def test_interrupt():
    bugger = argstore()
    handler = argcheck()

    screen = Screen(80, 24)
    screen.draw = bugger
    screen.cursor_position = handler

    stream = Stream(screen)
    stream.feed_str(ctrl.CSI + "10;" + ctrl.SUB + "10" + esc.HVP)

    assert not handler.count
    assert bugger.seen == [
        ctrl.SUB, "10" + esc.HVP
    ]


def test_control_characters():
    handler = argcheck()
    screen = Screen(80, 24)
    screen.cursor_position = handler

    stream = Stream(screen)
    stream.feed_str(ctrl.CSI + "10;\t\t\n\r\n10" + esc.HVP)

    assert handler.count == 1
    assert handler.args == (10, 10)


def test_set_title_icon_name():
    screen = Screen(80, 24)
    stream = Stream(screen)

    # a) set only icon name
    stream.feed_str(ctrl.OSC + "1;foo" + ctrl.ST)
    assert screen.icon_name == "foo"

    # b) set only title
    stream.feed_str(ctrl.OSC + "2;foo" + ctrl.ST)
    assert screen.title == "foo"

    # c) set both icon name and title
    stream.feed_str(ctrl.OSC + "0;bar" + ctrl.ST)
    assert screen.title == screen.icon_name == "bar"

    # d) set both icon name and title then terminate with BEL
    stream.feed_str(ctrl.OSC + "0;bar" + ctrl.BEL)
    assert screen.title == screen.icon_name == "bar"

    # e) test ➜ ('\xe2\x9e\x9c') symbol, that contains string terminator \x9c
    stream.feed_str("➜")
    assert screen.buffer[0][0].data == u"➜"


def test_compatibility_api():
    screen = Screen(80, 24)
    stream = Stream()
    stream.attach(screen)

    # All of the following shouldn't raise errors.
    # a) adding more than one listener
    stream.attach(Screen(80, 24))

    # b) feeding text
    stream.feed_str("привет")

    # c) detaching an attached screen.
    stream.detach(screen)


def test_draw_russian():
    # Test from https://github.com/selectel/pyte/issues/65
    screen = Screen(20, 1)
    screen.draw = handler = argcheck()

    stream = Stream(screen)
    stream.feed_str("Нерусский текст")
    assert handler.count == 1
    assert handler.args == ("Нерусский текст", )


def test_debug_stream():
    tests = [
        ("foo", "DRAW foo"),
        ("\x1b[1;24r\x1b[4l\x1b[24;1H",
         "SET_MARGINS 1; 24\nRESET_MODE 4\nCURSOR_POSITION 24; 1"),
    ]

    for input, expected in tests:
        output = StringIO()
        stream = DebugStream(to=output)
        stream.feed_str(input)

        lines = [l.rstrip() for l in output.getvalue().splitlines()]
        assert lines == expected.splitlines()


def test_select_other_charset():
    stream = Stream(Screen(3, 3))
    assert stream.use_utf8  # on by default.

    # a) disable utf-8
    stream.select_other_charset("@")
    assert not stream.use_utf8

    # b) unknown code -- noop
    stream.select_other_charset("X")
    assert not stream.use_utf8

    # c) enable utf-8
    stream.select_other_charset("G")
    assert stream.use_utf8
