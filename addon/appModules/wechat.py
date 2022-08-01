
import appModuleHandler
import speech
import config
import ui
import controlTypes
from NVDAObjects import NVDAObjectTextInfo
from versionInfo import version_year
from scriptHandler import script
from nvwave import playWaveFile
from os.path import join, dirname
role = controlTypes.Role if version_year>=2022 else controlTypes.role.Role

class AppModule(appModuleHandler.AppModule):
	SOUND_LINK = join(dirname(__file__), 'link.wav')
	SOUND_POPUP = join(dirname(__file__), 'popup.wav')
	confspec = {
	"isAutoMSG": "boolean(default=False)"
	}
	config.conf.spec["WeChatEnhancement"] = confspec
	isAutoMSG = config.conf["WeChatEnhancement"]["isAutoMSG"]

	def event_NVDAObject_init(self, obj):
		# 修正微信的控件浏览光标不能获取到信息
		if role.EDITABLETEXT != obj.role:
			obj.displayText = obj.name
			obj.TextInfo = NVDAObjectTextInfo

	def event_nameChange(self, obj, nextHandler):
		if obj.role==role.LISTITEM and obj.parent.name=='消息' and obj.simpleFirstChild:
			playWaveFile(self.SOUND_POPUP)
			if self.isAutoMSG:
				if obj.name==None:
					children = obj.recursiveDescendants
					for child in children:
						if not speech.isBlank(child.name): ui.message(child.name)
				elif obj.simpleFirstChild.role==role.BUTTON:
					ui.message('%s 说： %s' % (obj.simpleFirstChild.name,obj.name))
					if obj.value: ui.message(obj.value)
				elif obj.simpleFirstChild.role==role.EDITABLETEXT:
					ui.message('%s 说： %s' % (obj.simpleLastChild.name,obj.name))
					if obj.value: ui.message(obj.value)
		nextHandler()

	def event_gainFocus(self, obj, nextHandler, isFocus=False):
		# 为特殊聊天消息增加提示
		if obj.role==role.LISTITEM and obj.parent.name=='消息':
			if obj.value !=None: 			playWaveFile(self.SOUND_LINK)

		# 处理发送按钮的标签
		if obj.role==role.BUTTON and obj.name=='sendBtn':
			obj.name='发送(S)'
		# 网络错误提示
		if 'NetErrInfoTipsBarWnd' == obj.windowClassName:
			ui.message (obj.displayText)
			return
		# 处理微信列表的朗读
		if obj.name==None:
			# 复选框
			if obj.role==role.CHECKBOX:
				ui.message(obj.simpleFirstChild.name)
			# 列表项
			if obj.role==role.LISTITEM:
				children = obj.recursiveDescendants
				for child in children:
					if child.role==role.CHECKBOX: speech.speakObject(child)
					elif not speech.isBlank(child.name): ui.message(child.name)
		# 处理订阅号文章评论的朗读
		# 请在 wechatbrowser.py 中导入 AppModule
		elif obj.treeInterceptor and obj.role==role.LIST and 'discuss_list' == obj.IA2Attributes.get('class'):
			o=obj.firstChild.firstChild
			while o:
				ui.message(o.firstChild.name)
				o=o.next
		elif obj.treeInterceptor and obj.role==role.LISTITEM and 'js_comment' in obj.IA2Attributes.get('class'):
			ui.message(obj.firstChild.name)
		elif obj.treeInterceptor and obj.role==role.BUTTON and 'sns_opr_btn sns_praise_btn' == obj.IA2Attributes.get('class'):
			ui.message(obj.simplePrevious.name)
		nextHandler()


	@script(
		description='是否自动朗读新消息',
		category='微信pc',
		gesture='kb:f3'
	)
	def script_autoMSG(self,gesture):
		self.isAutoMSG=not self.isAutoMSG
		config.conf["WeChatEnhancement"]["isAutoMSG"]=self.isAutoMSG
		if self.isAutoMSG:
			ui.message("自动读出新消息")
		else:
			ui.message("默认")

