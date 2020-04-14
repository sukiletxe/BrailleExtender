# coding: utf-8
# configBE.py
# Part of BrailleExtender addon for NVDA
# Copyright 2016-2020 André-Abush CLAUSE, released under GPL.

from __future__ import unicode_literals
import os
import globalVars
from collections import OrderedDict

import addonHandler
addonHandler.initTranslation()
import braille
import config
import configobj
import inputCore
import languageHandler
from . import brailleTablesExt
from .common import *

Validator = configobj.validate.Validator

CHANNEL_stable = "stable"
CHANNEL_testing = "testing"
CHANNEL_dev = "dev"

CHOICE_none = "none"
CHOICE_braille = "braille"
CHOICE_speech = "speech"
CHOICE_speechAndBraille = "speechAndBraille"
CHOICE_dot7 = "dot7"
CHOICE_dot8 = "dot8"
CHOICE_dots78 = "dots78"
CHOICE_focus = "focus"
CHOICE_review = "review"
CHOICE_focusAndReview = "focusAndReview"
NOVIEWSAVED = chr(4)

# undefined char representations
CHOICE_tableBehaviour = 0
CHOICE_allDots8 = 1
CHOICE_allDots6 = 2
CHOICE_emptyCell = 3
CHOICE_otherDots = 4
CHOICE_questionMark = 5
CHOICE_otherSign = 6
CHOICE_liblouis = 7
CHOICE_HUC8 = 8
CHOICE_HUC6 = 9
CHOICE_hex = 10
CHOICE_dec = 11
CHOICE_oct = 12
CHOICE_bin = 13
CHOICES_undefinedCharRepr = [
	_("Use braille table behavior"),
	_("Dots 1-8 (⣿)"),
	_("Dots 1-6 (⠿)"),
	_("Empty cell (⠀)"),
	_("Other dot pattern (e.g.: 6-123456)"),
	_("Question mark (depending output table)"),
	_("Other sign/pattern (e.g.: \, ??)"),
	_("Hexadecimal, Liblouis style"),
	_("Hexadecimal, HUC8"),
	_("Hexadecimal, HUC6"),
	_("Hexadecimal"),
	_("Decimal"),
	_("Octal"),
	_("Binary")
]
outputMessage = dict([
	(CHOICE_none,             _("none")),
	(CHOICE_braille,          _("braille only")),
	(CHOICE_speech,           _("speech only")),
	(CHOICE_speechAndBraille, _("both"))
])

attributeChoices = dict([
	(CHOICE_none,   _("none")),
	(CHOICE_dots78, _("dots 7 and 8")),
	(CHOICE_dot7,   _("dot 7")),
	(CHOICE_dot8,   _("dot 8"))
])
attributeChoicesKeys = list(attributeChoices)
attributeChoicesValues = list(attributeChoices.values())

updateChannels = dict([
	(CHANNEL_stable,  _("stable")),
	(CHANNEL_dev,     _("development"))
])

focusOrReviewChoices = dict([
	(CHOICE_none,           _("none")),
	(CHOICE_focus,          _("focus mode")),
	(CHOICE_review,         _("review mode")),
	(CHOICE_focusAndReview, _("both"))
])

CHOICE_oneHandMethodSides = 0
CHOICE_oneHandMethodSide = 1
CHOICE_oneHandMethodDots = 2

CHOICE_oneHandMethods = dict([
	(CHOICE_oneHandMethodSides, _("Fill a cell in two stages on both sides")),
	(CHOICE_oneHandMethodSide, _("Fill a cell in two stages on one side (space = empty side)")),
	(CHOICE_oneHandMethodDots,  _("Fill a cell dots by dots (each dot is a toggle, press space to validate the character)"))
])
curBD = braille.handler.display.name
backupDisplaySize = braille.handler.displaySize
backupRoleLabels = {}
iniGestures = {}
iniProfile = {}
profileFileExists = gesturesFileExists = False

