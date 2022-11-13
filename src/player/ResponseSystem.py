"""ResponseSystem module: contains the ResponseSystem class."""

import random

from direct.directnotify.DirectNotifyGlobal import directNotify

def exactOrRandomRange(data):
    if isinstance(data, (tuple, list)):
        return random.uniform(data[0], data[1])
    else:
        return data

class ResponseLine:

    def __init__(self, line, delay=-1, preDelay=0.0, respeakDelay=0.0, speakOnce=False):
        # Delay after line is spoken until the character
        # can speak again.
        if delay == -1:
            self.postDelay = 1.0#(2.8, 3.5)
        else:
            self.postDelay = delay
        # Delay before line is actually spoken when this line
        # is chosen.
        self.preDelay = preDelay
        self.respeakDelay = respeakDelay
        self.speakOnce = speakOnce
        self.line = line

        self.speakCount = 0

    def reset(self):
        self.speakCount = 0

    def canSpeak(self, system, response):
        if self.speakOnce and self.speakCount > 0:
            return False

class Response:

    def __init__(self, lines=[], sequential=False, permitRepeats=False, noRepeat=False):
        self.lines = lines
        self.availableLines = []
        self.currIndex = 0
        self.enabled = True
        self.sequential = sequential
        self.permitRepeats = permitRepeats
        self.noRepeat = noRepeat

    def reset(self):
        self.availableLines = []
        self.enabled = True
        self.currIndex = 0
        for line in self.lines:
            line.reset()

    def getLine(self, system):
        if not self.enabled:
            return None

        if not self.availableLines:
            self.availableLines = list(self.lines)

        line = random.choice(self.availableLines)
        self.availableLines.remove(line)

        system.speakTime = globalClock.frame_time + exactOrRandomRange(line.preDelay)
        system.nextSpeakTime = globalClock.frame_time + exactOrRandomRange(line.postDelay)

        return line.line

class Rule:

    def __init__(self, criteria=[], responses=[], addMemory=[], removeMemory=[]):
        self.criteria = criteria
        self.responses = responses
        self.addMemory = addMemory
        self.removeMemory = removeMemory

    def reset(self):
        for resp in self.responses:
            resp.reset()

    def getResponse(self, system):
        if not self.responses:
            return None

        resp = random.choice(self.responses)
        return resp.getLine(system)

class ResponseSystem:

    notify = directNotify.newCategory("ResponseSystem")
    #notify.setDebug(True)

    def __init__(self, player):
        self.notify.setDebug(True)

        self.player = player

        self.memory = {}

        # Rules within a concept are sorted by decreasing number
        # of criteria.
        self.rulesByConcept = {}

        # The last time we spoke a line of dialogue.
        self.lastSpeakTime = 0.0

        self.speakTime = 0.0
        self.nextSpeakTime = 0.0

    def cleanup(self):
        self.player = None
        self.rulesByConcept = None

    def reset(self):
        self.lastSpeakTime = 0.0
        for rule in self.rulesByConcept.values():
            rule.reset()

    def addRule(self, concept, rule):
        if not concept in self.rulesByConcept:
            self.rulesByConcept[concept] = [rule]
        else:
            self.rulesByConcept[concept].append(rule)

    def sortRules(self):
        for concept in self.rulesByConcept.keys():
            self.rulesByConcept[concept].sort(key=lambda x: len(x.criteria), reverse=True)

    def updateMemory(self):
        for name, data in list(self.memory.items()):
            if data['expireTime'] > 0 and globalClock.frame_time >= data['expireTime']:
                del self.memory[name]

    def addMemory(self, name, value, expireTime=-1):
        if expireTime != -1:
            expireTime = globalClock.frame_time + expireTime
        self.memory[name] = {'value': value, 'expireTime': expireTime}

    def clearMemory(self, name):
        if name in self.memory:
            del self.memory[name]

    def speakConcept(self, data):
        concept = data['concept']

        if globalClock.frame_time < self.nextSpeakTime:
            self.notify.debug("Not time to speak yet")
            return None

        rules = self.rulesByConcept.get(concept)
        if not rules:
            self.notify.debug("No rules under concept " + str(concept))
            return None

        self.updateMemory()
        # Append memory to data table.
        for memName, memData in self.memory.items():
            data[memName] = memData['value']

        self.notify.debug("Speak concept " + str(concept) + " with data " + repr(data))

        highestMatchingScore = 0
        matchingRules = []

        for rule in rules:

            allMatch = True

            for criterion in rule.criteria:
                if not criterion(data):
                    allMatch = False
                    break

            if not allMatch:
                continue

            score = len(rule.criteria)

            if score >= highestMatchingScore:
                highestMatchingScore = score
                matchingRules.append(rule)

        if not matchingRules:
            self.notify.debug("No matching rule")
            return None

        if len(matchingRules) == 1:
            rule = matchingRules[0]
        else:
            rule = random.choice(matchingRules)

        # We have the best rule for this concept and current set of
        # criteria.  Attempt to speak a line from the response for
        # this rule.

        for mem in rule.addMemory:
            self.addMemory(mem['name'], mem['value'], mem.get('expireTime', -1))
        for mem in rule.removeMemory:
            self.clearMemory(mem['name'])

        line = rule.getResponse(self)
        if line:
            self.notify.debug("Speaking line " + line)
        return line






