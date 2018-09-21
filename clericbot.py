#!/usr/bin/env python
#
# Copyright 2011. All Rights Reserved.

"""Cleric bot."""

__author__ = 'schrepfer'

import datetime
import fnmatch
import logging
import math
import optparse
import os
import pickle
import pprint
import random
import re
import sys
import time

sys.path.insert(0, os.path.dirname(__file__) + '/pybot.zip')

from pybot import bot
from pybot import config
from pybot import events


SHOPS = {
  'plaque': {
    'post': 'n;fly;2 w;3 n;e;d;s;u',
    'church': '2 e;s;u',
    },
  'tinker': {
    'post': 'n;fly;2 e;d;s',
    'church': 'e;fly;3 e;3 s;e;d;s',
    },
  'billy': {
    'post': 'n;fly;e;2 s;e;d;n',
    'church': 'e;fly;3 e;5 s;e;d;n',
    },
  'akashia': {
    'post': 'n;fly;3 e;d;n',
    'church': 'e;fly;3 e;3 s;2 e;d;n',
    },
  'race': {
    'post': 'n;fly;w;2 s;w;d;n',
    'church': 'e;fly;3 s;w;2 s;e;d;n',
    },
  'janina': {
    'post': 'n;fly;e;s;d;w',
    'church': 'e;fly;3 e;4 s;d;w',
    },
  'mimmi': {
    'post': 'n;fly;e;2 n;d;e',
    'church': 'e;fly;3 e;s;d;e',
    },
  }

WIZARDS = [
    'altair', 'anna', 'arakorni', 'arthedain', 'avandhar', 'azynya', 'balin',
    'belabour', 'break', 'brennan', 'cheule', 'core', 'darc', 'darku', 'del',
    'deneb', 'deolon', 'deron', 'dranil', 'dusk', 'duval', 'endy', 'eod',
    'euna', 'explicit', 'farthon', 'fast', 'finderne', 'fizzban', 'fluffy',
    'friegaah', 'gandhi', 'gargo', 'geldan', 'geldor', 'gevalia', 'gonth',
    'goretongue', 'gorka', 'graerth', 'gregor', 'grungemen', 'hair', 'hammanu',
    'hub', 'hubo', 'jaden', 'jagmis', 'jared', 'juiblex', 'juicer', 'kaahn',
    'kaarle', 'kabul', 'katiria', 'kingsman', 'kreator', 'kroisos', 'larssi',
    'leper', 'lepwiztest', 'limit', 'lix', 'looser', 'loyd', 'macic', 'malys',
    'manowar', 'mehtar', 'mela', 'melkpak', 'miukkali', 'mobius', 'monte',
    'moongleam', 'morgil', 'mvx', 'neckbreaker', 'nek', 'noose', 'nullnull',
    'odium', 'om', 'opola', 'osir', 'pancreas', 'phileas', 'pim', 'pittis',
    'qase', 'salainen', 'selth', 'sepe', 'seth', 'sihu', 'squizzy', 'status',
    'sumppen', 'superfro', 'terorist', 'troops', 'turnipsi', 'ulme', 'viktor',
    'waaar', 'wilde', 'yaga', 'zagarus', 'zantar', 'zebo', 'zeith',
    ]

SNITCHES = [
    'aracno', 'springsteen', 'puti', 'gyver', 'shubby', 'chardron',
    ]

IGNORE = [
    'sunnii',
    ]

GODS = ['aquaris', 'belinik', 'kirvana', 'mordiggian', 'mortos', 'silvain', 'teros', 'xellios']

GAGS = {
  'simple': [
      # Tinker
      'The tinker asks \'Hi, what can I get for you?\'',
      'The tinker looks bored.',
      'The tinker twiddles his thumbs.',
      "The tinker says 'Only 32 more years and I can retire.'",
      # Billy
      "'A pack of sour milk is my favorite. It's very accurate.', tells Billy Bob.",
      "'Don't you remember the latest tune? Now it's payback time!', yells Billy Bob.",
      "'Get three head hits in a row and you'll get a special prize!', advertises",
      "'Hit'em hard! Those ignorant bastards!', advices Billy Bob.",
      "'I bet those rotten eggs hurt when they hit.', giggles Billy Bob.",
      "'Now is your chance to teach those tuners a lesson, use it!', advertises the",
      "'The special prize is really cool!', yells the street barker.",
      'Billy Bob.',
      "Excited Billy Bob screams: 'Get those bastards! Hit'em into groin!'",
      'street barker.',
      # Mimmi
      "Mimmi plays a happy tune with her nose and whispers to you 'I was once",
      "Mimmi says 'I had a dream about making love with Pave Maijanen'",
      "Mimmi says 'istun taikka kavelen, pylly soittaa savelen'",
      "asked to make a record with Hector'",
      "asked to make a record with Tapio Rautavaara'",
      "nahkanuijaa.'",
      "past again, she says 'Huhhuijaa ku on niin monta muijaa ja kaikki tarttee",
      'Mimmi grabs a box of candies and devours them greedily.',
      'Mimmi stares into the distance and looks like she is living in the',
      # Janina
      "Janina humms quietly 'I wanna be loved by you, just you..'",
      "Janina smiles radiantly at you and says 'What could I get for you?'",
      ],
  'glob': [
      'p: *',
      ],
  'regexp': [
      ],
  }