noMessageTimeout = True if 'noMessageTimeout' in config.conf["braille"] else False
outputTables = inputTables = None
preTables = []
postTables = []
if not os.path.exists(profilesDir): log.error('Profiles\' path not found')
else: log.debug('Profiles\' path (%s) found' % profilesDir)

def getValidBrailleDisplayPrefered():
	l = braille.getDisplayList()
	l.append(("last", _("last known")))
	return l

def getConfspec():
	global curBD
	curBD = braille.handler.display.name
	return {
		"autoCheckUpdate": "boolean(default=True)",
		"lastNVDAVersion": 'string(default="unknown")',
		"updateChannel": "option({CHANNEL_dev}, {CHANNEL_stable}, {CHANNEL_testing}, default={CHANNEL_stable})".format(
			CHOICE_none=CHOICE_none,
			CHANNEL_dev=CHANNEL_dev,
			CHANNEL_stable=CHANNEL_stable,
			CHANNEL_testing=CHANNEL_testing
		),
		"lastCheckUpdate": "float(min=0, default=0)",
		"profile_%s" % curBD: 'string(default="default")',
		"keyboardLayout_%s" % curBD: "string(default=\"?\")",
		"modifierKeysFeedback": "option({CHOICE_none}, {CHOICE_braille}, {CHOICE_speech}, {CHOICE_speechAndBraille}, default={CHOICE_braille})".format(
			CHOICE_none=CHOICE_none,
			CHOICE_braille=CHOICE_braille,
			CHOICE_speech=CHOICE_speech,
			CHOICE_speechAndBraille=CHOICE_speechAndBraille
		),
		"beepsModifiers": "boolean(default=False)",
		"volumeChangeFeedback": "option({CHOICE_none}, {CHOICE_braille}, {CHOICE_speech}, {CHOICE_speechAndBraille}, default={CHOICE_braille})".format(
			CHOICE_none=CHOICE_none,
			CHOICE_braille=CHOICE_braille,
			CHOICE_speech=CHOICE_speech,
			CHOICE_speechAndBraille=CHOICE_speechAndBraille
		),
		"brailleDisplay1": 'string(default="last")',
		"brailleDisplay2": 'string(default="last")',
		"hourDynamic": "boolean(default=True)",
		"leftMarginCells_%s" % curBD: "integer(min=0, default=0, max=80)",
		"rightMarginCells_%s" % curBD: "integer(min=0, default=0, max=80)",
		"reverseScrollBtns": "boolean(default=False)",
		"autoScrollDelay_%s" % curBD: "integer(min=125, default=3000, max=42000)",
		"smartDelayScroll": "boolean(default=False)",
		"ignoreBlankLineScroll": "boolean(default=True)",
		"speakScroll": "option({CHOICE_none}, {CHOICE_focus}, {CHOICE_review}, {CHOICE_focusAndReview}, default={CHOICE_focusAndReview})".format(
			CHOICE_none=CHOICE_none,
			CHOICE_focus=CHOICE_focus,
			CHOICE_review=CHOICE_review,
			CHOICE_focusAndReview=CHOICE_focusAndReview
		),
		"stopSpeechScroll": "boolean(default=False)",
		"stopSpeechUnknown": "boolean(default=True)",
		"speakRoutingTo": "boolean(default=True)",
		"routingReviewModeWithCursorKeys": "boolean(default=False)",
		"tabSpace": "boolean(default=False)",
		f"tabSize_{curBD}": "integer(min=1, default=2, max=42)",
		"undefinedCharsRepr": {
			"method": "integer(min=0, default=%s, max=%s)" % (CHOICE_HUC8, CHOICE_bin),
			"hardSignPatternValue": "string(default=??)",
			"hardDotPatternValue": "string(default=6-12345678)",
			"desc": "boolean(default=True)",
			"extendedDesc": "boolean(default=True)",
			"start": "string(default=[)",
			"end": "string(default=])",
			"lang": "string(default=Windows)",
			"table": "string(default=current)"
		},
		"viewSaved": "string(default=%s)" % NOVIEWSAVED,
		"reviewModeTerminal": "boolean(default=True)",
		"oneHandMode": "boolean(default=False)",
		"oneHandMethod": "integer(min=0, max=%d, default=%d)" % (CHOICE_oneHandMethodDots, CHOICE_oneHandMethodSides),
		"features": {
			"attributes": "boolean(default=True)",
			"roleLabels": "boolean(default=True)"
		},
		"attributes": {
			"bold": "option({CHOICE_none}, {CHOICE_dot7}, {CHOICE_dot8}, {CHOICE_dots78}, default={CHOICE_dots78})".format(
				CHOICE_none=CHOICE_none,
				CHOICE_dot7=CHOICE_dot7,
				CHOICE_dot8=CHOICE_dot8,
				CHOICE_dots78=CHOICE_dots78
			),
			"italic": "option({CHOICE_none}, {CHOICE_dot7}, {CHOICE_dot8}, {CHOICE_dots78}, default={CHOICE_none})".format(
				CHOICE_none=CHOICE_none,
				CHOICE_dot7=CHOICE_dot7,
				CHOICE_dot8=CHOICE_dot8,
				CHOICE_dots78=CHOICE_dots78
			),
			"underline": "option({CHOICE_none}, {CHOICE_dot7}, {CHOICE_dot8}, {CHOICE_dots78}, default={CHOICE_none})".format(
				CHOICE_none=CHOICE_none,
				CHOICE_dot7=CHOICE_dot7,
				CHOICE_dot8=CHOICE_dot8,
				CHOICE_dots78=CHOICE_dots78
			),
			"strikethrough": "option({CHOICE_none}, {CHOICE_dot7}, {CHOICE_dot8}, {CHOICE_dots78}, default={CHOICE_none})".format(
				CHOICE_none=CHOICE_none,
				CHOICE_dot7=CHOICE_dot7,
				CHOICE_dot8=CHOICE_dot8,
				CHOICE_dots78=CHOICE_dots78
			),
			"text-position:sub": "option({CHOICE_none}, {CHOICE_dot7}, {CHOICE_dot8}, {CHOICE_dots78}, default={CHOICE_none})".format(
				CHOICE_none=CHOICE_none,
				CHOICE_dot7=CHOICE_dot7,
				CHOICE_dot8=CHOICE_dot8,
				CHOICE_dots78=CHOICE_dots78
			),
			"text-position:super": "option({CHOICE_none}, {CHOICE_dot7}, {CHOICE_dot8}, {CHOICE_dots78}, default={CHOICE_none})".format(
				CHOICE_none=CHOICE_none,
				CHOICE_dot7=CHOICE_dot7,
				CHOICE_dot8=CHOICE_dot8,
				CHOICE_dots78=CHOICE_dots78
			),
			"invalid-spelling": "option({CHOICE_none}, {CHOICE_dot7}, {CHOICE_dot8}, {CHOICE_dots78}, default={CHOICE_dots78})".format(
				CHOICE_none=CHOICE_none,
				CHOICE_dot7=CHOICE_dot7,
				CHOICE_dot8=CHOICE_dot8,
				CHOICE_dots78=CHOICE_dots78
			)
		},
		"quickLaunches": {},
		"roleLabels": {},
		"tables": {
			"groups": {},
			"shortcuts": 'string(default="?")',
			"preferedInput": f'string(default="{config.conf["braille"]["inputTable"]}|unicode-braille.utb")',
			"preferedOutput": f'string(default="{config.conf["braille"]["translationTable"]}")',
		},
		"advancedInputMode": {
			"stopAfterOneChar": "boolean(default=True)",
			"escapeSignUnicodeValue": "string(default=⠼)",
		}
	}

