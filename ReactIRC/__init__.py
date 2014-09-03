# -*- coding: utf-8 -*-

"""
ReactIRC IRC Bot Library
~~~~~~~~~~~~~~~~~~~~~~~~

ReactIRC is a library for creating IRC. It features a simple, but powerful
interface and is heavily inspired by flask.

Basic Usage:

    bot = Bot()

    bot.on("Hello, I'm (.*)")
    def greeting(name):

        return "Hey there %s" % name

    bot.monitor(nick="bot", channel="python")

:copyright: (c) 2014 by Mihir Singh (@citruspi)
:license: MIT, see LICENSE for more details.

"""

__title__ = 'ReactIRC'
__author__ = 'Mihir Singh (@citruspi)'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014 Mihir Singh (@citruspi)'

from bot import Bot