THINK = r'\. o O \( '
CHANNELS = r'.(mud|newbie).: '
TELLS = r'tells you \''
SAYS = r'[a-z ]+ \''

def getExpression(*parts):
  return r'(?i)^([A-Z][a-z]+) (' + '|'.join(parts) + ').*?'

COMMON = getExpression(CHANNELS, SAYS)
COMMON_DISTANT = getExpression(CHANNELS, TELLS)
COMMON_PRESENT = getExpression(SAYS)
GHOST_CHANNEL = r'(?i)^([A-Z][a-z]+) the toasted .(mud|newbie).: .*?'
GHOST_COMMON = r'(?i)^[Gg]host of ([a-z]+) [a-z ]+ \'.*?'

TIME_DELAY = 60

ME = 'me'

class TimeZone(datetime.tzinfo):
  """Eastern European Time."""

  def __init__(self, name, offset):
    self._name = name
    self._offset = offset

  def utcoffset(self, unused_dt):
    return datetime.timedelta(hours=self._offset)

  def dst(self, unused_dt):
    return datetime.timedelta(hours=self._offset - 1)

  def tzname(self, unused_dt):
    return self._name


EET = TimeZone('Europe/Helsinki', 3)


class ClericBot(bot.Bot):

  def __init__(self, options, sksp=None):
    self._casting = False
    self._enabled = True
    self._disable_till = 0
    self._execute = None
    self._file_handle = None
    self._last = None
    self._last_send = 0
    self._missing = {}
    self._moved = False
    self._options = options
    self._present = set()
    self._previous = {}
    self._previous_time = {}
    self._prompt = {}
    self._queue = []
    self._report = 0
    self._requests = {}
    self._counts = {}
    self._at_shop = False
    self._sksp = sksp
    self._todo = {}
    super(ClericBot, self).__init__()

  @property
  def options(self):
    return self._options

  @property
  def queue(self):
    return self._queue

  def status(self, message):
    print '\x1b[36m%% %s\x1b[0m' % message

  def error(self, message):
    print '\x1b[31m%% %s\x1b[0m' % message

  def isGagged(self, line):
    if line in GAGS['simple']:
      return True
    for pattern in GAGS['glob']:
      if fnmatch.fnmatch(line, pattern):
        return True
    for pattern in GAGS['regexp']:
      if re.search(pattern, line):
        return True
    return False

  @events.event(events.READ)
  def onRead(self, line):
    stripped = bot.ANSI_COLOR_PATTERN.sub('', line)
    if self.options.display and not self.isGagged(stripped):
      #sys.stdout.write('[%s] %s\n' % (time.strftime('%H:%M:%S'), line))
      sys.stdout.write('%s\n' % line)
    if self._file_handle:
      self._file_handle.write(stripped + '\n')
      self._file_handle.flush()
    return super(ClericBot, self).onRead(line)

  def send(self, commands, splitlines=True, escape=True):
    if splitlines:
      commands = commands.split(';')
    else:
      commands = [commands]
    for command in commands:
      if not command:
        continue
      self.engine.eventManager.triggerEvent(
          events.SEND, ('!' if escape else '') + command)

  @events.event(events.SEND)
  def onSend(self, line):
    if self._file_handle:
      self._file_handle.write('# '  + line + '\n')
      self._file_handle.flush()
    self._last_send = time.time()
    return True

  @property
  def idle(self):
    return time.time() - self._last_send

  def executeCommand(self, line):
    if ' ' in line:
      command, args = line.split(' ', 1)
    else:
      command, args = line, []
    if command == 'z':
      self.send(args)
      return
    if command == 'prompt':
      for key, value in sorted(self._prompt.iteritems()):
        self.status('%12s: %s' % (key, value))
      return
    if command in ('dump', 'save'):
      self.dump()
      return
    if command == 'load':
      self.load()
      return
    if command == 'trigger':
      self.engine.eventManager.triggerEvent(events.READ, args)
      return
    if command == 'time':
      now = datetime.datetime.now(EET)
      self.status('%s [night=%s]' % (now, self.night))
      return
    if command == 'enabled':
      self._enabled = not self._enabled
      self.status('Enabled: %s [running=%s]' % (self._enabled, self.running))
      return
    if command == 'status':
      self.status('Running: %s [enabled=%s, night=%s]' % (
          self.running, self._enabled, self.night))
      return
    if command in ('expr', 'eval'):
      self.status('%s\n%s' % (args, pprint.pformat(eval(args))))
      return
    self.error('Unknown command: %s' % command)

  @events.event(events.INPUT)
  def onInput(self, line):
    if line.startswith('/'):
      self.executeCommand(line.lstrip('/'))
      return
    self.engine.eventManager.triggerEvent(events.SEND, line)

  @events.event(events.STARTUP)
  def onStartup(self):
    self.load()
    self.connection.connect(self.options.address, self.options.port)
    return True

  @events.event(events.SHUTDOWN)
  def onShutdown(self):
    self.dump()
    return True

  @events.event(events.DISCONNECT)
  def onDisconnect(self):
    self.dump()
    return True

  @events.event(events.CONNECT)
  def onConnect(self):
    if self._file_handle:
      self._file_handle.close()
    self._file_handle = open(self.options.log, 'w')
    self._moved = False
    self.send(self.options.username, escape=False)
    self.send(self.options.password, escape=False)
    self.send(
        'prompt p: <hp> <maxhp> <sp> <maxsp> <exp> <cash> <expl> <wgt> <last_exp> '
        '"<scan>" "<align>" <party><newline>')
    self.send('bl')
    self.send('save')
    return True

  @bot.trigger('Character SAVED. (crash recovery flag OK)', matcher=bot.SimpleMatcher)
  def sayHi(self, unused_match):
    self._moved = True

  @events.event(events.DISCONNECT)
  def onDisconnect(self):
    if self._file_handle:
      self._file_handle.close()
    self.engine.startTimer(
      'reconnect', 5.0, self.connection.connect, self.options.address,
      self.options.port)
    return True

  @bot.trigger(r'^A Huge Post office \(')
  def postOffice(self, unused_match):
    if self._moved:
      return
    paths = SHOPS.get(self.options.shop)
    if paths and 'post' in paths:
      self.send(paths['post'])

  @bot.trigger(r'^Entrance to the Great Temple \(')
  def churchEntrance(self, unused_match):
    if self._moved:
      return
    paths = SHOPS.get(self.options.shop)
    if paths and 'church' in paths:
      self.send(paths['church'])

  ALIGN = {
      'satanic': -6,
      'demonic': -5,
      'extremily evil': -4,
      'very evil': -3,
      'evil': -2,
      'slightly evil': -1,
      'neutral': 0,
      'slightly good': 1,
      'good': 1,
      'very good': 2,
      'extremly good': 3,
      'angelic': 4,
      'godly': 5,
      }

  def getAlign(self):
    align = self._prompt.get('align', '')
    return self.ALIGN.get(align.lower(), 0)

  @bot.trigger(r'^p: (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) "([^"]*)" "([^"]*)" (.*)$')
  def prompt(self, match):
    self._prompt = {
        'hp': match[1],
        'maxhp': match[2],
        'sp': match[3],
        'maxsp': match[4],
        'exp': match[5],
        'cash': match[6],
        'expl': match[7],
        'wgt': match[8],
        'last_exp': match[9],
        'scan': match[10],
        'align': match[11],
        'party': match[12],
        }

  @property
  def night(self):
    now = datetime.datetime.now(EET)
    return now.hour >= 23 or now.hour < 7

  @property
  def running(self):
    if not self._at_shop:
      return False
    if self._disable_till > time.time():
      return False
    #if not self.night:
      #return False
    return self._enabled

  SKILL = 'use'
  SPELL = 'cast'

  def add(self, action, sksp, target, present=True, force=False, insert=False):
    self.status('add(%r, %r, %r, present=%r, force=%r, insert=%r)' % (
        action, sksp, target, present, force, insert))
    target = target.lower()
    execute = (action, sksp, target, present)
    if not self.running:
      self.status('add: Aborting. Not running.')
      return
    if self._sksp and sksp not in self._sksp:
      self.status('add: Aborting. Do not have sksp.')
      return
    # Remove duplicates
    if execute == self._execute:
      self.status('add: Aborting. Already executing.')
      return
    if execute in self._queue:
      self.status('add: Aborting. Already in queue.')
      return
    if target == self.options.username or target == 'you':
      return
    if target in SNITCHES:
      self.status('add: Aborting. Snitch. Sleepy time.')
      self._disable_till = time.time() + 300
      return
    if target in IGNORE:
      self.status('add: Aborting. Ignored.')
      return
    if target in WIZARDS or 'test' in target:
      self.status('add: Aborting and disabling. Wizard.')
      self._enabled = False
      return
    if target != ME:
      if present and target not in self._present:
        self.addMissing(action, sksp, target)
        return
      if not present and target in self._present:
        self.status('add: Aborting. Target should not be present.')
        return
      if not force:
        now = time.time()
        requests = self._requests.setdefault(target, {}).setdefault(sksp, [])
        # Abort if 2 or more of the same requests in 3 min
        if len([r for r in requests if r > now - 180]) >= 2:
          self.status('add: Aborting. Too many similar requests.')
          return
        requests.append(now)
    if insert:
      self._queue.insert(0, execute)
    else:
      self._queue.append(execute)
    self.delayExecute()

  def remove(self, target, *sksps):
    if not self.running:
      return
    remove = []
    if not sksps:
      sksps = self._sksp
    for i, execute in enumerate(self._queue):
      if target != execute[2]:
        continue
      for sksp in sksps:
        if sksp == execute[1]:
          self.status('remove(%r, %r)' % (target, sksp))
          remove.append(i)
    for i in reversed(remove):
      self._queue.pop(i)
    self.removeMissing(target, *sksps)
    if not self._execute:
      return
    if target == self._execute[2] and self._execute[1] in sksps:
      self.status('remove: Stopping.')
      self.send('cast stop')

  def removeMissing(self, target, *sksps):
    if target not in self._missing:
      return
    remove = []
    for i, missing in enumerate(self._missing[target]):
      if missing[1] in sksps:
        self.status('removeMissing(%r, %r)' % (target, missing[1]))
        remove.append(i)
    for i in reversed(remove):
      self._missing[target].pop(i)

  def addMissing(self, action, sksp, target):
    self.status('addMissing(%r, %r, %r)' % (action, sksp, target))
    now = time.time()
    if target not in self._missing:
      self._missing[target] = []
    self._missing[target].append((action, sksp, now))

  def addSpell(self, spell, target, **kwargs):
    self.add(self.SPELL, spell, target, **kwargs)

  def addSkill(self, spell, target, **kwargs):
    self.add(self.SKILL, spell, target, **kwargs)

  def executeDelay(self):
    return min(60, max(2, 2 * math.sqrt(self.idle / 60)))

  def delayExecute(self):
    if not self._casting and not self.engine.isTimer('execute'):
      sleep = self.executeDelay()
      self.status('delayExecute: Executing in %ds.' % sleep)
      self.engine.startTimer('execute', sleep, self.execute)

  def capitalize(self, words):
    return ' '.join(map(str.capitalize, words.split()))

  def execute(self):
    if not self._queue:
      #self.status('execute: Abort. Queue empty.')
      return
    action, sksp, target, present = self._previous[target] = self._execute = self._queue.pop(0)
    self.status('execute() -> %s' % repr(self._execute))
    self._previous_time[target] = time.time()
    if target != ME:
      if present and target not in self._present:
        self.status('execute: Abort. Target should be present.')
        self.execute()
        return
      if not present and target in self._present:
        self.status('execute: Abort. Target should not be present.')
        self.execute()
        return
      self.send('alias _healing %s' % target)
      if self.options.announce and present:
        self.send(self.options.announce % {
            'action': action,
            'Action': self.capitalize(action),
            'sksp': sksp,
            'Sksp': self.capitalize(sksp),
            'target': target,
            'Target': self.capitalize(target),
            })
    self.send("%s '%s' %s" % (action, sksp, target))
    self._counts.setdefault(target, {}).setdefault(sksp, 0)
    self._counts[target][sksp] += 1

  def dump(self):
    vars = {
        '_enabled': self._enabled,
        '_prompt': self._prompt,
        '_counts': self._counts,
        }
    with open(self.options.save, 'w') as fh:
      pickle.dump(vars, fh)

  def load(self):
    if not os.path.isfile(self.options.save):
      return
    with open(self.options.save, 'r') as fh:
      vars = pickle.load(fh)
      for k, v in vars.iteritems():
        setattr(self, k, v)

  #@bot.trigger('^([A-Z][a-z]+) tells you \'(thanks|thnx|thank you)\'$')
  #def toldThanks(self, match):
    #self.engine.startTimer('thanks', 1.0, self.send, 'tell %s np' % match[1].lower())

  #@bot.trigger(COMMON_PRESENT, priority=-1)
  def wizards(self, match):
    player = match[1].lower()
    if player in WIZARDS or 'test' in player:
      self.status('wizards: Disabling. Wizard.')
      self._enabled = False

  @bot.trigger(COMMON_PRESENT + r'\b(another|again|more)\b')
  def repeatPrevious(self, match):
    player = match[1].lower()
    if player not in self._previous or player not in self._previous_time:
      return
    if self._previous_time[player] < time.time() - TIME_DELAY:
      self.status('repeatPrevious: Waited too long.')
      return
    self.add(*self._previous[player])

  @bot.trigger('You don\'t have enough spell points.', matcher=bot.SimpleMatcher)
  def noSpellPoints(self, unused_match):
    self.send('report')
    self._queue = []
    self._missing = {}

  #@bot.trigger('^You don\'t know any such (spell)\\.$')
  #@bot.trigger('^You don\'t know that (skill)\\.$')
  def missingSkSp(self, match):
    self.send('think Oops. Don\'t have that %s..' % match[1])

  @bot.trigger('You start chanting.', matcher=bot.SimpleMatcher)
  @bot.trigger('You start concentrating on the skill.', matcher=bot.SimpleMatcher)
  def startSkSp(self, unused_match):
    self._casting = True
    self._report = 0

  #@bot.trigger(r'^([A-Z][a-z]+( [a-z]+)*): (#+)$')
  def essenceEye(self, match):
    spell = match[1]
    rounds = len(match[3])
    if spell == 'Resurrect' and (rounds <= 4 and self._report == 0):
      self.send('think %s in %d round%s [DO NOT IDLE]' % (
          spell, rounds, '' if rounds == 1 else 's'))
      self._report += 1
    if spell == 'Reincarnation' and (
        (rounds <= 10 and self._report == 0) or (rounds <= 5 and self._report == 1)):
      self.send('think %s in %d round%s' % (
          spell, rounds, '' if rounds == 1 else 's'))
      self._report += 1

  @bot.trigger('Cast * at what?', matcher=bot.GlobMatcher)
  @bot.trigger('You are done with the chant.', matcher=bot.SimpleMatcher)
  @bot.trigger('Your movement prevents you from casting the spell.', matcher=bot.SimpleMatcher)
  @bot.trigger('You are prepared to do the skill.', matcher=bot.SimpleMatcher)
  @bot.trigger('Use * at who?', matcher=bot.GlobMatcher)
  @bot.trigger('Your movement breaks your skill attempt.', matcher=bot.SimpleMatcher)
  @bot.trigger('You stop casting the spell.', matcher=bot.SimpleMatcher)
  @bot.trigger('You stop your skill attempt.', matcher=bot.SimpleMatcher)
  @bot.trigger('Target is not present.', matcher=bot.SimpleMatcher)
  def doneSksp(self, unused_match):
    self._casting = False
    self._last = self._execute
    self._execute = None
    self.delayExecute()

  @bot.trigger(r"^The Tinker's Tool Shop \(")
  @bot.trigger(r'^Hall of Fame \(')
  @bot.trigger(r'^The jolly game booth of Billy Bob \(')
  @bot.trigger(r"^Akashia's Fine garments and Body Coverings \(")
  @bot.trigger(r'^The Magical Museum of Racial History \(')
  @bot.trigger(r"^Mimmi's candy store \(")
  @bot.trigger(r"^Janina's Bridal Boutique \(")
  def roomStart(self, unused_match):
    self._present = set()
    self._at_shop = True

  @bot.trigger(' \\(\x1b\\[1m[a-z]+\x1b\\[0m(,\x1b\\[1m[a-z]+\x1b\\[0m)*\\)\\.$', priority=-1, raw=True)
  def room(self, unused_match):
    self._at_shop = False

  @bot.trigger(COMMON + r'\b(stop)\b')
  def stop(self, match):
    player = match[1].lower()
    if not self._casting or not self._execute:
      return
    action, sksp, target, present = self._execute
    if player != target:
      return
    self.send('cast stop')
    self.send('think Stopped')

  def isValid(self, match):
    line = match[0].lower()
    player = match[1].lower()
    for present in self._present:
      if present == player:
        continue
      if re.search(r'\b(%s)\b' % present, line):
        return False
    return True

  @bot.trigger('\x1b\\[31m([A-Z][a-z]+)( [A-Z\'][a-z\']+)? the .*\x1b\\[2;37;0m', raw=True)
  @bot.trigger('\x1b\\[35mGhost of ([a-z]+)\x1b\\[2;37;0m', raw=True)
  def lookPlayers(self, match):
    self.arrives(match)

  @bot.trigger(r'^([A-Z][a-z]+) (arrives|floats in) ')
  @bot.trigger(r'^([A-Z][a-z]+) fades in\.$')
  @bot.trigger(r'^([A-Z][a-z]+) rises from the ground\.$')
  def arrives(self, match):
    player = match[1].lower()
    self._present.add(player)
    if player in self._missing:
      for action, sksp, when in self._missing[player]:
        if when < time.time() - TIME_DELAY:
          continue
        self.add(action, sksp, player, present=True)
      del self._missing[player]
    self.remove(player, 'summon ghost', 'summon')

  @bot.trigger(r'^([A-Z][a-z]+) disappears in ')
  @bot.trigger(r'^([A-Z][a-z]+) (leaves|floats) [a-z]+\.$')
  def leaves(self, match):
    player = match[1].lower()
    if player in self._present:
      self._present.remove(player)

  @bot.trigger(r'^([A-Z][a-z]+) looks sick\.$')
  @bot.trigger(COMMON + r'\b((rm|remove|cure) disease)\b')
  def spellCureDisease(self, match):
    self.addSpell('cure disease', match[1])

  @bot.trigger(r'^([A-Z][a-z]+) screams as (he|she|it) suffers from POISON!$')
  @bot.trigger(COMMON + r'\b((rm|remove|cure) poison|rp)\b')
  def spellRemovePoison(self, match):
    if not self.isValid(match):
      return
    self.addSpell('remove poison', match[1])

  @bot.trigger(COMMON + r'\b(cure blind(nes+)?)\b')
  def spellCureBlindness(self, match):
    if not self.isValid(match):
      return
    self.addSpell('cure blindness', match[1])

  #@bot.trigger('The poison resists.', matcher=bot.SimpleMatcher)

  @bot.trigger(GHOST_CHANNEL + r'\b(reinc|reincarnation)\b')
  @bot.trigger(GHOST_COMMON + r'\b(reinc|reincarnation)\b')
  def spellReincarnation(self, match):
    player = match[1].lower()
    if player not in self._present:
      self.spellSummonGhost(match)
    self.addSpell('reincarnation', player)

  def addTodo(self, action, sksp, target):
    self.status('addTodo(%r, %r, %r)' % (action, sksp, target))
    target = target.lower()
    if target not in self._todo:
      self._todo[target] = {}
    now = time.time()
    self._todo[target][sksp] = (action, now)

  def executeTodo(self, target, sksp):
    target = target.lower()
    if target not in self._todo:
      return
    if sksp not in self._todo[target]:
      return
    #self.status('executeTodo(%r, %r)' % (target, sksp))
    action, when = self._todo[target][sksp]
    if time.time() - 2 * TIME_DELAY < when:
      self.add(action, sksp, target)
    # Cleanup
    del self._todo[target][sksp]
    if not self._todo[target]:
      del self._todo[target]

  @bot.trigger(COMMON + r'\b(reinc|reincarnation)\b')
  def spellReincarnationAlive(self, match):
    self.addTodo(self.SPELL, 'reincarnation', match[1])

  @bot.trigger(r'^([A-Z][a-z]+) floats in ')
  def deadArrives(self, match):
    self.executeTodo(match[1], 'reincarnation')

  @bot.trigger(r'^([A-Z][a-z]+) is DEAD, R\.I\.P\.')
  def dead(self, match):
    self.remove(match[1].lower())
    self.executeTodo(match[1], 'reincarnation')

  @bot.trigger(GHOST_CHANNEL + r'\b(res+(urrect|or+|ing)?|med+i+cs?)\b')
  @bot.trigger(GHOST_COMMON + r'\b(res+(urrect|or+|ing)?|med+i+cs?)\b')
  def spellResurrect(self, match):
    for god in GODS:
      if god == self.options.god:
        continue
      if god in match[0].lower():
        return
    player = match[1].lower()
    if player not in self._present:
      self.spellSummonGhost(match)
    self.addSpell('resurrect', player)

  @bot.trigger(GHOST_CHANNEL + r'\b(g?sum+|summ+|sum+on|vine)\b', priority=-1)
  @bot.trigger(GHOST_COMMON + r'\b(g?sum+|summ+|sum+on|vine)\b', priority=-1)
  def spellSummonGhost(self, match):
    self.addSpell('summon ghost', match[1], present=False)

  @bot.trigger(r'^([A-Z][a-z]+) appears in a solid form\.$')
  def playerAlive(self, match):
    self.remove(match[1].lower(), 'summon ghost', 'reincarnation', 'resurrect')

  #@bot.trigger(r'^You throw ghost of ([a-z]+) a magical vine\.$')
  #def summonedGhost(self, match):
    #self.addSpell('resurrect', player)

  @bot.trigger(COMMON_DISTANT + r'\b(summ+|sum+on|vine)\b')
  def spellSummon(self, match):
    self.addSpell('summon', match[1], present=False)

  @bot.trigger(COMMON_DISTANT + r'\b(dheals?)\b')
  def spellMajorDistantHeal(self, match):
    self.addSpell('major distant heal', match[1], present=False)

  @bot.trigger(r'^([A-Z][a-z]+) already has been blessed by ([A-Z][a-z]+)\.$')
  def alreadyBlessed(self, match):
    self.send('sayto %s %s already blessed you.' % (match[1].lower(), match[2]))

  @bot.trigger(COMMON + r'\b(bless)\b')
  def skillBless(self, match):
    align = self.getAlign()
    if 'evil' in match[0].lower() and align >= 0:
      return
    if 'good' in match[0].lower() and align <= 0:
      return
    if not self.isValid(match):
      return
    self.addSkill('bless', match[1])

  @bot.trigger(r'^[A-Z][a-z]+ calls a blessing on ([A-Z][a-z]+)\.$')
  def removeBless(self, match):
    player = match[1].lower()
    self.remove(player, 'bless')

  @bot.trigger(r'^([A-Z][a-z]+) disappears in ')
  @bot.trigger(r'^([A-Z][a-z]+) (leaves|floats) [a-z]+\.$')
  def leaves(self, match):
    player = match[1].lower()
    if player in self._present:
      self._present.remove(player)

  @bot.trigger(r'^([A-Z][a-z]+) looks sick\.$')
  @bot.trigger(COMMON + r'\b((rm|remove|cure) disease)\b')
  def spellCureDisease(self, match):
    self.addSpell('cure disease', match[1])

  @bot.trigger(r'^([A-Z][a-z]+) screams as (he|she|it) suffers from POISON!$')
  @bot.trigger(COMMON + r'\b((rm|remove|cure) poison|rp)\b')
  def spellRemovePoison(self, match):
    if not self.isValid(match):
      return
    self.addSpell('remove poison', match[1])

  @bot.trigger(COMMON + r'\b(cure blind(nes+)?)\b')
  def spellCureBlindness(self, match):
    if not self.isValid(match):
      return
    self.addSpell('cure blindness', match[1])

  #@bot.trigger('The poison resists.', matcher=bot.SimpleMatcher)

  @bot.trigger(GHOST_CHANNEL + r'\b(reinc|reincarnation)\b')
  @bot.trigger(GHOST_COMMON + r'\b(reinc|reincarnation)\b')
  def spellReincarnation(self, match):
    player = match[1].lower()
    if player not in self._present:
      self.spellSummonGhost(match)
    self.addSpell('reincarnation', player)

  @bot.trigger(r'^([A-Z][a-z]+) disappears in a black cloud of smoke\.$')
  def removeReincarnation(self, match):
    player = match[1].lower()
    self.remove(player, 'reincarnation')

  def addTodo(self, action, sksp, target):
    self.status('addTodo(%r, %r, %r)' % (action, sksp, target))
    target = target.lower()
    if target not in self._todo:
      self._todo[target] = {}
    now = time.time()
    self._todo[target][sksp] = (action, now)

  def executeTodo(self, target, sksp):
    target = target.lower()
    if target not in self._todo:
      return
    if sksp not in self._todo[target]:
      return
    #self.status('executeTodo(%r, %r)' % (target, sksp))
    action, when = self._todo[target][sksp]
    if time.time() - TIME_DELAY < when:
      self.add(action, sksp, target)
    # Cleanup
    del self._todo[target][sksp]
    if not self._todo[target]:
      del self._todo[target]

  @bot.trigger(COMMON + r'\b(reinc|reincarnation)\b')
  def spellReincarnationAlive(self, match):
    self.addTodo(self.SPELL, 'reincarnation', match[1])

  @bot.trigger(r'^([A-Z][a-z]+) floats in ')
  def deadArrives(self, match):
    self.executeTodo(match[1], 'reincarnation')

  @bot.trigger(r'^([A-Z][a-z]+) is DEAD, R\.I\.P\.')
  def dead(self, match):
    self.remove(match[1].lower())
    self.executeTodo(match[1], 'reincarnation')

  @bot.trigger(GHOST_CHANNEL + r'\b(res+(urrect|or+|ing)?|med+i+cs?)\b')
  @bot.trigger(GHOST_COMMON + r'\b(res+(urrect|or+|ing)?|med+i+cs?)\b')
  def spellResurrect(self, match):
    for god in GODS:
      if god == self.options.god:
        continue
      if god in match[0].lower():
        return
    player = match[1].lower()
    if player not in self._present:
      self.spellSummonGhost(match)
    self.addSpell('resurrect', player)

  @bot.trigger(GHOST_CHANNEL + r'\b(g?sum+|summ+|sum+on|vine)\b', priority=-1)
  @bot.trigger(GHOST_COMMON + r'\b(g?sum+|summ+|sum+on|vine)\b', priority=-1)
  def spellSummonGhost(self, match):
    self.addSpell('summon ghost', match[1], present=False)

  @bot.trigger(r'^([A-Z][a-z]+) appears in a solid form\.$')
  def playerAlive(self, match):
    self.remove(match[1].lower(), 'summon ghost', 'reincarnation', 'resurrect')

  #@bot.trigger(r'^You throw ghost of ([a-z]+) a magical vine\.$')
  #def summonedGhost(self, match):
    #self.addSpell('resurrect', player)

  @bot.trigger(COMMON_DISTANT + r'\b(summ+|sum+on|vine)\b')
  def spellSummon(self, match):
    self.addSpell('summon', match[1], present=False)

  @bot.trigger(COMMON_DISTANT + r'\b(dheals?)\b')
  def spellMajorDistantHeal(self, match):
    self.addSpell('major distant heal', match[1], present=False)

  @bot.trigger(r'^([A-Z][a-z]+) already has been blessed by ([A-Z][a-z]+)\.$')
  def alreadyBlessed(self, match):
    self.send('sayto %s %s already blessed you.' % (match[1].lower(), match[2]))

  @bot.trigger(COMMON + r'\b(bless)\b')
  def skillBless(self, match):
    align = self.getAlign()
    if 'evil' in match[0].lower() and align >= 0:
      return
    if 'good' in match[0].lower() and align <= 0:
      return
    if not self.isValid(match):
      return
    self.addSkill('bless', match[1])

  @bot.trigger(r'^[A-Z][a-z]+ calls a blessing on ([A-Z][a-z]+)\.$')

  @bot.trigger(COMMON + r'\b(flight)\b')
  def spellFlight(self, match):
    if not self.isValid(match):
      return
    self.addSpell('flight', match[1])

  @bot.trigger(COMMON + r'\b(water walking|ww)\b')
  def spellWaterWalking(self, match):
    if not self.isValid(match):
      return
    self.addSpell('water walking', match[1])

  @bot.trigger(COMMON + r'\b((dispel|remove|rm) [kc]urse|qurp|ribbits|QURP)\b')
  def spellDispelCurse(self, match):
    if not self.isValid(match):
      return
    self.addSpell('dispel curse', match[1])

  @bot.trigger(COMMON + r'\b(sex change)\b')
  def spellSexChange(self, match):
    if not self.isValid(match):
      return
    self.addSpell('sex change', match[1])

  @bot.trigger(COMMON + r'\b(see magic)\b')
  def spellSeeMagic(self, match):
    if not self.isValid(match):
      return
    self.addSpell('see magic', match[1])

  @bot.trigger(COMMON + r'\b((rm|remove) scar|rscar)\b')
  def spellRemoveScar(self, match):
    if not self.isValid(match):
      return
    self.addSpell('remove scar', match[1])

  @bot.trigger(COMMON + r'\b(estimate worth|ews?)\b')
  def spellEstimateWorth(self, match):
    if not self.isValid(match):
      return
    self.addSpell('estimate worth', match[1])

  @bot.trigger(COMMON + r'\b(feast|food)\b')
  def spellFeast(self, match):
    if not self.isValid(match):
      return
    self.addSpell('feast', match[1])

  @bot.trigger(COMMON + r'\b(heal)\b')
  def spellHeal(self, match):
    if not self.isValid(match):
      return
    if 'half heal' in self._sksp:
      self.addSpell('half heal', match[1])
      return
    self.addSpell('heal', match[1])

  @bot.trigger('Your stomach is a hollow wound, begging to be filled.', matcher=bot.SimpleMatcher)
  def starving(self, match):
    self.addSpell('feast', ME, insert=True)

  @bot.trigger('You shiver and suffer as the POISON takes effect!', matcher=bot.SimpleMatcher)
  def poisoned(self, match):
    self.addSpell('remove poison', ME, insert=True)

  @bot.trigger('You die.', matcher=bot.SimpleMatcher)
  def youDie(self, match):
    self._enabled = False

  @bot.trigger('You fail miserably.', matcher=bot.SimpleMatcher)
  @bot.trigger('You fail the spell.', matcher=bot.SimpleMatcher)
  @bot.trigger('You have trouble concentrating and fail the spell.', matcher=bot.SimpleMatcher)
  @bot.trigger('You lose your balance and stumble, ruining the spell.', matcher=bot.SimpleMatcher)
  @bot.trigger('You lose your concentration and fail the spell.', matcher=bot.SimpleMatcher)
  @bot.trigger('You poke yourself in the eye and the spell misfires.', matcher=bot.SimpleMatcher)
  @bot.trigger('Your spell just fizzles.', matcher=bot.SimpleMatcher)
  @bot.trigger('Your spell just sputters.', matcher=bot.SimpleMatcher)
  @bot.trigger('You scream with frustration as the spell utterly fails.', matcher=bot.SimpleMatcher)
  @bot.trigger('You stumble over the spell\'s complexity and mumble the words.', matcher=bot.SimpleMatcher)
  @bot.trigger('You stutter the magic words and fail the spell.', matcher=bot.SimpleMatcher)
  @bot.trigger('You think of Leper and become too scared to cast your spell.', matcher=bot.SimpleMatcher)
  @bot.trigger('^[A-Z][a-z]+ completely resists the effects of your spell!$')
  def failSpell(self, unused_match):
    if not self._last:
      return
    self.add(*self._last, force=True, insert=True)

  @bot.trigger(r'^\[(.*)\] transfered \d+ gold\.$')
  def receivedTransfer(self, match):
    self.engine.startTimer('thanks', 1.5, self.send, 'tell %s ty!' % match[1].lower())

  #@bot.trigger('Autosave.', matcher=bot.SimpleMatcher)
  def autosave(self, unused_match):
    self.send('bl')