def getLabelFromID(idCategory, idLabel):
	if idCategory == 0: return braille.roleLabels[int(idLabel)]
	elif idCategory == 1: return braille.landmarkLabels[idLabel]
	elif idCategory == 2: return braille.positiveStateLabels[int(idLabel)]
	elif idCategory == 3: return braille.negativeStateLabels[int(idLabel)]

def setLabelFromID(idCategory, idLabel, newLabel):
	if idCategory == 0: braille.roleLabels[int(idLabel)] = newLabel
	elif idCategory == 1: braille.landmarkLabels[idLabel] = newLabel
	elif idCategory == 2: braille.positiveStateLabels[int(idLabel)] = newLabel
	elif idCategory == 3: braille.negativeStateLabels[int(idLabel)] = newLabel

def loadRoleLabels(roleLabels):
	global backupRoleLabels
	for k, v in roleLabels.items():
		try:
			arg1 = int(k.split(':')[0])
			arg2 = k.split(':')[1]
			backupRoleLabels[k] = (v, getLabelFromID(arg1, arg2))
			setLabelFromID(arg1, arg2, v)
		except BaseException as err:
			log.error("Error during loading role label `%s` (%s)" % (k, err))
			roleLabels.pop(k)
			config.conf["brailleExtender"]["roleLabels"] = roleLabels

