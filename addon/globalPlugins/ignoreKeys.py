# Ignore Keys
# Originally a private add-on by Tyler Spivey <tspivey@pcdesk.net>, on behalf of Sarah k Alawami <marrie12@gmail.com>
# With a subsequent rewrite and expansion by Luke Davis <XLTechie@newanswertech.com>.
# Copyright (c) 2023-2024, Sarah k Alawami, Luke Davis, all rights reserved.

import weakref
from enum import IntFlag, auto
from typing import Optional

import config
import gui
import ui
import addonHandler
import globalPluginHandler
import keyboardHandler
import tones
import winUser
import winInputHook
from scriptHandler import script
from logHandler import log

try:
	addonHandler.initTranslation()
except addonHandler.AddonError:
	log.error(
		"Attempted to initialize translations in an inappropriate context. May be running from scratchpad."
	)

# Configure the Input Gestures category
try:
	ADDON_SUMMARY = addonHandler.getCodeAddon().manifest["summary"]
except Exception:
	ADDON_SUMMARY = "Ignore Keys"  # Static assignment for emergencies (e.g. scratchpad use)

pluginRef: Optional[weakref.ref[globalPluginHandler.GlobalPlugin]] = None
"""
Allows us a shorthand module level reference to the GlobalPlugin object once defined.
"""

config.conf.spec["ignoreSpecialKeys"] = {
	"keyGroup": "integer(default=0)",
	"restoreLockKeys": "boolean(default=True)",
	"startInIgnoreMode": "boolean(default=False)",
}


class IgnoreKeysSettings (gui.settingsDialogs.SettingsPanel):
	"""NVDA configuration panel based configurator  for Ignore Keys."""

	# Translators: Label for the Ignore Keys settings category in NVDA Settings panel.
	title: str = _("Ignore Keys")

	def makeSettings(self, settingsSizer):
		"""Creates a settings panel."""
		helper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		self.startInIgnoreModeCB = helper.addItem(
			wx.CheckBox(
				self,
				# Translators: The label for a checkbox in Ignore Keys settings panel
				label=_("Start ignoring the selected keys as soon as NVDA launches")
			)
		)
		self.startInIgnoreModeCB.SetValue(config.conf["ignoreKeys"]["startInIgnoreMode"])
		self.restoreLockKeysCB = helper.addItem(
			wx.CheckBox(
				self,
				# Translators: The label for a checkbox in Ignore Keys settings panel
				label=_("Restore any selected lock keys to their original state when turning off ignore")
			)
		)
		self.restoreLockKeysCB.SetValue(
			config.conf["ignoreKeys"]["restoreLockKeys"]
		)

	def onSave(self):
		config.conf["ignoreKeys"]["startInIgnoreMode"] = self.startInIgnoreModeCB.Value
		config.conf["ignoreKeys"]["restoreLockKeys"] = self.restoreLockKeysCB.Value


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.patched: bool = False
		global pluginRef
		pluginRef = weakref.ref(self)

	def patch(self):
		if self.patched:
			return
		else:
			self.old_fn = keyboardHandler.internal_keyDownEvent
			keyboardHandler.internal_keyDownEvent = internal_keyDownEvent
			winInputHook.keyDownCallback = internal_keyDownEvent
			self.patched = True
			tones.beep(2000, 100)

	def unpatch(self, shouldBeep: bool = True):
		if self.patched:
			keyboardHandler.internal_keyDownEvent = self.old_fn
			winInputHook.keyDownCallback = self.old_fn
			self.patched = False
			if shouldBeep:
				tones.beep(1000, 100)

	def terminate(self):
		self.unpatch(False)

	@script(
		# Translators: A description of the input gesture for Input Help.
		description=_("Toggle to keep NVDA from intercepting the configured keys to be ignored. Press again to restore normal behavior."),
		gesture="kb:NVDA+f8",
		category=ADDON_SUMMARY
	)
	def script_patch(self, gesture):
		if self.patched:
			self.unpatch()
		else:
			self.patch()

def internal_keyDownEvent(vkCode, scanCode, extended, injected):
	if (
		vkCode == winUser.VK_PAUSE
		or vkCode == winUser.VK_CANCEL
		or vkCode == winUser.VK_SCROLL
	):
		return True
	else:
		return pluginRef.old_fn(vkCode, scanCode, extended, injected)
