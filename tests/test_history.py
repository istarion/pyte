# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import operator
import os

import pyte
from pyte import control as ctrl, modes as mo
from pyte.compat import map, str


def chars(lines):
    return ["".join(map(operator.attrgetter("data"), line))
            for line in lines]


def test_index():
    screen = pyte.HistoryScreen(5, 5, history=50)

    # Filling the screen with line numbers, so it's easier to
    # track history contents.
    for idx in range(len(screen.buffer)):
        screen.draw(str(idx))
        if idx != len(screen.buffer) - 1:
            screen.linefeed()

    assert not screen.history.top
    assert not screen.history.bottom

    # a) first index, expecting top history to be updated.
    line = screen.buffer[0]
    screen.index()
    assert screen.history.top
    assert screen.history.top[-1] == line

    # b) second index.
    line = screen.buffer[0]
    screen.index()
    assert len(screen.history.top) == 2
    assert screen.history.top[-1] == line

    # c) rotation.
    for _ in range(len(screen.buffer) * screen.lines):
        screen.index()

    assert len(screen.history.top) == 25  # pages // 2 * lines


def test_reverse_index():
    screen = pyte.HistoryScreen(5, 5, history=50)

    # Filling the screen with line numbers, so it's easier to
    # track history contents.
    for idx in range(len(screen.buffer)):
        screen.draw(str(idx))
        if idx != len(screen.buffer) - 1:
            screen.linefeed()

    assert not screen.history.top
    assert not screen.history.bottom

    screen.cursor_position()

    # a) first index, expecting top history to be updated.
    line = screen.buffer[-1]
    screen.reverse_index()
    assert screen.history.bottom
    assert screen.history.bottom[0] == line

    # b) second index.
    line = screen.buffer[-1]
    screen.reverse_index()
    assert len(screen.history.bottom) == 2
    assert screen.history.bottom[1] == line

    # c) rotation.
    for _ in range(len(screen.buffer) ** screen.lines):
        screen.reverse_index()

    assert len(screen.history.bottom) == 50