def discardRoleLabels():
	global backupRoleLabels
	for k, v in backupRoleLabels.items():
		arg1 = int(k.split(':')[0])
		arg2 = k.split(':')[1]
		setLabelFromID(arg1, arg2, v[1])
	backupRoleLabels = {}

def loadConf():
	global curBD, gesturesFileExists, profileFileExists, iniProfile
	curBD = braille.handler.display.name
	try: brlextConf = config.conf["brailleExtender"].copy()
	except configobj.validate.VdtValueError:
		config.conf["brailleExtender"]["updateChannel"] = "dev"
		brlextConf = config.conf["brailleExtender"].copy()
	if "profile_%s" % curBD not in brlextConf.keys():
		config.conf["brailleExtender"]["profile_%s" % curBD] = "default"
	if "tabSize_%s" % curBD not in brlextConf.keys():
		config.conf["brailleExtender"]["tabSize_%s" % curBD] = 2
	if "leftMarginCells__%s" % curBD not in brlextConf.keys():
		config.conf["brailleExtender"]["leftMarginCells_%s" % curBD] = 0
	if "rightMarginCells_%s" % curBD not in brlextConf.keys():
		config.conf["brailleExtender"]["rightMarginCells_%s" % curBD] = 0
	if "autoScrollDelay_%s" % curBD not in brlextConf.keys():
		config.conf["brailleExtender"]["autoScrollDelay_%s" % curBD] = 3000
	if "keyboardLayout_%s" % curBD not in brlextConf.keys():
		config.conf["brailleExtender"]["keyboardLayout_%s" % curBD] = "?"
	confGen = (r"%s\%s\%s\profile.ini" % (profilesDir, curBD, config.conf["brailleExtender"]["profile_%s" % curBD]))
	if (curBD != "noBraille" and os.path.exists(confGen)):
		profileFileExists = True
		confspec = config.ConfigObj("", encoding="UTF-8", list_values=False)
		iniProfile = config.ConfigObj(confGen, configspec=confspec, indent_type="\t", encoding="UTF-8")
		result = iniProfile.validate(Validator())
		if result is not True:
			log.exception("Malformed configuration file")
			return False
	else:
		if curBD != "noBraille": log.warn("%s inaccessible" % confGen)
		else: log.debug("No braille display present")

	limitCellsRight = int(config.conf["brailleExtender"]["rightMarginCells_%s" % curBD])
	if (backupDisplaySize-limitCellsRight <= backupDisplaySize and limitCellsRight > 0):
		braille.handler.displaySize = backupDisplaySize-limitCellsRight
	if config.conf["brailleExtender"]["tables"]["shortcuts"] not in brailleTablesExt.listTablesFileName(brailleTablesExt.listUncontractedTables()): config.conf["brailleExtender"]["tables"]["shortcuts"] = '?'
	if config.conf["brailleExtender"]["features"]["roleLabels"]:
		loadRoleLabels(config.conf["brailleExtender"]["roleLabels"].copy())
	initializePreferedTables()
	return True

def initializePreferedTables():
	global inputTables, outputTables
	inputTables, outputTables = brailleTablesExt.getPreferedTables()