def defineFlags():
  parser = optparse.OptionParser(version='%prog v0.0', description=__doc__)
  # See: http://docs.python.org/library/optparse.html
  parser.add_option(
      '-v', '--verbosity',
      action='store',
      default=20,
      dest='verbosity',
      metavar='LEVEL',
      type='int',
      help='the logging verbosity')
  parser.add_option(
      '-l', '--log',
      action='store',
      default='clericbot.log',
      dest='log',
      metavar='FILE',
      type='str',
      help='path to log file')
  parser.add_option(
      '-f', '--config',
      action='store',
      default='configs/settings.cfg',
      dest='config',
      metavar='FILE',
      type='str',
      help='path to the config file')
  parser.add_option(
      '-s', '--save',
      action='store',
      default='clericbot.sav',
      dest='save',
      metavar='FILE',
      type='str',
      help='path to the cleric save file')
  parser.add_option(
      '-d', '--display',
      action='store_true',
      default=True,
      dest='display',
      help='display mud output to screen')
  return parser.parse_args()


def main(options, unused_args):
  try:
    cfg = config.readConfig(options.config)
  except AssertionError, e:
    logging.error('%s', e)
    return os.EX_DATAERR
  options.address = cfg.get('server', 'address')
  options.port = int(cfg.get('server', 'port'))
  options.username = cfg.get('character', 'name')
  options.password = cfg.get('character', 'password')
  options.god = cfg.get('character', 'god')
  options.shop = cfg.get('settings', 'shop')
  options.announce = cfg.get('settings', 'announce')
  sksp = set(s[0] for s in cfg.items('sksp') if s[1])

  inst = ClericBot(options, sksp=sksp)
  inst.start()
  return os.EX_OK


if __name__ == '__main__':
  opts, args = defineFlags()
  logging.basicConfig(
      level=opts.verbosity,
      datefmt='%Y/%m/%d %H:%M:%S',
      format='[%(asctime)s] %(levelname)s: %(message)s')
  sys.exit(main(opts, args))
