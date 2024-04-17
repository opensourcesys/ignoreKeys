# Ignore special keys
# Originally a private add-on by Tyler Spivey <tspivey@pcdesk.net>, on behalf of Sarah k Alawami <marrie12@gmail.com>
# With a subsequent rewrite and expansion by Luke Davis <XLTechie@newanswertech.com>.
# Copyright (c) 2023-2024, Sarah k Alawami, Luke Davis, all rights reserved.

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
from globalCommands import SCRCAT_TOOLS


addonHandler.initTranslation()
globalPluginPointer: Optional[globalPluginHandler.GlobalPlugin] = None

config.conf.spec["ignoreSpecialKeys"] = {
	"resetSelectedLockKeys": "boolean(default=True)",
	"keyGroup": "integer(default=0)",
}

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.patched = False
		global globalPluginPointer
		globalPluginPointer = self

	def patch(self):
		if self.patched:
			return
		else:
			self.old_fn = keyboardHandler.internal_keyDownEvent
			keyboardHandler.internal_keyDownEvent = internal_keyDownEvent
			winInputHook.keyDownCallback = internal_keyDownEvent
			self.patched = True
			tones.beep(1000, 100)

	def unpatch(self, shouldBeep: bool = True):
		if self.patched:
			keyboardHandler.internal_keyDownEvent = self.old_fn
			winInputHook.keyDownCallback = self.old_fn
			self.patched = False
			if shouldBeep:
				tones.beep(700, 100)

	def terminate(self):
		self.unpatch(False)

	@script(
		description="Toggle to keep NVDA from intercepting foot pedal keys. Press again to restore normal keyboard.",
		gesture="kb:NVDA+shift+f8",
		category=SCRCAT_TOOLS
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
		return globalPluginPointer.old_fn(vkCode, scanCode, extended, injected)
