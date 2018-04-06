#! /usr/bin/python3.6

import discord
import asyncio
import pyxhook, math
import psutil
import time
import logging, atexit, locale
logging.basicConfig()
locale.setlocale(locale.LC_ALL, '')

import json

token = open("token.txt", "r").read().strip()

db = {"key": 0, "keyAN": 0, "keyF": {}, "keyANF": {}, "mC": [0, 0, 0, 0, 0], "mouseD": 0.0}
try:
    db.update(json.load(open("database.json", "r")))
except Exception as e:
    print(e)

start = psutil.net_io_counters(pernic=True)['wlan0']

mousePos = [-1, -1]

lastT = 0

def save(force = False):
    global lastT
    if force or ((time.time() - lastT) > 300):
        print("Saving database....")
        lastT = time.time()
        json.dump(db, open("database.json", "w"))

def toBytes(num):
    levels = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    level = 0
    while num > 1024:
        num /= 1024.0
        level += 1
    return ("%g" % num) + levels[level]

def toNum(num, name = ""):
    levels = ["", "kilo", "mega", "giga", "tera", "peta"]
    level2s = ["", "K", "M", "B", "T"]
    level = 0
    while num > 1000:
        num /= 1000.0
        level += 1
    l = ""
    if name:
        l = " " + levels[level] + name
    else:
        l = level2s[level]
    return ("%g" % num) + l

def toDist(num):
    num *= 2.54
    return "{:,g} metres".format(num / 100)

def OnKeyPress(event):
    global keys
    db["keyF"][event.Key] = db["keyF"].get(event.Key, 0) + 1
    if(event.Key.lower() in "abcdefghijklmnopqrstuvwxyz0123456789"):
        db["keyAN"] += 1
        db["keyANF"][event.Key] = db["keyANF"].get(event.Key, 0) + 1
    db["key"] += 1
    save()
    
def OnMouseMove(event):
    global mousePos, mouseDist
    if(mousePos[0] >= 0):
        dst = math.hypot(event.Position[0] - mousePos[0], event.Position[1] - mousePos[1])
        db["mouseD"] += dst
            
    mousePos = [event.Position[0], event.Position[1]]
    save()
    
def OnMouse(event):
    mouseClicks = db["mC"]
    if "middle" in event.MessageName:
        mouseClicks[2] += 1
    elif "left" in event.MessageName:
        mouseClicks[0] += 1
    elif "right" in event.MessageName:
        mouseClicks[1] += 1
    elif "wheel down" in event.MessageName:
        mouseClicks[3] += 1
    elif "wheel up" in event.MessageName:
        mouseClicks[4] += 1
    save()

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    if message.content.startswith('~~stats'):
        embed = discord.Embed(title = 'Statistics', colour=0xDEADBF)
        embed.add_field(name = "Keystrokes", value = toNum(db["key"]), inline = False)
        embed.add_field(name = "Alphanumeric keystrokes", value = toNum(db["keyAN"]), inline = False)
        embed.add_field(name = "Mouse distance", value = toDist(db["mouseD"] / 140.917), inline = False)
        embed.add_field(name = "LMB presses", value = toNum(db["mC"][0]))
        embed.add_field(name = "RMB presses", value = toNum(db["mC"][2]))
        embed.add_field(name = "MMB presses", value = toNum(db["mC"][1]))
        embed.add_field(name = "Mouse wheel up", value = toNum(db["mC"][4]))
        embed.add_field(name = "Mouse wheel down", value = toNum(db["mC"][3]))
        current = psutil.net_io_counters(pernic=True)['wlan0']
        b_sent = current.bytes_sent - start.bytes_sent
        p_sent = (current.packets_sent - start.packets_sent)
        embed.add_field(name = "Network data sent", value = "**" + toBytes(b_sent) + "** in **" + str(p_sent) + "** packets (average: **" + toBytes(b_sent / p_sent) + "** packet size)")
        b_recv = current.bytes_recv - start.bytes_recv
        p_recv = (current.packets_recv - start.packets_recv)
        embed.add_field(name = "Network data recieved", value = "**" + toBytes(b_recv) + "** in **" + str(p_recv) + "** packets (average: **" + toBytes(b_recv / p_recv) + "** packet size)")

        keyL = list(db["keyF"].items())
        keyL = sorted(keyL, key = lambda a: -a[1])
        m = ""
        for i in range(4):
            m += "**" + keyL[i][0] + "** (%g times)\n" % (keyL[i][1])
        embed.add_field(name = "Most common keys:", value = m, inline = False)

        keyL = list(db["keyANF"].items())
        keyL = sorted(keyL, key = lambda a: -a[1])
        m = ""
        for i in range(4):
            m += "**" + keyL[i][0] + "** (%g times)\n" % (keyL[i][1])
        embed.add_field(name = "Most common alphanumeric keys:", value = m, inline = False)
        await client.send_message(message.channel, embed = embed)

hm = pyxhook.HookManager()
hm.KeyDown = OnKeyPress
hm.MouseMovement = OnMouseMove
hm.MouseAllButtonsDown = OnMouse

hm.HookKeyboard()

hm.start()

client.run(token)

atexit.register(save, True)
