import wx
import appModuleHandler
import speech
import config
import ui
import api
import eventHandler
import controlTypes
import mouseHandler
import winUser
from NVDAObjects import NVDAObjectTextInfo
from versionInfo import version_year
from scriptHandler import script
from nvwave import playWaveFile
from os.path import join, dirname
role = controlTypes.Role if version_year>=2022 else controlTypes.role.Role

class AppModule(appModuleHandler.AppModule):
	ReportOCRResultTimer=None
	OCRResult=None
	SOUND_LINK = join(dirname(__file__), "link.wav")

	SOUND_POPUP = join(dirname(__file__), "popup.wav")
	confspec = {
	"isAutoMSG": "boolean(default=False)"
	}
	config.conf.spec["WeChatEnhancement"] = confspec
	isAutoMSG = config.conf["WeChatEnhancement"]["isAutoMSG"]

	def event_NVDAObject_init(self, obj):
		if role.EDITABLETEXT != obj.role:
			obj.displayText = obj.name
			obj.TextInfo = NVDAObjectTextInfo

	def event_nameChange(self, obj, nextHandler):
		try:
			if obj.role==role.LISTITEM and obj.parent.name=="消息" and obj.simpleFirstChild:
				playWaveFile(self.SOUND_POPUP)
				if self.isAutoMSG:
					if obj.name==None:
						children = obj.recursiveDescendants
						for child in children:
							if not speech.isBlank(child.name): ui.message(child.name)
					elif obj.simpleFirstChild.role==role.BUTTON:
						ui.message("%s %s" % (obj.simpleFirstChild.name, obj.name))
		except: pass
		nextHandler()

	def event_gainFocus(self, obj, nextHandler, isFocus=False):
		# 读出被转发的消息
		try:
			if obj.name==None:
				if obj.role==role.LISTITEM:
					children = obj.recursiveDescendants
					for child in children:
						if not speech.isBlank(child.name): ui.message(child.name)
					return
		except AttributeError: pass
		# 消息列表中特殊消息音效提醒
		try:
			if obj.role==role.LISTITEM and obj.parent.name=="消息":
				if obj.value != None:
					playWaveFile(self.SOUND_LINK)
		except AttributeError: pass
		# 群组中成员昵称的报告方式
		try:
			if obj.role==role.BUTTON and obj.simpleParent.role==role.LISTITEM:
				if obj.next.firstChild.firstChild.role==role.STATICTEXT:
					obj.name = obj.next.firstChild.firstChild.name
		except AttributeError: pass

		nextHandler()


	@script(
		description="是否自动朗读新消息",
		category="PC微信增强",
		gesture="kb:f3"
	)
	def script_autoMSG(self,gesture):
		self.isAutoMSG=not self.isAutoMSG
		config.conf["WeChatEnhancement"]["isAutoMSG"]=self.isAutoMSG
		if self.isAutoMSG:
			ui.message("自动读出新消息")
		else:
			ui.message("默认")

	def event_foreground(self, obj, nextHandler):
		if obj.windowClassName == "ImagePreviewWnd":
			wx.CallLater(800, self.clickButton, "提取文字", 0)
			wx.CallLater(100, self.ReportOCRResult)
		else:
			if self.ReportOCRResultTimer:
				self.ReportOCRResultTimer.Stop()
				self.OCRResult=None
		nextHandler()

	def ReportOCRResult(self):
		fg=api.getForegroundObject()
		try:
			if fg.simpleLastChild.role==role.STATICTEXT:
				if self.OCRResult != fg.simpleLastChild.name:
					self.OCRResult = fg.simpleLastChild.name
					ui.message(self.OCRResult)
					fg.simpleLastChild.name = self.OCRResult
			else: self.OCRResult = None
		except: pass
		self.ReportOCRResultTimer = wx.CallLater(100, self.ReportOCRResult)

	@script(
		description="关闭微信内置浏览器窗口",
		category="PC微信增强",
		gesture="kb:control+w"
	)
	def script_close(self,gesture):
		if api.getForegroundObject().windowClassName in ("CefWebViewWnd", "ImagePreviewWnd"):
			self.clickButton("关闭", 0)

	def clickButton(self, name, depth):
		obj = api.getForegroundObject()
		if not obj:
			return
		Depth = 0
		for child in obj.recursiveDescendants:
			Depth += 1
			if depth !=0 and Depth >= depth: break
			if child.role == role.BUTTON and child.name == name:
				self.click(child)
	def click(self, obj):
		l, t, w, h = obj.location
		x, y = int(l + w / 2), int(t + h / 2)
		winUser.setCursorPos(x, y)
		mouseHandler.executeMouseMoveEvent(x, y)
		mouseHandler.doPrimaryClick()