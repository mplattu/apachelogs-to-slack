#!/usr/bin/env python3

import fileinput
import hashlib
import json
import os
import re
import requests

from typing import List

SETTINGS = os.path.dirname(os.path.abspath(__file__)) + '/apachelogs-to-slack.json'

class Settings:
    def __init__(self, settingsFilePath):
        self.settings = {}
        with open(settingsFilePath, 'r') as file:
            self.settings = json.load(file)

    def getSettings(self):
        return self.settings

class HashStorage:
    def __init__(self, hashFilePath):
        self.hashFilePath = hashFilePath
        self.hash = None
    
    def readHash(self) -> str:
        try:
            with open(self.hashFilePath, 'r', encoding='utf-8') as file:
                content = file.read()
        except FileNotFoundError:
            return None
        
        return content

    def writeHash(self, hash: str):
        with open(self.hashFilePath, 'w', encoding='utf-8') as file:
            file.write(hash)

class LogChecker:
    def __init__(self, settings: object):
        self.settings = settings
        self.warnings = []
        self.lastProcessedHashFromPreviousSession = None
        self.lastProcessedLogLineHash = None
        
        self.hashStorage = HashStorage(self.settings['hashFile'])

    def processLine (self, lineToParse: str) -> List[str]:
        apacheCombinedRe = r'^([(\d\.)]+) [^ ]* [^ ]* \[([^ ]* [^ ]*)\] "([^"]*)" (\d+) [^ ]* "([^"]*)" "([^"]*)"'
        return re.match(apacheCombinedRe, lineToParse).groups()

    def messageFormatter(self, message:str, logArray: List[str]) -> str:
        for index in range(len(logArray)):
            indexRegex = re.compile("#"+str(index))
            message = re.sub(indexRegex, logArray[index], message)
        
        return message

    def calculateHash(self, logLine: str) -> str:
        if logLine is None:
            return None

        hash = hashlib.sha256()
        hash.update(logLine.encode('utf-8'))

        return hash.hexdigest()

    def addLogLine(self, logLine: str):
        if self.lastProcessedHashFromPreviousSession is None:
            self.lastProcessedHashFromPreviousSession = self.hashStorage.readHash()

        self.lastProcessedLogLineHash = self.calculateHash(logLine)

        logArray = self.processLine(logLine)

        rules = self.settings['rules']

        for rule in rules:
            if rule['field'] > 0:
                ruleRegex = re.compile(rule['regex'])
                if re.match(ruleRegex, logArray[rule['field']]):
                    self.warnings.append(self.messageFormatter(rule['message'], logArray))
            else:
                if re.match(ruleRegex, logLine):
                    self.warnings.append(self.messageFormatter(rule['message'], logArray))

        if self.lastProcessedHashFromPreviousSession == self.lastProcessedLogLineHash:
            self.warnings = []

    def getWarnings (self) -> List[str]:
        self.hashStorage.writeHash(self.lastProcessedLogLineHash)
        return self.warnings
    
    def getLastLogLineHash (self) -> str:
        return self.lastProcessedLogLineHash

class SlackNotifier:
    def __init__(self, settings):
        self.settings = settings
    
    def notify(self, messages: List[str]):
        for message in messages:
            payload = {'text': message}
            response = requests.post(self.settings['slackWebHookUrl'], json=payload)
            if response.status_code != 200:
                print(f"Slack returns status code {response.status_code}")

settings = Settings(SETTINGS)
logChecker = LogChecker(settings.getSettings())

for logLine in fileinput.input():
    logChecker.addLogLine(logLine)

print(logChecker.getWarnings())

slackNotifier = SlackNotifier(settings.getSettings())
slackNotifier.notify(logChecker.getWarnings())