def loadGestures():
	if gesturesFileExists:
		if os.path.exists(os.path.join(profilesDir, "_BrowseMode", config.conf["braille"]["inputTable"] + ".ini")): GLng = config.conf["braille"]["inputTable"]
		else: GLng = 'en-us-comp8.utb'
		gesturesBMPath = os.path.join(profilesDir, "_BrowseMode", "common.ini")
		gesturesLangBMPath = os.path.join(profilesDir, "_BrowseMode/", GLng + ".ini")
		inputCore.manager.localeGestureMap.load(gesturesBDPath())
		for fn in [gesturesBMPath, gesturesLangBMPath]:
			f = open(fn)
			tmp = [line.strip().replace(' ', '').replace('$', iniProfile["general"]["nameBK"]).replace('=', '=br(%s):' % curBD) for line in f if line.strip() and not line.strip().startswith('#') and line.count('=') == 1]
			tmp = {k.split('=')[0]: k.split('=')[1] for k in tmp}
		inputCore.manager.localeGestureMap.update({'browseMode.BrowseModeTreeInterceptor': tmp})

def gesturesBDPath(a = False):
	l = ['\\'.join([profilesDir, curBD, config.conf["brailleExtender"]["profile_%s" % curBD], "gestures.ini"]),
	'\\'.join([profilesDir, curBD, "default", "gestures.ini"])]
	if a: return "; ".join(l)
	for p in l:
		if os.path.exists(p): return p
	return '?'

def initGestures():
	global gesturesFileExists, iniGestures
	if profileFileExists and gesturesBDPath() != '?':
		log.debug('Main gestures map found')
		confGen = gesturesBDPath()
		confspec = config.ConfigObj("", encoding="UTF-8", list_values=False)
		iniGestures = config.ConfigObj(confGen, configspec=confspec, indent_type="\t", encoding="UTF-8")
		result = iniGestures.validate(Validator())
		if result is not True:
			log.exception("Malformed configuration file")
			gesturesFileExists = False
		else: gesturesFileExists = True
	else:
		if curBD != "noBraille": log.warn('No main gestures map (%s) found' % gesturesBDPath(1))
		gesturesFileExists = False
	if gesturesFileExists:
		for g in iniGestures["globalCommands.GlobalCommands"]:
			if isinstance(
					iniGestures["globalCommands.GlobalCommands"][g],
					list):
				for h in range(
						len(iniGestures["globalCommands.GlobalCommands"][g])):
					iniGestures[inputCore.normalizeGestureIdentifier(
						str(iniGestures["globalCommands.GlobalCommands"][g][h]))] = g
			elif ('kb:' in g and g not in ["kb:alt', 'kb:control', 'kb:windows', 'kb:control', 'kb:applications"] and 'br(' + curBD + '):' in str(iniGestures["globalCommands.GlobalCommands"][g])):
				iniGestures[inputCore.normalizeGestureIdentifier(str(
					iniGestures["globalCommands.GlobalCommands"][g])).replace('br(' + curBD + '):', '')] = g
	return gesturesFileExists, iniGestures


def getKeyboardLayout():
	if (config.conf["brailleExtender"]["keyboardLayout_%s" % curBD] is not None
	and config.conf["brailleExtender"]["keyboardLayout_%s" % curBD] in iniProfile['keyboardLayouts'].keys()):
		return iniProfile['keyboardLayouts'].keys().index(config.conf["brailleExtender"]["keyboardLayout_%s" % curBD])
	else: return 0

def getTabSize():
	size = config.conf["brailleExtender"]["tabSize_%s" % curBD]
	if size < 0: size = 2
	return size
# remove old config files
cfgFile = globalVars.appArgs.configPath + r"\BrailleExtender.conf"
cfgFileAttribra = globalVars.appArgs.configPath + r"\attribra-BE.ini"
if os.path.exists(cfgFile): os.remove(cfgFile)
if os.path.exists(cfgFileAttribra): os.remove(cfgFileAttribra)

if not os.path.exists(configDir): os.mkdir(configDir)
if not os.path.exists(os.path.join(configDir, "brailleDicts")): os.mkdir(os.path.join(configDir, "brailleDicts"))