def test_prev_page():
    screen = pyte.HistoryScreen(4, 4, history=40)
    screen.set_mode(mo.LNM)

    assert screen.history.position == 40

    # Once again filling the screen with line numbers, but this time,
    # we need them to span on multiple lines.
    for idx in range(len(screen.buffer) * 10):
        screen.draw(str(idx))

        screen.linefeed()

    assert screen.history.top
    assert not screen.history.bottom
    assert screen.history.position == 40
    assert len(screen.buffer) == screen.lines
    assert screen.display == [
        "37  ",
        "38  ",
        "39  ",
        "    "
    ]

    assert chars(screen.history.top)[-4:] == [
        "33  ",
        "34  ",
        "35  ",
        "36  "
    ]

    # a) first page up.
    screen.prev_page()
    assert screen.history.position == 36
    assert len(screen.buffer) == screen.lines
    assert screen.display == [
        "35  ",
        "36  ",
        "37  ",
        "38  "
    ]

    assert chars(screen.history.top)[-4:] == [
        "31  ",
        "32  ",
        "33  ",
        "34  "
    ]

    assert len(screen.history.bottom) == 2
    assert chars(screen.history.bottom) == [
        "39  ",
        "    ",
    ]

    # b) second page up.
    screen.prev_page()
    assert screen.history.position == 32
    assert len(screen.buffer) == screen.lines
    assert screen.display == [
        "33  ",
        "34  ",
        "35  ",
        "36  ",
    ]

    assert len(screen.history.bottom) == 4
    assert chars(screen.history.bottom) == [
        "37  ",
        "38  ",
        "39  ",
        "    ",
    ]

    # c) same with odd number of lines.
    screen = pyte.HistoryScreen(5, 5, history=50)
    screen.set_mode(mo.LNM)

    for idx in range(len(screen.buffer) * 10):
        screen.draw(str(idx))

        screen.linefeed()

    assert screen.history.top
    assert not screen.history.bottom
    assert screen.history.position == 50
    assert screen.display == [
        "46   ",
        "47   ",
        "48   ",
        "49   ",
        "     "
    ]

    screen.prev_page()
    assert screen.history.position == 45
    assert len(screen.buffer) == screen.lines
    assert screen.display == [
        "43   ",
        "44   ",
        "45   ",
        "46   ",
        "47   "
    ]

    assert len(screen.history.bottom) == 3
    assert chars(screen.history.bottom) == [
        "48   ",
        "49   ",
        "     ",
    ]

    # d) same with cursor in the middle of the screen.
    screen = pyte.HistoryScreen(5, 5, history=50)
    screen.set_mode(mo.LNM)

    for idx in range(len(screen.buffer) * 10):
        screen.draw(str(idx))

        screen.linefeed()

    assert screen.history.top
    assert not screen.history.bottom
    assert screen.history.position == 50
    assert screen.display == [
        "46   ",
        "47   ",
        "48   ",
        "49   ",
        "     "
    ]

    screen.cursor_to_line(screen.lines // 2)

    while screen.history.position > screen.lines:
        screen.prev_page()

    assert screen.history.position == screen.lines
    assert len(screen.buffer) == screen.lines
    assert screen.display == [
        "21   ",
        "22   ",
        "23   ",
        "24   ",
        "25   "
    ]

    while screen.history.position < screen.history.size:
        screen.next_page()

    assert screen.history.position == screen.history.size
    assert len(screen.buffer) == screen.lines
    assert screen.display == [
        "46   ",
        "47   ",
        "48   ",
        "49   ",
        "     "
    ]

    # e) same with cursor near the middle of the screen.
    screen = pyte.HistoryScreen(5, 5, history=50)
    screen.set_mode(mo.LNM)

    for idx in range(len(screen.buffer) * 10):
        screen.draw(str(idx))

        screen.linefeed()

    assert screen.history.top
    assert not screen.history.bottom
    assert screen.history.position == 50
    assert screen.display == [
        "46   ",
        "47   ",
        "48   ",
        "49   ",
        "     "
    ]

    screen.cursor_to_line(screen.lines // 2 - 2)

    while screen.history.position > screen.lines:
        screen.prev_page()

    assert screen.history.position == screen.lines
    assert len(screen.buffer) == screen.lines
    assert screen.display == [
        "21   ",
        "22   ",
        "23   ",
        "24   ",
        "25   "
    ]

    while screen.history.position < screen.history.size:
        screen.next_page()

    assert screen.history.position == screen.history.size
    assert len(screen.buffer) == screen.lines
    assert screen.display == [
        "46   ",
        "47   ",
        "48   ",
        "49   ",
        "     "
    ]


def test_next_page():
    screen = pyte.HistoryScreen(5, 5, history=50)
    screen.set_mode(mo.LNM)

    # Once again filling the screen with line numbers, but this time,
    # we need them to span on multiple lines.
    for idx in range(len(screen.buffer) * 5):
        screen.draw(str(idx))

        screen.linefeed()

    assert screen.history.top
    assert not screen.history.bottom
    assert screen.history.position == 50
    assert len(screen.buffer) == screen.lines
    assert screen.display == [
        "21   ",
        "22   ",
        "23   ",
        "24   ",
        "     "
    ]

    # a) page up -- page down.
    screen.prev_page()
    screen.next_page()
    assert screen.history.top
    assert not screen.history.bottom
    assert screen.history.position == 50
    assert screen.display == [
        "21   ",
        "22   ",
        "23   ",
        "24   ",
        "     "
    ]

    # b) double page up -- page down.
    screen.prev_page()
    screen.prev_page()
    screen.next_page()
    assert screen.history.position == 45
    assert screen.history.top
    assert chars(screen.history.bottom) == [
        "23   ",
        "24   ",
        "     "
    ]

    assert len(screen.buffer) == screen.lines
    assert screen.display == [
        "18   ",
        "19   ",
        "20   ",
        "21   ",
        "22   "
    ]

    # c) double page up -- double page down
    screen.prev_page()
    screen.prev_page()
    screen.next_page()
    screen.next_page()
    assert screen.history.position == 45
    assert len(screen.buffer) == screen.lines
    assert screen.display == [
        "18   ",
        "19   ",
        "20   ",
        "21   ",
        "22   "
    ]


def test_ensure_width(monkeypatch):
    screen = pyte.HistoryScreen(5, 5, history=50)
    screen.set_mode(mo.LNM)
    escape = dict(pyte.Stream.escape)
    escape.update({"N": "next_page", "P": "prev_page"})
    monkeypatch.setattr(pyte.Stream, "escape", escape)

    stream = pyte.Stream(screen)

    for idx in range(len(screen.buffer) * 5):
        stream.feed(str(idx) + os.linesep)

    assert screen.display == [
        "21   ",
        "22   ",
        "23   ",
        "24   ",
        "     "
    ]

    # a) shrinking the screen, expecting the lines displayed to
    #    be truncated.
    screen.resize(5, 2)
    stream.feed(ctrl.ESC + "P")

    assert all(len(l) != 2 for l in screen.history.top)
    assert all(len(l) == 2 for l in screen.history.bottom)
    assert screen.display == [
        "18",
        "19",
        "20",
        "21",
        "22"
    ]

    # b) expading the screen, expecting the lines displayed to
    #    be filled with whitespace characters.
    screen.resize(5, 10)
    stream.feed(ctrl.ESC + "N")

    assert all(len(l) == 10 for l in list(screen.history.top)[-3:])
    assert all(len(l) != 10 for l in screen.history.bottom)
    assert screen.display == [
        "21        ",
        "22        ",
        "23        ",
        "24        ",
        "          "
    ]


def test_not_enough_lines():
    screen = pyte.HistoryScreen(5, 5, history=6)
    screen.set_mode(mo.LNM)

    for idx in range(len(screen.buffer)):
        screen.draw(str(idx))

        screen.linefeed()

    assert screen.history.top
    assert not screen.history.bottom
    assert screen.history.position == 6
    assert screen.display == [
        "1    ",
        "2    ",
        "3    ",
        "4    ",
        "     "
    ]

    screen.prev_page()
    assert not screen.history.top
    assert len(screen.history.bottom) is 1
    assert chars(screen.history.bottom) == ["     "]
    assert screen.display == [
        "0    ",
        "1    ",
        "2    ",
        "3    ",
        "4    ",
    ]

    screen.next_page()
    assert screen.history.top
    assert not screen.history.bottom
    assert screen.display == [
        "1    ",
        "2    ",
        "3    ",
        "4    ",
        "     "
    ]


def test_draw(monkeypatch):
    screen = pyte.HistoryScreen(5, 5, history=50)
    screen.set_mode(mo.LNM)
    escape = dict(pyte.Stream.escape)
    escape.update({"N": "next_page", "P": "prev_page"})
    monkeypatch.setattr(pyte.Stream, "escape", escape)

    stream = pyte.Stream(screen)
    for idx in range(len(screen.buffer) * 5):
        stream.feed(str(idx) + os.linesep)

    assert screen.display == [
        "21   ",
        "22   ",
        "23   ",
        "24   ",
        "     "
    ]

    # a) doing a pageup and then a draw -- expecting the screen
    #    to scroll to the bottom before drawing anything.
    stream.feed(ctrl.ESC + "P")
    stream.feed(ctrl.ESC + "P")
    stream.feed(ctrl.ESC + "N")
    stream.feed("x")

    assert screen.display == [
        "21   ",
        "22   ",
        "23   ",
        "24   ",
        "x    "
    ]


def test_cursor_is_hidden(monkeypatch):
    screen = pyte.HistoryScreen(5, 5, history=50)
    escape = dict(pyte.Stream.escape)
    escape.update({"N": "next_page", "P": "prev_page"})
    monkeypatch.setattr(pyte.Stream, "escape", escape)

    stream = pyte.Stream(screen)
    for idx in range(len(screen.buffer) * 5):
        stream.feed(str(idx) + os.linesep)

    assert not screen.cursor.hidden

    stream.feed(ctrl.ESC + "P")
    assert screen.cursor.hidden
    stream.feed(ctrl.ESC + "P")
    assert screen.cursor.hidden
    stream.feed(ctrl.ESC + "N")
    assert screen.cursor.hidden
    stream.feed(ctrl.ESC + "N")
    assert not screen.cursor.hidden
