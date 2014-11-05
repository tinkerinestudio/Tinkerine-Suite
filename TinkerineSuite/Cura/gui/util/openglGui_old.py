from __future__ import absolute_import
from __future__ import division
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import traceback
import sys
import os
import time
from wx import glcanvas
import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GL import *

from Cura.util import profile
from Cura.util import version
from Cura.gui.util import opengl
from Cura.gui.util import tooltipText


class animation(object):
	def __init__(self, gui, start, end, runTime):
		self._start = start
		self._end = end
		self._startTime = time.time()
		self._runTime = runTime
		gui._animationList.append(self)

	def isDone(self):
		return time.time() > self._startTime + self._runTime

	def getPosition(self):
		if self.isDone():
			return self._end
		f = (time.time() - self._startTime) / self._runTime
		ts = f*f
		tc = f*f*f
		#f = 6*tc*ts + -15*ts*ts + 10*tc
		f = tc + -3*ts + 3*f
		return self._start + (self._end - self._start) * f

class Tooltip(wx.Panel):
	"A base class for configuration dialogs. Handles creation of settings, and popups"
	def __init__(self, parent):
		super(Tooltip, self).__init__(parent)
		
		self.settingControlList = []
		
		#Create the popup window
		self.popup = wx.PopupWindow(self, flags=wx.BORDER_SIMPLE)
		self.popup.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_INFOBK))
		self.popup.setting = None
		self.popup.text = wx.StaticText(self.popup, -1, 'aaaaaaa');
		self.popup.sizer = wx.BoxSizer()
		self.popup.sizer.Add(self.popup.text, flag=wx.EXPAND|wx.ALL, border=1)
		self.popup.SetSizer(self.popup.sizer)
		
		self.timer = 0
		
		self.showing = False
		self._parent = parent

	def OnPopupDisplay(self, setting, x, y):
		self.timer += 1
		print self.timer
		self.popup.setting = setting
		self.UpdatePopup(setting, x, y)
		self.popup.Show()
		self.showing = True
		#print self.popup.IsShown()
		#print "AHAH"
		
	def OnPopupHide(self, e):
		self.popup.Hide()
		self.showing = False
	
	def UpdatePopup(self, setting, x, y):
		if self.popup.setting == setting:
			#if setting.validationMsg != '':
			#	self.popup.text.SetLabel(setting.validationMsg + '\n\n' + setting.helpText)
			#else:
			self.popup.text.SetLabel(setting)
			self.popup.text.Wrap(350)
			self.popup.Fit()
			#x, y = setting.ctrl.ClientToScreenXY(0, 0)
			#sx, sy = setting.ctrl.GetSizeTuple()
			#if platform.system() == "Windows":
			#	for some reason, under windows, the popup is relative to the main window... in some cases. (Wierd ass bug)
			#	wx, wy = self.ClientToScreenXY(0, 0)
				#x -= wx
				#y -= wy
			wx, wy = self.ClientToScreenXY(0, 0)
			w, h = self._parent.GetSize()
			#print wx, wy
			#print w, h
			self.popup.SetPosition((wx+x+30, wy+y-30))

		
class glGuiControl(object):
	def __init__(self, parent, pos):
		self._parent = parent
		self._base = parent._base
		self._pos = pos
		self._size = (0,0, 1, 1)
		self._parent.add(self)
		
	def setSize(self, x, y, w, h):
		self._size = (x, y, w, h)

	def getSize(self):
		return self._size

	def getMinSize(self):
		return 1, 1

	def updateLayout(self):
		pass

	def focusNext(self):
		for n in xrange(self._parent._glGuiControlList.index(self) + 1, len(self._parent._glGuiControlList)):
			if self._parent._glGuiControlList[n].setFocus():
				return
		for n in xrange(0, self._parent._glGuiControlList.index(self)):
			if self._parent._glGuiControlList[n].setFocus():
				return

	def focusPrevious(self):
		for n in xrange(self._glGuiControlList.index(self) -1, -1, -1):
			if self._glGuiControlList[n].setFocus():
				return
		for n in xrange(len(self._glGuiControlList) - 1, self._glGuiControlList.index(self), -1):
			if self._glGuiControlList[n].setFocus():
				return

	def setFocus(self):
		return False

	def hasFocus(self):
		return self._base._focus == self

	def OnMouseUp(self, x, y):
		pass

	def OnKeyChar(self, key):
		pass

class glGuiContainer(glGuiControl):
	def __init__(self, parent, pos):
		self._glGuiControlList = []
		glGuiLayoutButtons(self)
		super(glGuiContainer, self).__init__(parent, pos)

	def add(self, ctrl):
		self._glGuiControlList.append(ctrl)
		self.updateLayout()

	def OnMouseDown(self, x, y, button):
		for ctrl in self._glGuiControlList:
			if ctrl.OnMouseDown(x, y, button):
				return True
		return False

	def OnMouseUp(self, x, y):
		for ctrl in self._glGuiControlList:
			if ctrl.OnMouseUp(x, y):
				return True
		return False

	def OnMouseMotion(self, x, y):
		handled = False
		for ctrl in self._glGuiControlList:
			if ctrl.OnMouseMotion(x, y):
				handled = True
		return handled

	def draw(self):
		for ctrl in self._glGuiControlList:
			ctrl.draw()

	def updateLayout(self):
		self._layout.update()
		for ctrl in self._glGuiControlList:
			ctrl.updateLayout()

class glGuiPanel(glcanvas.GLCanvas):
	def __init__(self, parent):
		attribList = (glcanvas.WX_GL_RGBA, glcanvas.WX_GL_DOUBLEBUFFER, glcanvas.WX_GL_DEPTH_SIZE, 24, glcanvas.WX_GL_STENCIL_SIZE, 8, 0)
		glcanvas.GLCanvas.__init__(self, parent, style=wx.WANTS_CHARS, attribList = attribList)
		self._base = self
		self._focus = None
		self._container = None
		self._container = glGuiContainer(self, (0,0))
		self._shownError = False
		self._parent = parent

		self._context = glcanvas.GLContext(self)
		self._glButtonsTexture = None
		#self._glButtonsSettingsTexture = None
		self._glRobotTexture = None
		self._glLittoTexture = None
		self._glBlackBoxTexture = None
		self._buttonSize = 64

		self._animationList = []
		self.glReleaseList = []
		self._refreshQueued = False
		self.bla = 0

		wx.EVT_PAINT(self, self._OnGuiPaint)
		wx.EVT_SIZE(self, self._OnSize)
		wx.EVT_ERASE_BACKGROUND(self, self._OnEraseBackground)
		
		self.loaded = False
		glColor4ub(255,255,255,255)
		wx.EVT_LEFT_DOWN(self, self._OnGuiMouseDown)
		wx.EVT_LEFT_DCLICK(self, self._OnGuiMouseDown)
		wx.EVT_LEFT_UP(self, self._OnGuiMouseUp)
		wx.EVT_RIGHT_DOWN(self, self._OnGuiMouseDown)
		wx.EVT_RIGHT_DCLICK(self, self._OnGuiMouseDown)
		wx.EVT_RIGHT_UP(self, self._OnGuiMouseUp)
		wx.EVT_MIDDLE_DOWN(self, self._OnGuiMouseDown)
		wx.EVT_MIDDLE_DCLICK(self, self._OnGuiMouseDown)
		wx.EVT_MIDDLE_UP(self, self._OnGuiMouseUp)
		wx.EVT_MOTION(self, self._OnGuiMouseMotion)
		wx.EVT_CHAR(self, self._OnGuiKeyChar)
		wx.EVT_KILL_FOCUS(self, self.OnFocusLost)
		wx.EVT_IDLE(self, self._OnIdle)
		
		self._progressBar = None
		
	def setProgressBar(self, value):
		self._progressBar = value

	def getProgressBar(self):
		return self._progressBar

	def _OnIdle(self, e):
		if len(self._animationList) > 0 or self._refreshQueued:
			self._refreshQueued = False
			for anim in self._animationList:
				if anim.isDone():
					self._animationList.remove(anim)
			self.Refresh()

	def _OnGuiKeyChar(self, e):
		if self._focus is not None:
			self._focus.OnKeyChar(e.GetKeyCode())
			self.Refresh()
		else:
			self.OnKeyChar(e.GetKeyCode())

	def OnFocusLost(self, e):
		self._focus = None
		self.Refresh()

	def _OnGuiMouseDown(self,e):
		self.SetFocus()
		if self._container.OnMouseDown(e.GetX(), e.GetY(), e.GetButton()):
			self.Refresh()
			return
		self.OnMouseDown(e)

	def _OnGuiMouseUp(self, e):
		if self._container.OnMouseUp(e.GetX(), e.GetY()):
			self.Refresh()
			return
		self.OnMouseUp(e)

	def _OnGuiMouseMotion(self,e):
		self.Refresh()
		if not self._container.OnMouseMotion(e.GetX(), e.GetY()):
			self.OnMouseMotion(e)

	def _OnGuiPaint(self, e):
		h = self.GetSize().GetHeight()
		w = self.GetSize().GetWidth()
		#oldButtonSize = self._buttonSize
		#if h / 3 < w / 4:
		#	w = h * 4 / 3
		#if w < 64 * 8:
		#	self._buttonSize = 32
		#elif w < 64 * 10:
		#	self._buttonSize = 48
		#elif w < 64 * 15:
		#	self._buttonSize = 64
		#elif w < 64 * 20:
		#	self._buttonSize = 80
		#else:
		#	self._buttonSize = 96
		#if self._buttonSize != oldButtonSize:
			#self._container.updateLayout()

		dc = wx.PaintDC(self)
		try:
			self.SetCurrent(self._context)
			for obj in self.glReleaseList:
				obj.release()
			del self.glReleaseList[:]
			renderStartTime = time.time()
			self.OnPaint(e)
			self._drawGui()
			glFlush()
			if version.isDevVersion():
				renderTime = time.time() - renderStartTime
				glLoadIdentity()
				glTranslate(10, self.GetSize().GetHeight() - 30, -1)
				glColor4f(0.2,0.2,0.2,0.5)
				opengl.glDrawStringLeft("fps:%d" % (1 / renderTime))
			self.SwapBuffers()
		except:
			errStr = 'An error has occurred during the 3D view drawing.'
			tb = traceback.extract_tb(sys.exc_info()[2])
			errStr += "\n%s: '%s'" % (str(sys.exc_info()[0].__name__), str(sys.exc_info()[1]))
			for n in xrange(len(tb)-1, -1, -1):
				locationInfo = tb[n]
				errStr += "\n @ %s:%s:%d" % (os.path.basename(locationInfo[0]), locationInfo[2], locationInfo[1])
			if not self._shownError:
				wx.CallAfter(wx.MessageBox, errStr, '3D window error', wx.OK | wx.ICON_EXCLAMATION)
				self._shownError = True

	def _drawGui(self):
		if self._glButtonsTexture is None:
			self._glButtonsTexture = opengl.loadGLTexture('glButtons copy settings2.png')
			#self._glButtonsSettingsTexture = opengl.loadGLTexture('glButtons.png')
			#self._glRobotTexture = opengl.loadGLTexture('tinkersuite2.png')
			self._glLittoTexture = opengl.loadGLTexture('litto_label.png')
			self._glCoordiaTexture = opengl.loadGLTexture('Coordia_one.png')
			
			self._glSettingBorder = opengl.loadGLTexture('setting_border.png')
			self._glSettingBorder2 = opengl.loadGLTexture('setting_border2.png')
			self._glCameraBorder = opengl.loadGLTexture('camera_border.png')
			self._glViewmodeBorder = opengl.loadGLTexture('viewmode_border.png')
			self._glBlackBoxTexture = opengl.loadGLTexture('black_square.png')
			self._glScaleTexture = opengl.loadGLTexture('scale_border2.png')
			self._glRotateTexture = opengl.loadGLTexture('rotate_border.png')
		
		glDisable(GL_DEPTH_TEST)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glDisable(GL_LIGHTING)
		glColor4ub(255,255,255,255)

		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		size = self.GetSize()
		glOrtho(0, size.GetWidth()-1, size.GetHeight()-1, 0, -1000.0, 1000.0)
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		glEnd()
		glDisable(GL_TEXTURE_2D)
		glPopMatrix()
		
		
		if 0: #removed tinkersuite

			glBindTexture(GL_TEXTURE_2D, self._glRobotTexture)
			glEnable(GL_TEXTURE_2D)
			glPushMatrix()
			glColor4f(1,1,1,1)
			glTranslate(size.GetWidth() - 12, 48,0)
			#s = self._buttonSize * 1.4
			glScale(343,40,100)
			glBegin(GL_QUADS)
			glTexCoord2f(1, 0)
			glVertex2f(0,-1)
			glTexCoord2f(0, 0)
			glVertex2f(-1,-1)
			glTexCoord2f(0, 1)
			glVertex2f(-1, 0)
			glTexCoord2f(1, 1)
			glVertex2f(0, 0)
		glEnd()
		glDisable(GL_TEXTURE_2D)
		glPopMatrix()

		glBindTexture(GL_TEXTURE_2D, self._glCoordiaTexture)
		glEnable(GL_TEXTURE_2D)
		glPushMatrix()
		glColor4f(1,1,1,1)
		glTranslate(305, 68,0)
		glScale( 295,58,255)
			
		glBegin(GL_QUADS)
		glTexCoord2f(1, 0)
		glVertex2f(0,-1)
		glTexCoord2f(0, 0)
		glVertex2f(-1,-1)
		glTexCoord2f(0, 1)
		glVertex2f(-1, 0)
		glTexCoord2f(1, 1)
		glVertex2f(0, 0)
		glEnd()
		glDisable(GL_TEXTURE_2D)
		glPopMatrix()
		
		#the outside box for the settings panel
		if self.settingsOpen:
			if self.advancedOpen:
				glBindTexture(GL_TEXTURE_2D, self._glSettingBorder)
			else:
				glBindTexture(GL_TEXTURE_2D, self._glSettingBorder2)
			glEnable(GL_TEXTURE_2D)
			glPushMatrix()
			glColor4f(1,1,1,1)
			if self.advancedOpen:
				glTranslate(380+15, size.GetHeight()-15,0)
				glScale(387,196,100)

			else:
				glTranslate(380+15, size.GetHeight()-15,0)
				glScale(387,126,100)
			glBegin(GL_QUADS)
			glTexCoord2f(1, 0)
			glVertex2f(0,-1)
			glTexCoord2f(0, 0)
			glVertex2f(-1,-1)
			glTexCoord2f(0, 1)
			glVertex2f(-1, 0)
			glTexCoord2f(1, 1)
			glVertex2f(0, 0)
			glEnd()
			glDisable(GL_TEXTURE_2D)
			glPopMatrix()
		if self.cameraOpen:
			glBindTexture(GL_TEXTURE_2D, self._glCameraBorder)
			glEnable(GL_TEXTURE_2D)
			glPushMatrix()
			glColor4f(1,1,1,1)
			
			size = self.GetSize()
			
			x = size.GetWidth()/2 + 143
			#if x < 585:
			#	x = 585
			
			glTranslate(x, size.GetHeight()-62,0)
			glScale(292,84,100)
			glBegin(GL_QUADS)
			glTexCoord2f(1, 0)
			glVertex2f(0,-1)
			glTexCoord2f(0, 0)
			glVertex2f(-1,-1)
			glTexCoord2f(0, 1)
			glVertex2f(-1, 0)
			glTexCoord2f(1, 1)
			glVertex2f(0, 0)
			glEnd()
			glDisable(GL_TEXTURE_2D)
			glPopMatrix()
		if self.viewmodeOpen:
			glBindTexture(GL_TEXTURE_2D, self._glViewmodeBorder)
			glEnable(GL_TEXTURE_2D)
			glPushMatrix()
			glColor4f(1,1,1,1)
			
			size = self.GetSize()
			
			x = size.GetWidth()/2 + 159
			#if x < 624:
			#	x = 624
			
			glTranslate(x, size.GetHeight()-62,0)
			glScale(324,83,100)
			glBegin(GL_QUADS)
			glTexCoord2f(1, 0)
			glVertex2f(0,-1)
			glTexCoord2f(0, 0)
			glVertex2f(-1,-1)
			glTexCoord2f(0, 1)
			glVertex2f(-1, 0)
			glTexCoord2f(1, 1)
			glVertex2f(0, 0)
			glEnd()
			glDisable(GL_TEXTURE_2D)
			glPopMatrix()
			
		if self.rotateToolButton.getSelected():
			glBindTexture(GL_TEXTURE_2D, self._glRotateTexture)
			glEnable(GL_TEXTURE_2D)
			glPushMatrix()
			glColor4f(1,1,1,1)
			
			size = self.GetSize()
			
			x = size.GetWidth()/2 + 102
			#if x < 624:
			#	x = 624
			
			glTranslate(x, size.GetHeight()-62,0)
			glScale(206,83,100)
			glBegin(GL_QUADS)
			glTexCoord2f(1, 0)
			glVertex2f(0,-1)
			glTexCoord2f(0, 0)
			glVertex2f(-1,-1)
			glTexCoord2f(0, 1)
			glVertex2f(-1, 0)
			glTexCoord2f(1, 1)
			glVertex2f(0, 0)
			glEnd()
			glDisable(GL_TEXTURE_2D)
			glPopMatrix()
			
		if self.scaleToolButton.getSelected():
			glBindTexture(GL_TEXTURE_2D, self._glScaleTexture)
			glEnable(GL_TEXTURE_2D)
			glPushMatrix()
			glColor4f(1,1,1,1)
			
			size = self.GetSize()
			
			x = size.GetWidth()/2 + 188
			#if x < 624:
			#	x = 624
			
			glTranslate(x, size.GetHeight()-60,0)
			glScale(373,120,0)
			glBegin(GL_QUADS)
			glTexCoord2f(1, 0)
			glVertex2f(0,-1)
			glTexCoord2f(0, 0)
			glVertex2f(-1,-1)
			glTexCoord2f(0, 1)
			glVertex2f(-1, 0)
			glTexCoord2f(1, 1)
			glVertex2f(0, 0)
			glEnd()
			glDisable(GL_TEXTURE_2D)
			glPopMatrix()
			
		if profile.getProfileSetting('vase') == 'True' and self.settingsOpen and self.advancedOpen:
			glBindTexture(GL_TEXTURE_2D, self._glBlackBoxTexture)
			glEnable(GL_TEXTURE_2D)
			glPushMatrix()
			glColor4f(1,1,1,.3)
			glTranslate(143, size.GetHeight()-99,0)
			glScale(125,28,100)
			glBegin(GL_QUADS)
			glTexCoord2f(1, 0)
			glVertex2f(0,-1)
			glTexCoord2f(0, 0)
			glVertex2f(-1,-1)
			glTexCoord2f(0, 1)
			glVertex2f(-1, 0)
			glTexCoord2f(1, 1)
			glVertex2f(0, 0)
			glEnd()
			glDisable(GL_TEXTURE_2D)
			glPopMatrix()
		progress = self._progressBar
		if progress is not None:
			bs = 64
			pos = (115,385)
			glColor4ub(60,60,60,255)

			size = self.GetSize()
			y = float(size.GetHeight())/2 + (1.5 * bs * 1.2) - bs/2
			
			
			opengl.glDrawQuad(pos[0]-bs/2, y, bs, bs / 3)
			glColor4ub(255,255,255,255)
			opengl.glDrawQuad(pos[0]-bs/2+2, y+2, (bs - 2) * progress + 1, bs / 3 - 4)
			glTranslate(pos[0]-bs/2,y-10,0)
			glColor4ub(0,0,0,200)
			if progress == 0.001:
				opengl.glDrawStringLeft("Preparing to slice...")
			else:
				opengl.glDrawStringLeft("Slicing...")

			glTranslate(70,28,0)
			opengl.glDrawStringLeft(str(int(progress*100)) + "%")
			glTranslate(-70,-28,0)
			glTranslate(-(pos[0]-bs/2),-y+10,0)

		#glColor4ub(255,255,255,255)
		#if self.loaded == False:
		#	self.abc = testtext.font_data("HelveticaNeueLTStd-Lt.otf",12)
		#	self.loaded = True

		#self.abc.glPrint(500,500,str(self.bla))
		#self.abc.glPrint(500,550,"Litto 3d Printer")
		#self.bla = self.bla+1
		
		#argh = tooltipText.tooltipText(200, size.GetHeight()-120, "PROFILE", "HelveticaNeueLTStd-Lt.otf", 16, (255,111,22))

		
		self._container.draw() #moved this to end so the buttons and stuff draw on top of the gui elements (like the setting panel)
	def _OnEraseBackground(self,event):
		#Workaround for windows background redraw flicker.
		pass

	def _OnSize(self,e):
		self._container.setSize(0, 0, self.GetSize().GetWidth(), self.GetSize().GetHeight())
		self._container.updateLayout()
		self.Refresh()

	def OnMouseDown(self,e):
		pass
	def OnMouseUp(self,e):
		pass
	def OnMouseMotion(self, e):
		pass
	def OnKeyChar(self, keyCode):
		pass
	def OnPaint(self, e):
		pass
	def OnKeyChar(self, keycode):
		pass

	def QueueRefresh(self):
		wx.CallAfter(self._queueRefresh)

	def _queueRefresh(self):
		self._refreshQueued = True

	def add(self, ctrl):
		if self._container is not None:
			self._container.add(ctrl)

class glGuiLayoutButtons(object):
	def __init__(self, parent):
		self._parent = parent
		self._parent._layout = self

	def update(self):
		bs = self._parent._base._buttonSize
		x0, y0, w, h = self._parent.getSize()
		gridSize = bs * 1.0
		for ctrl in self._parent._glGuiControlList:
			pos = ctrl._pos
			
			try:
				imageID = ctrl._imageID
			except:
				imageID = None
				
			if pos[0] < 0:
				x = w + pos[0] * gridSize - bs * 0.2
				if x < 660 + (pos[0] + 9) * gridSize and pos[0] != -1.11: #-1.11 is for the gcode slider. 
					x = 660 + (pos[0] + 9) * gridSize
			else:
				x = pos[0] * gridSize + bs * 0.2

			try:
				if ctrl._center == "bottom":
					x = float(w)/2 + (pos[0] * gridSize * 1.2) - gridSize/2
					
			except:
				#y = h + pos[1] * gridSize * 1.2 - bs * 0.2
				pass

				
				
			if pos[1] < 0:
				y = h + pos[1] * gridSize * 1.2 - bs * 0.2
				#gg = (pos[1] + 6.5) * 64
				if pos[1] == -1:
					pass
					#print "negative one"
			else:
				y = pos[1] * gridSize * 1.2 + bs * 0.2
				
			try:
				if ctrl._center == "left":
					y = float(h)/2 + (pos[1] * gridSize * 1.2) - gridSize
			except:
				#y = h + pos[1] * gridSize * 1.2 - bs * 0.2
				pass

			
			ctrl.setSize(x, y, gridSize, gridSize)

	def getLayoutSize(self):
		_, _, w, h = self._parent.getSize()
		return w, h

class glGuiLayoutGrid(object):
	def __init__(self, parent):
		self._parent = parent
		self._parent._layout = self
		self._size = 0,0
		self._alignBottom = True

	def update(self):
		borderSize = self._parent._base._buttonSize * 0.2
		x0, y0, w, h = self._parent.getSize()
		x0 += borderSize
		y0 += borderSize
		widths = {}
		heights = {}
		for ctrl in self._parent._glGuiControlList:
			x, y = ctrl._pos
			w, h = ctrl.getMinSize()
			if not x in widths:
				widths[x] = w
			else:
				widths[x] = max(widths[x], w)
			if not y in heights:
				heights[y] = h
			else:
				heights[y] = max(heights[y], h)
		self._size = sum(widths.values()) + borderSize * 2, sum(heights.values()) + borderSize * 2
		if self._alignBottom:
			y0 -= self._size[1] - self._parent.getSize()[3]
			self._parent.setSize(x0 - borderSize, y0 - borderSize, self._size[0], self._size[1])
		for ctrl in self._parent._glGuiControlList:
			x, y = ctrl._pos
			x1 = x0
			y1 = y0
			for n in xrange(0, x):
				if not n in widths:
					widths[n] = 3
				x1 += widths[n]
			for n in xrange(0, y):
				if not n in heights:
					heights[n] = 3
				y1 += heights[n]
			ctrl.setSize(x1, y1, widths[x], heights[y])

	def getLayoutSize(self):
		return self._size

class glButton(glGuiControl):
	def __init__(self, parent, imageID, tooltipTitle, tooltip, pos, callback, Xnudge = 0, Ynudge = 0, size = None, center = "none"):
		self._buttonSize = size
		self._hidden = False
		super(glButton, self).__init__(parent, pos)
		self._tooltip = tooltip
		self._tooltipTitle = tooltipTitle
		self._parent = parent
		self._imageID = imageID
		self._callback = callback
		self._selected = False
		self._focus = False
		self._disabled = False
		self._showExpandArrow = False
		self._progressBar = None
		self._altTooltip = ''
		self._Xnudge = Xnudge
		self._Ynudge = Ynudge
		self._glDittoTexture = None
		self._center = center
		
		self._tooltipTextTitle = tooltipText.tooltipText(20, 130, self._tooltipTitle, "HelveticaNeueLTStd-Lt.otf", 24, (139,197,63)) #(43,182,115)
		self._tooltipTextTitle.makeText()
		self.oldtextTitle = self._tooltipTextTitle._text
		
		self._tooltipText = tooltipText.tooltipText(20, 145, self._tooltip, "HelveticaNeueLTStd-Lt.otf", 16, (43,182,115)) #(43,182,115)
		self._tooltipText.makeText()
		self.oldtext = self._tooltipText._text
		
	def getImageID(self):
		return int(self._imageID)
		
	def setImageID(self, value):
		self._imageID = value
		
	def setSelected(self, value):
		self._selected = value

	def setExpandArrow(self, value):
		self._showExpandArrow = value

	def setHidden(self, value):
		self._hidden = value

	def setDisabled(self, value):
		self._disabled = value

	def setProgressBar(self, value):
		self._progressBar = value

	def getProgressBar(self):
		return self._progressBar

	def setBottomText(self, value):
		self._altTooltip = value

	def getSelected(self):
		return self._selected

	def getMinSize(self):
		if self._hidden:
			return 0, 0
		if self._buttonSize is not None:
			return self._buttonSize, self._buttonSize
		return self._base._buttonSize, self._base._buttonSize

	def _getPixelPos(self):
		x0, y0, w, h = self.getSize()
		#print self.getSize()
		return x0 + w / 2, y0 + h / 2

	def draw(self):
		if self._hidden:
			return

		cx = (self._imageID % 4) / 4
		cy = int(self._imageID / 4) / 4
		bs = self.getMinSize()[0]
		pos = self._getPixelPos()

		glBindTexture(GL_TEXTURE_2D, self._base._glButtonsTexture)

		#if self._disabled:
		#	glColor4ub(128,128,128,128)
		#else:
		#	glColor4ub(255,255,255,255)
			
		scale = 0.9
		if self._selected:
			#scale = 0.9
			glColor4ub(255,25,0,255)
		elif self._focus:
			#if self._imageID != 21:#not the upper left logo
			glColor4ub(43,222,115,255)
		else:
			glColor4ub(200,200,200,255)
		#opengl.glDrawTexturedQuad(self._Xnudge+pos[0]-bs*scale/2, self._Ynudge + pos[1]-bs*scale/2, bs*scale, bs*scale, 0)
		opengl.glDrawTexturedQuad(self._Xnudge+pos[0]-bs*scale/2, self._Ynudge + pos[1]-bs*scale/2, bs*scale, bs*scale, self._imageID)
		if self._showExpandArrow:
			if self._selected:
				opengl.glDrawTexturedQuad(pos[0]+bs*scale/2-bs*scale/4*1.2, pos[1]-bs*scale/2*1.2, bs*scale/4, bs*scale/4, 1)
			else:
				opengl.glDrawTexturedQuad(pos[0]+bs*scale/2-bs*scale/4*1.2, pos[1]-bs*scale/2*1.2, bs*scale/4, bs*scale/4, 1, 2)
		glPushMatrix()
		glTranslatef(pos[0], pos[1], 0)
		glDisable(GL_TEXTURE_2D)
		if self._focus:
			
			glTranslatef(0, -0.55*bs*scale, 0)
			if 0:
				glPushMatrix()
				glColor4ub(60,60,60,255)
				glTranslatef(-1, -1, 0)
				opengl.glDrawStringCenter(self._tooltip)
				glTranslatef(0, 2, 0)
				opengl.glDrawStringCenter(self._tooltip)
				glTranslatef(2, 0, 0)
				opengl.glDrawStringCenter(self._tooltip)
				glTranslatef(0, -2, 0)
				opengl.glDrawStringCenter(self._tooltip)
				glPopMatrix()

				glColor4ub(255,255,255,255)
				opengl.glDrawStringCenter(self._tooltip)
			glPopMatrix()
			
			#don't use this anymore
			#if self._tooltipTextTitle.mode == "follow": 
			#	self._tooltipTextTitle._x = pos[0] -32 #TODO: calculate how long the word is
			#	self._tooltipTextTitle._y = pos[1] -20
				
			if self._center == "left":
				self._tooltipTextTitle._x = pos[0] +34
				self._tooltipTextTitle._y = pos[1] +7
				
				self._tooltipText._x = pos[0] +34
				self._tooltipText._y = pos[1] +20
			elif self._center == "bottom":
				length = len(str(self._tooltipTitle))
				self._tooltipTextTitle._x = pos[0] - (length/2)*12 #TODO: calculate how long the word is
				self._tooltipTextTitle._y = pos[1] -28

				

			self._tooltipTextTitle.makeText()
			self._tooltipTextTitle.displayText()
			

			self._tooltipText.makeText()
			self._tooltipText.displayText()
			
			if 0: #removed image for hover over
				if self._glDittoTexture is None:
					self._glDittoTexture = opengl.loadGLTexture('import_text2.png')
				glBindTexture(GL_TEXTURE_2D, self._glDittoTexture)
				glEnable(GL_TEXTURE_2D)
				glPushMatrix()
				glColor4f(1,1,1,1)
				glTranslate(180, 160,100)
				glScale(160,49,100)
				glBegin(GL_QUADS)
				glTexCoord2f(1, 0)
				glVertex2f(0,-1)
				glTexCoord2f(0, 0)
				glVertex2f(-1,-1)
				glTexCoord2f(0, 1)
				glVertex2f(-1, 0)
				glTexCoord2f(1, 1)
				glVertex2f(0, 0)
				glEnd()
				glDisable(GL_TEXTURE_2D)
			
		glPopMatrix()
		progress = self._progressBar
		if progress is not None:
			glColor4ub(60,60,60,255)
			opengl.glDrawQuad(pos[0]-bs/2, pos[1]+bs/2, bs, bs / 4)
			glColor4ub(255,255,255,255)
			opengl.glDrawQuad(pos[0]-bs/2+2, pos[1]+bs/2+2, (bs - 5) * progress + 1, bs / 4 - 4)
		elif len(self._altTooltip) > 0:
			glPushMatrix()
			glTranslatef(pos[0], pos[1], 0)
			glTranslatef(0.6*bs*scale, 0, 0)

			glPushMatrix()
			glColor4ub(60,60,60,255)
			glTranslatef(-1, -1, 0)
			opengl.glDrawStringLeft(self._altTooltip)
			glTranslatef(0, 2, 0)
			opengl.glDrawStringLeft(self._altTooltip)
			glTranslatef(2, 0, 0)
			opengl.glDrawStringLeft(self._altTooltip)
			glTranslatef(0, -2, 0)
			opengl.glDrawStringLeft(self._altTooltip)
			glPopMatrix()

			glColor4ub(255,255,255,255)
			opengl.glDrawStringLeft(self._altTooltip)
			glPopMatrix()

	def _checkHit(self, x, y):
		if self._hidden or self._disabled:
			return False
		bs = self.getMinSize()[0]
		pos = self._getPixelPos()
		return -bs * 0.5 <= x - pos[0] <= bs * 0.5 and -bs * 0.5 <= y - pos[1] <= bs * 0.5

	def OnMouseMotion(self, x, y):
		if self._checkHit(x, y):
			self._focus = True
			return True
		self._focus = False
		return False

	def OnMouseDown(self, x, y, button):
		if self._checkHit(x, y):
			self._callback(button)
			return True
		return False

class glRadioButton(glButton):
	def __init__(self, parent, imageID, tooltipTitle, tooltip, pos, group, callback, xNudge, yNudge, size, scaleModifier, center):
		super(glRadioButton, self).__init__(parent, imageID, tooltipTitle, tooltip, pos, self._onRadioSelect, xNudge, yNudge, size, center)
		self._group = group
		self._radioCallback = callback
		self._group.append(self)
		self._center = center
		self._scaleModifier = scaleModifier

	def setSelected(self, value):
		self._selected = value

	def _onRadioSelect(self, button):
		self._base._focus = None
		for ctrl in self._group:
			if ctrl != self:
				ctrl.setSelected(False)
		if self.getSelected():
			self.setSelected(False)
		else:
			self.setSelected(True)
		self._radioCallback(button)
		
	def _checkHit(self, x, y):
		if self._hidden or self._disabled:
			return False
		bs = self.getMinSize()[0]*self._scaleModifier
		pos = self._getPixelPos()
		return -bs * 0.5 <= x - pos[0] <= bs * 0.5 and -bs * 0.5 <= y - pos[1] <= bs * 0.5
class glComboButton(glButton):
	def __init__(self, parent, tooltipTitle, tooltip, imageIDs, tooltips, pos, callback):
		super(glComboButton, self).__init__(parent, imageIDs[0], tooltipTitle, tooltip, pos, self._onComboOpenSelect)
		self._imageIDs = imageIDs
		self._tooltips = tooltips
		self._comboCallback = callback
		self._selection = 0

	def _onComboOpenSelect(self, button):
		if self.hasFocus():
			self._base._focus = None
		else:
			self._base._focus = self

	def draw(self):
		if self._hidden:
			return
		self._selected = self.hasFocus()
		super(glComboButton, self).draw()

		bs = self._base._buttonSize / 2
		pos = self._getPixelPos()

		if not self._selected:
			return

		glPushMatrix()
		glTranslatef(pos[0]+bs*0.5, pos[1] + bs*0.5, 0)
		glBindTexture(GL_TEXTURE_2D, self._base._glButtonsTexture)
		for n in xrange(0, len(self._imageIDs)):
			glTranslatef(0, bs, 0)
			glColor4ub(255,255,0,255)
			opengl.glDrawTexturedQuad(-0.5*bs,-0.5*bs,bs,bs, 0)
			opengl.glDrawTexturedQuad(-0.5*bs,-0.5*bs,bs,bs, self._imageIDs[n])
			glDisable(GL_TEXTURE_2D)

			glPushMatrix()
			glTranslatef(-0.55*bs, 0.1*bs, 0)

			glPushMatrix()
			glColor4ub(60,60,60,255)
			glTranslatef(-1, -1, 0)
			opengl.glDrawStringRight(self._tooltips[n])
			glTranslatef(0, 2, 0)
			opengl.glDrawStringRight(self._tooltips[n])
			glTranslatef(2, 0, 0)
			opengl.glDrawStringRight(self._tooltips[n])
			glTranslatef(0, -2, 0)
			opengl.glDrawStringRight(self._tooltips[n])
			glPopMatrix()

			glColor4ub(255,255,255,255)
			opengl.glDrawStringRight(self._tooltips[n])
			glPopMatrix()
		glPopMatrix()

	def getValue(self):
		return self._selection

	def setValue(self, value):
		self._selection = value
		self._imageID = self._imageIDs[self._selection]
		self._comboCallback()

	def OnMouseDown(self, x, y, button):
		if self._hidden or self._disabled:
			return False
		if self.hasFocus():
			bs = self._base._buttonSize / 2
			pos = self._getPixelPos()
			if 0 <= x - pos[0] <= bs and 0 <= y - pos[1] - bs <= bs * len(self._imageIDs):
				self._selection = int((y - pos[1] - bs) / bs)
				self._imageID = self._imageIDs[self._selection]
				self._base._focus = None
				self._comboCallback()
				return True
		return super(glComboButton, self).OnMouseDown(x, y, button)

class glFrame(glGuiContainer):
	def __init__(self, parent, pos):
		super(glFrame, self).__init__(parent, pos)
		self._selected = False
		self._focus = False
		self._hidden = False

	def setSelected(self, value):
		self._selected = value

	def setHidden(self, value):
		self._hidden = value
		for child in self._glGuiControlList:
			if self._base._focus == child:
				self._base._focus = None

	def getSelected(self):
		return self._selected

	def getMinSize(self):
		return self._base._buttonSize, self._base._buttonSize

	def _getPixelPos(self):
		x0, y0, w, h = self.getSize()
		return x0, y0

	def draw(self):
		if self._hidden:
			return

		bs = self._parent._buttonSize
		pos = self._getPixelPos()

		size = self._layout.getLayoutSize()
		#glColor4ub(0,0,0,200)
		#opengl.glDrawStretchedQuad(pos[0], pos[1], size[0], size[1], bs*0.75, 0)
		#Draw the controls on the frame
		super(glFrame, self).draw()

	def _checkHit(self, x, y):
		if self._hidden:
			return False
		pos = self._getPixelPos()
		w, h = self._layout.getLayoutSize()
		#print w,h
		return 0 <= x - pos[0] <= w and 0 <= y - pos[1] <= h

	def OnMouseMotion(self, x, y):
		#super(glFrame, self).OnMouseMotion(x, y)
		if self._checkHit(x, y):
			self._focus = True
			return True
		self._focus = False
		return False

	def OnMouseDown(self, x, y, button):
		if self._checkHit(x, y):
			super(glFrame, self).OnMouseDown(x, y, button)
			return True
		return False

class glNotification(glFrame):
	def __init__(self, parent, pos):
		self._anim = None
		super(glNotification, self).__init__(parent, pos)
		glGuiLayoutGrid(self)._alignBottom = False
		self._label = glLabel(self, "Notification", (0, 0))
		self._buttonEject = glButton(self, 31, "Eject", '', (1, 0), self.onEject, 25)
		self._button = glButton(self, 30, "", '', (2, 0), self.onClose, 25)
		self._padding = glLabel(self, "", (0, 1))
		self.setHidden(True)

	def setSize(self, x, y, w, h):
		w, h = self._layout.getLayoutSize()
		baseSize = self._base.GetSizeTuple()
		if self._anim is not None:
			super(glNotification, self).setSize(baseSize[0] / 2 - w / 2, baseSize[1] - self._anim.getPosition() - self._base._buttonSize * 0.2, 1, 1)
		else:
			super(glNotification, self).setSize(baseSize[0] / 2 - w / 2, baseSize[1] - self._base._buttonSize * 0.2, 1, 1)

	def draw(self):
		self.setSize(0,0,0,0)
		self.updateLayout()
		super(glNotification, self).draw()

	def message(self, text, ejectCallback = None):
		self._anim = animation(self._base, -20, 25, 1)
		self.setHidden(False)
		self._label.setLabel(text)
		self._buttonEject.setHidden(ejectCallback is None)
		self._ejectCallback = ejectCallback
		self._base._queueRefresh()
		self.updateLayout()

	def onEject(self, button):
		self.onClose(button)
		self._ejectCallback()

	def onClose(self, button):
		if self._anim is not None:
			self._anim = animation(self._base, self._anim.getPosition(), -20, 1)
		else:
			self._anim = animation(self._base, 25, -20, 1)

class glLabel(glGuiControl):
	def __init__(self, parent, label, pos):
		self._label = label
		super(glLabel, self).__init__(parent, pos)
		self._center = "bottom"
		self._tooltipText = tooltipText.tooltipText(200, 200, self._label, "HelveticaNeueLTStd-Lt.otf", 11, (0,0,0,255)) #(139,197,63)) #(43,182,115)
		self._tooltipText.makeText()
		self._hidden = False
	def setLabel(self, label):
		self._label = label
		
	def setHidden(self, value):
		self._hidden = value
		
	def getMinSize(self):
		w, h = opengl.glGetStringSize(self._label)
		return w + 10, h + 4

	def _getPixelPos(self):
		x0, y0, w, h = self.getSize()
		return x0, y0

	def draw(self):
		if self._hidden:
			return
		x, y, w, h = self.getSize()
		
		glPushMatrix()
		glTranslatef(x, y, 0)

		glColor4ub(0,0,0,0)
		glBegin(GL_QUADS)
		glTexCoord2f(1, 0)
		glVertex2f( w, 0)
		glTexCoord2f(0, 0)
		glVertex2f( 0, 0)
		glTexCoord2f(0, 1)
		glVertex2f( 0, h)
		glTexCoord2f(1, 1)
		glVertex2f( w, h)
		glEnd()
		
		self._tooltipText._x = x + 5
		self._tooltipText._y = y + h
		self._tooltipText._text = self._label
		
		self._tooltipText.makeText()		
		self._tooltipText.displayText()
		
		glTranslate(5, h - 5, 0)
		glColor4ub(0,0,0,255)
		#opengl.glDrawStringLeft(self._label)
		glPopMatrix()

	def _checkHit(self, x, y):
		return False

	def OnMouseMotion(self, x, y):
		return False

	def OnMouseDown(self, x, y, button):
		return False

class glNumberCtrl(glGuiControl):
	def __init__(self, parent, value, pos, callback, isPercent = False):
		self._callback = callback
		self._value = str(value)
		self._selectPos = 0
		self._maxLen = 5
		self._inCallback = False
		self._center = "bottom"
		self._isPercent = isPercent
		self._hidden = False
		super(glNumberCtrl, self).__init__(parent, pos)

		self._tooltipText = tooltipText.tooltipText(200, 200, self._value, "HelveticaNeueLTStd-Lt.otf", 13, (43,182,115)) #(139,197,63)) #(43,182,115)
		self._tooltipText.makeText()
		
	def setHidden(self, value):
		self._hidden = value
		
	def setValue(self, value):
		if self._inCallback:
			return
		self._value = str(value)

	def getMinSize(self):
		w, h = opengl.glGetStringSize("VALUES")
		return w + 4, h + 4

	def _getPixelPos(self):
		x0, y0, w, h = self.getSize()
		w, h = opengl.glGetStringSize("VALUES")
		w -= 25
		h += 10
		return x0, y0

	def draw(self):
		#if not self._parent.scaleToolButton.getSelected():
		#	return
		if self._hidden:
			return
		x, y, w, h = self.getSize()
		w, h = opengl.glGetStringSize("VALUES")
		w -= 25
		h += 10
		
		#x+=10
		stringLength = opengl.glGetStringSize(self._value[0:len(self._value)])[0]
		adjust = stringLength / 2.0
		#if self._isPercent:
			#adjust = (3 - len(self._value)) * 5
		#	adjust = stringLength / 2.0
		#else:
		#	adjust = (4 - len(self._value)) * 7
		x -= adjust
		glPushMatrix()
		glTranslatef(x, y, 0)

		if self.hasFocus():
			glColor4ub(220,220,220,0)
			glBegin(GL_QUADS)
			glTexCoord2f(1, 0)
			glVertex2f( w, 0)
			glTexCoord2f(0, 0)
			glVertex2f( 0, 0)
			glTexCoord2f(0, 1)
			glVertex2f( 0, h-1)
			glTexCoord2f(1, 1)
			glVertex2f( w, h-1)
			glEnd()
		else:
			glColor4ub(200,200,200,150)

		glTranslate(5, h - 5, 0)
		glColor4ub(0,0,0,255)
		
		

		
		self._tooltipText._x = x + 5
		self._tooltipText._y = y + h -5
		self._tooltipText._text = self._value
		if self._isPercent:
			self._tooltipText._text += "%"
		self._tooltipText.makeText()		
		self._tooltipText.displayText()
		#print "string size"
		#print opengl.glGetStringSize(self._value[0:self._selectPos])[0]
		
		#opengl.glDrawStringLeft(self._value)
		if self.hasFocus():
			glTranslate((opengl.glGetStringSize(self._value[0:self._selectPos])[0] - 1)*0.8, -6, 0)
			opengl.glDrawStringLeft('|')
		glPopMatrix()

	def _checkHit(self, x, y):
		x1, y1, w, h = self.getSize()
		w, h = opengl.glGetStringSize("VALUES")
		w -= 25
		h += 10
		return 0 <= x - x1 <= w and 0 <= y - y1 <= h

	def OnMouseMotion(self, x, y):
		return False

	def OnMouseDown(self, x, y, button):
		if self._checkHit(x, y):
			self.setFocus()
			return True
		return False

	def OnKeyChar(self, c):
		self._inCallback = True
		if c == wx.WXK_LEFT:
			self._selectPos -= 1
			self._selectPos = max(0, self._selectPos)
		if c == wx.WXK_RIGHT:
			self._selectPos += 1
			self._selectPos = min(self._selectPos, len(self._value))
		if c == wx.WXK_UP:
			try:
				value = float(self._value)
			except:
				pass
			else:
				value += 1
				self._value = str(value)
				self._callback(self._value)
		if c == wx.WXK_DOWN:
			try:
				value = float(self._value)
			except:
				pass
			else:
				value -= 1
				if value > 0:
					self._value = str(value)
					self._callback(self._value)
		if c == wx.WXK_BACK and self._selectPos > 0:
			self._value = self._value[0:self._selectPos - 1] + self._value[self._selectPos:]
			self._selectPos -= 1
			self._callback(self._value)
		if c == wx.WXK_DELETE:
			self._value = self._value[0:self._selectPos] + self._value[self._selectPos + 1:]
			self._callback(self._value)
		if c == wx.WXK_TAB or c == wx.WXK_NUMPAD_ENTER or c == wx.WXK_RETURN:
			if wx.GetKeyState(wx.WXK_SHIFT):
				self.focusPrevious()
			else:
				self.focusNext()
		if (ord('0') <= c <= ord('9') or c == ord('.')) and len(self._value) < self._maxLen:
			self._value = self._value[0:self._selectPos] + chr(c) + self._value[self._selectPos:]
			self._selectPos += 1
			self._callback(self._value)
		self._inCallback = False

	def setFocus(self):
		self._base._focus = self
		self._selectPos = len(self._value)
		return True

class glCheckbox(glGuiControl):
	def __init__(self, parent, value, pos, callback):
		self._callback = callback
		self._value = value
		self._selectPos = 0
		self._maxLen = 6
		self._inCallback = False
		super(glCheckbox, self).__init__(parent, pos)

	def setValue(self, value):
		if self._inCallback:
			return
		self._value = str(value)

	def getValue(self):
		return self._value

	def getMinSize(self):
		return 20, 20

	def _getPixelPos(self):
		x0, y0, w, h = self.getSize()
		return x0, y0

	def draw(self):
		x, y, w, h = self.getSize()

		glPushMatrix()
		glTranslatef(x, y, 0)

		glColor4ub(0,0,0,255)
		
		if self._value:
			opengl.glDrawTexturedQuad(w-h/2,0, h, h, 28)
		else:
			opengl.glDrawTexturedQuad(w/2-h/2,0, h, h, 29)
		glDisable(GL_TEXTURE_2D)
		glPopMatrix()

	def _checkHit(self, x, y):
		x1, y1, w, h = self.getSize()
		return 0 <= x - x1 <= w and 0 <= y - y1 <= h

	def OnMouseMotion(self, x, y):
		return False

	def OnMouseDown(self, x, y, button):
		if self._checkHit(x, y):
			self._value = not self._value
			return True
		return False

class glSlider(glGuiControl):
	def __init__(self, parent, value, minValue, maxValue, pos, callback):
		super(glSlider, self).__init__(parent, pos)
		self._callback = callback
		self._focus = False
		self._hidden = False
		self._value = value
		self._minValue = minValue
		self._maxValue = maxValue
		self._parent = parent

	def setValue(self, value):
		self._value = value

	def getValue(self):
		if self._value < self._minValue:
			return self._minValue
		if self._value > self._maxValue:
			return self._maxValue
		return self._value

	def setRange(self, minValue, maxValue):
		if maxValue < minValue:
			maxValue = minValue
		self._minValue = minValue
		self._maxValue = maxValue

	def getMinValue(self):
		return self._minValue

	def getMaxValue(self):
		return self._maxValue

	def setHidden(self, value):
		self._hidden = value

	def getMinSize(self):
		return self._base._buttonSize * 0.2 +20, self._base._buttonSize * 4.3

	def _getPixelPos(self):
		x0, y0, w, h = self.getSize()
		minSize = self.getMinSize()
		return x0 + w / 2, (self._parent._parent.GetSize()[1] / 2) - 30
		
		#x0, y0, w, h = self.getSize()
		##print self.getSize()
		#return x0 + w / 2, y0 + h / 2
	def draw(self):
		if self._hidden:
			return

		w, h = self.getMinSize()
		w -= 20
		pos = self._getPixelPos()

		glPushMatrix()
		glTranslatef(pos[0]+15, pos[1], 0)
		glDisable(GL_TEXTURE_2D)
		if self.hasFocus():
			glColor4ub(60,60,60,130)
		else:
			glColor4ub(60,60,60,90)
		glBegin(GL_QUADS)
		glVertex2f( w/4,-h/2)
		glVertex2f(-w/4,-h/2)
		glVertex2f(-w/4, h/2)
		glVertex2f( w/4, h/2)
		glEnd()

		scrollLength = h - w
		if self._maxValue-self._minValue != 0:
			valueNormalized = ((self.getValue()-self._minValue)/(self._maxValue-self._minValue))
		else:
			valueNormalized = 0
		glTranslate(0.0,scrollLength/2,0)
		
		if self._focus:
		#if 0:
			glColor4ub(0,0,0,255)
			glPushMatrix()
			glTranslate(-w/2,opengl.glGetStringSize(str(self._minValue))[1]/2,0)
			#opengl.glDrawStringRight(str(self._minValue))
			glTranslate(0,-scrollLength,0)
			#opengl.glDrawStringRight(str(self._maxValue))
			glTranslate(w,scrollLength-scrollLength*valueNormalized,0)
			#opengl.glDrawStringLeft(str(self.getValue()))
			glPopMatrix()
		glColor4ub(0,0,0,100)
		glTranslate(0.0-15,-scrollLength*valueNormalized,0)
		glBegin(GL_QUADS)
		glVertex2f( w/2,-w/3)
		glVertex2f(-w/2,-w/3)
		glVertex2f(-w/2, w/3)
		glVertex2f( w/2, w/3)
		
		glEnd()
		
		glColor4ub(0,0,0,100)
		glBegin(GL_QUADS)
		glVertex2f( w/2,-w/3)
		glVertex2f(w/2,w/3)
		glVertex2f(w, 0)
		glVertex2f( w/2, -w/3)
		
		glEnd()
		
		glPopMatrix()

	def _checkHit(self, x, y):
		if self._hidden:
			return False
		pos = self._getPixelPos()
		w, h = self.getMinSize()
		return -w/2 <= x - pos[0] <= w/2 and -h/2 <= y - pos[1] <= h/2

	def setFocus(self):
		self._base._focus = self
		return True

	def OnMouseMotion(self, x, y):
		if self.hasFocus():
			w, h = self.getMinSize()
			scrollLength = h - w
			pos = self._getPixelPos()
			self.setValue(int(self._minValue + (self._maxValue - self._minValue) * -(y - pos[1] - scrollLength/2) / scrollLength))
			self._callback()
			return True
		if self._checkHit(x, y):
			self._focus = True
			return True
		self._focus = False
		return False

	def OnMouseDown(self, x, y, button):
		if self._checkHit(x, y):
			self.setFocus()
			self.OnMouseMotion(x, y)
			return True
		return False

	def OnMouseUp(self, x, y):
		if self.hasFocus():
			self._base._focus = None
			return True
		return False

		
class glButtonSetting(glGuiControl):
	def __init__(self, parent, imageID, tooltip, pos, callback, Xnudge = 0, Ynudge = 0, size = None, scaleModifier = None, advanced = False):
		self._buttonSize = size
		self._scaleModifier = scaleModifier
		self._hidden = False
		super(glButtonSetting, self).__init__(parent,pos)
		self._tooltip = tooltip
		self._parent = parent
		self._imageID = imageID
		self._callback = callback
		self._selected = False
		self._focus = False
		self._disabled = False
		self._showExpandArrow = False
		self._progressBar = None
		self._altTooltip = ''
		self._Xnudge = Xnudge
		self._Ynudge = Ynudge
		self._default_Ynudge = Ynudge
		self._glDittoTexture = None
		self._advanced = advanced
		
		self._popup = Tooltip(parent)
		self._popup.Hide()
	def getImageID(self):
		return int(self._imageID)
		
	def setImageID(self, value):
		self._imageID = value
		
	def setSelected(self, value):
		self._selected = value

	def setExpandArrow(self, value):
		self._showExpandArrow = value

	def setHidden(self, value):
		self._hidden = value

	def setDisabled(self, value):
		self._disabled = value

	def setProgressBar(self, value):
		self._progressBar = value

	def getProgressBar(self):
		return self._progressBar

	def setBottomText(self, value):
		self._altTooltip = value

	def getSelected(self):
		return self._selected

	def getMinSize(self):
		if self._hidden:
			return 0, 0
		if self._buttonSize is not None:
			return self._buttonSize, self._buttonSize
		return self._base._buttonSize, self._base._buttonSize

	def _getPixelPos(self):
		windowWidth,windowHeight = self._parent.GetSize()
		x0, y0, w, h = self.getSize()
		x0 = self._Xnudge
		y0 = windowHeight - self._Ynudge
		return x0 + w / 2, y0 + h / 2

	def draw(self):
		if self._parent.settingsOpen == False:
			self._hidden = True
		else:
			self._hidden = False
		
		if self._hidden:
			return
		if self._advanced == True and self._parent.advancedOpen == False:
			return
		if self._advanced == False and self._parent.advancedOpen == False:
			self._Ynudge = self._default_Ynudge - 70
		elif self._advanced == None: #only for the advancedTabButton. No matter what it's position is -70.
			self._Ynudge = self._default_Ynudge - 70
		else:
			self._Ynudge = self._default_Ynudge
			
		cx = (self._imageID % 4) / 4
		cy = int(self._imageID / 4) / 4
		bs = self.getMinSize()[0]
		pos = self._getPixelPos()
		glBindTexture(GL_TEXTURE_2D, self._base._glButtonsTexture)
			

		if self._disabled:
			glColor4ub(128,128,128,128)
		else:
			glColor4ub(255,255,255,156)
			
		scale = 1
		if self._selected:
			scale = 1
			glColor4ub(255,25,0,255)
		elif self._focus:
			#scale = 0.9
			if self._imageID != 21:#not the upper left logo
				#glColor4ub(43,222,115,255)
				glColor4ub(255,255,255,255)
			glColor4ub(150,150,150,255)
		else:
			glColor4ub(180,180,180,255)
		#opengl.glDrawTexturedQuad(self._Xnudge+pos[0]-bs*scale/2, self._Ynudge + pos[1]-bs*scale/2, bs*scale, bs*scale, 0)
		opengl.glDrawTexturedQuad(pos[0]-bs*scale/2, pos[1]-bs*scale/2, bs*scale, bs*scale, self._imageID)
		#print pos[1]-bs*scale/2
		#if self._showExpandArrow:
		#	if self._selected:
		#		opengl.glDrawTexturedQuad(pos[0]+bs*scale/2-bs*scale/4*1.2, pos[1]-bs*scale/2*1.2, bs*scale/4, bs*scale/4, 1)
		#	else:
		#		opengl.glDrawTexturedQuad(pos[0]+bs*scale/2-bs*scale/4*1.2, pos[1]-bs*scale/2*1.2, bs*scale/4, bs*scale/4, 1, 2)
		glPushMatrix()
		glTranslatef(pos[0], pos[1], 0)
		glDisable(GL_TEXTURE_2D)
		if self._focus and 0:
			glTranslatef(0, -0.55*bs*scale, 0)

			glPushMatrix()
			glColor4ub(60,60,60,255)
			glTranslatef(-1, -1, 0)
			opengl.glDrawStringCenter(self._tooltip)
			glTranslatef(0, 2, 0)
			opengl.glDrawStringCenter(self._tooltip)
			glTranslatef(2, 0, 0)
			opengl.glDrawStringCenter(self._tooltip)
			glTranslatef(0, -2, 0)
			opengl.glDrawStringCenter(self._tooltip)
			glPopMatrix()

			glColor4ub(255,255,255,255)
			opengl.glDrawStringCenter(self._tooltip)
			glPopMatrix()
			if 0:
				if self._glDittoTexture is None:
					self._glDittoTexture = opengl.loadGLTexture('import_text2.png')

				glBindTexture(GL_TEXTURE_2D, self._glDittoTexture)
				glEnable(GL_TEXTURE_2D)
				glPushMatrix()
				glColor4f(1,1,1,1)
				glTranslate(180, 160,100)
				glScale(160,49,100)
				glBegin(GL_QUADS)
				glTexCoord2f(1, 0)
				glVertex2f(0,-1)
				glTexCoord2f(0, 0)
				glVertex2f(-1,-1)
				glTexCoord2f(0, 1)
				glVertex2f(-1, 0)
				glTexCoord2f(1, 1)
				glVertex2f(0, 0)
			glEnd()
			glDisable(GL_TEXTURE_2D)
			
		glPopMatrix()



	def _checkHit(self, x, y):
		if self._hidden or self._disabled:
			return False
		bs = self.getMinSize()[0] * self._scaleModifier
		pos = self._getPixelPos()
		return -bs * 0.5 <= x - pos[0] <= bs * 0.5 and -bs * 0.5 <= y - pos[1] <= bs * 0.5
		

	def OnMouseMotion(self, x, y):
		
		#if self._tooltip != '':
		#	return
		if self._checkHit(x, y):
			self._focus = True
			if not self._popup.showing and self._tooltip != '':
				pos = self._getPixelPos()
				self._popup.OnPopupDisplay(self._tooltip, pos[0]-25,pos[1])
			return True
			
		if self._popup.showing:
			self._popup.OnPopupHide(self)
		self._focus = False
		return False

	def OnMouseDown(self, x, y, button):
		#if self._tooltip == '':
		#	return
		if self._checkHit(x, y):
			self._callback(button)
			#self.setSelected(True)
			return True
		return False
		
class glRadioButtonSetting(glButtonSetting):
	def __init__(self, parent, imageID, tooltip, pos, group, callback, Xnudge = 0, Ynudge = 0, size = None, scaleModifier = None, advanced = False):
		super(glRadioButtonSetting, self).__init__(parent, imageID, tooltip, pos, self._onRadioSelect, Xnudge, Ynudge, size, scaleModifier, advanced) #this is the init for glButtonSetting
		
		#self, parent, imageID, tooltip, pos, callback, Xnudge = 0, Ynudge = 0, size = None
		
		self._group = group
		self._radioCallback = callback
		self._group.append(self)
		
	def setSelected(self, value):
		self._selected = value

	def _onRadioSelect(self, button):
		self._base._focus = None
		for ctrl in self._group:
			if ctrl != self:
				ctrl.setSelected(False)
		if self.getSelected():
			pass
			#self.setSelected(False)
		else:
			self.setSelected(True)
		self._radioCallback(button)

class glCameraRadioButtonSetting(glRadioButton):
	def __init__(self, parent, imageID, pos, group, callback, Xnudge = 0, Ynudge = 0, size = None, type = None):
		super(glCameraRadioButtonSetting, self).__init__(parent, imageID, '', '', pos, group, self._onRadioSelect,0,0,1,None,"none")
		self._buttonSize = size
		self._type = type
		self._group = group
		self._radioCallback = callback
		self._group.append(self)
		
		self._Xnudge = Xnudge
		self._Ynudge = Ynudge
		

	def setSelected(self, value):
		self._selected = value

	def _onRadioSelect(self, button):
		self._base._focus = None
		for ctrl in self._group:
			if ctrl != self:
				ctrl.setSelected(False)
		if self.getSelected():
			pass
			#self.setSelected(False)
		else:
			self.setSelected(True)
		self._radioCallback(button)
		
	def getMinSize(self):
		if self._hidden:
			return 0, 0
		if self._buttonSize is not None:
			return self._buttonSize, self._buttonSize
			
		return self._base._buttonSize, self._base._buttonSize
		
	def _getPixelPos(self):
		windowWidth,windowHeight = self._parent.GetSize()
		x0, y0, w, h = self.getSize()
		#print self.getSize()
		#print x0 + w / 2, y0 + h / 2
		return self._Xnudge + windowWidth / 2, windowHeight - self._Ynudge - y0 + h / 2

	def draw(self):
		if self._type == 'camera':
			if self._parent.cameraOpen == False:
				self._hidden = True
			else:
				self._hidden = False
		if self._type == 'viewmode':
			if self._parent.viewmodeOpen == False:
				self._hidden = True
			else:
				self._hidden = False
		
				
		
		
		if self._hidden:
			return

		cx = (self._imageID % 4) / 4
		cy = int(self._imageID / 4) / 4
		bs = self._buttonSize
		pos = self._getPixelPos()

		glBindTexture(GL_TEXTURE_2D, self._base._glButtonsTexture)

		if self._disabled:
			glColor4ub(128,128,128,128)
		else:
			glColor4ub(255,255,255,255)
			
		scale = 1
		if self._selected:
			glColor4ub(255,25,0,255)
		elif self._focus:
			glColor4ub(43,222,115,255)
		else:
			glColor4ub(200,200,200,255)
		#opengl.glDrawTexturedQuad(self._Xnudge+pos[0]-bs*scale/2, self._Ynudge + pos[1]-bs*scale/2, bs*scale, bs*scale, 0)
		opengl.glDrawTexturedQuad(pos[0]-bs*scale/2, pos[1]-bs*scale/2, bs*scale, bs*scale, self._imageID)
		if self._showExpandArrow:
			if self._selected:
				opengl.glDrawTexturedQuad(pos[0]+bs*scale/2-bs*scale/4*1.2, pos[1]-bs*scale/2*1.2, bs*scale/4, bs*scale/4, 1)
			else:
				opengl.glDrawTexturedQuad(pos[0]+bs*scale/2-bs*scale/4*1.2, pos[1]-bs*scale/2*1.2, bs*scale/4, bs*scale/4, 1, 2)
		glPushMatrix()
		glTranslatef(pos[0], pos[1], 0)
		glDisable(GL_TEXTURE_2D)
		if self._focus:
			
			glTranslatef(0, -0.55*bs*scale, 0)
			glPopMatrix()
			
			
		glPopMatrix()
		progress = self._progressBar
		if progress is not None:
			glColor4ub(60,60,60,255)
			opengl.glDrawQuad(pos[0]-bs/2, pos[1]+bs/2, bs, bs / 4)
			glColor4ub(255,255,255,255)
			opengl.glDrawQuad(pos[0]-bs/2+2, pos[1]+bs/2+2, (bs - 5) * progress + 1, bs / 4 - 4)

	def _checkHit(self, x, y):
		if self._hidden or self._disabled:
			return False
		bs = self.getMinSize()[0]
		pos = self._getPixelPos()
		#print -bs * 0.5 <= x - pos[0] <= bs * 0.5 and -bs * 0.5 <= y - pos[1] <= bs * 0.5
		return -bs * 0.5 <= x - pos[0] <= bs * 0.5 and -bs * 0.5 <= y - pos[1] <= bs * 0.5
		
	def OnMouseMotion(self, x, y):
		if self._checkHit(x, y):
			self._focus = True
			return True
			
		self._focus = False
		return False

	def OnMouseDown(self, x, y, button):
		if self._checkHit(x, y):
			self._callback(button)
			return True
		return False
		
class glViewmodeRadioButtonSetting(glRadioButtonSetting):
	def __init__(self, parent, imageID, tooltip, pos, group, callback, Xnudge = 0, Ynudge = 0, size = None, advanced = False):
		super(glViewmodeRadioButtonSetting, self).__init__(parent, imageID, tooltip, pos, group, self._onRadioSelect, Xnudge, Ynudge, size, advanced) #this is the init for glButtonSetting
		
		#self, parent, imageID, tooltip, pos, callback, Xnudge = 0, Ynudge = 0, size = None
		
		self._group = group
		self._radioCallback = callback
		self._group.append(self)

	def setSelected(self, value):
		self._selected = value

	def _onRadioSelect(self, button):
		self._base._focus = None
		for ctrl in self._group:
			if ctrl != self:
				ctrl.setSelected(False)
		if self.getSelected():
			self.setSelected(False)
		else:
			self.setSelected(True)
		self._radioCallback(button)
		
	def draw(self):
		if self._parent.viewmodeOpen == False:
			self._hidden = True
		else:
			self._hidden = False
		
		if self._hidden:
			return
		
		cx = (self._imageID % 4) / 4
		cy = int(self._imageID / 4) / 4
		bs = self.getMinSize()[0] #i don't use this anymore
		pos = self._getPixelPos()
		glBindTexture(GL_TEXTURE_2D, self._base._glButtonsTexture)
			

		if self._disabled:
			glColor4ub(128,128,128,128)
		else:
			glColor4ub(255,255,255,156)
			
		scale = 1
		if self._selected:
			scale = 1.05
			glColor4ub(255,0,0,255)
		elif self._focus:
			#scale = 0.9
			if self._imageID != 21:#not the upper left logo
				#glColor4ub(43,222,115,255)
				glColor4ub(255,255,255,255)
			glColor4ub(200,200,200,255)
		else:
			glColor4ub(200,200,200,255)
		#opengl.glDrawTexturedQuad(self._Xnudge+pos[0]-bs*scale/2, self._Ynudge + pos[1]-bs*scale/2, bs*scale, bs*scale, 0)
		opengl.glDrawTexturedQuad(pos[0]-bs*scale/2, pos[1]-bs*scale/2, bs*scale, bs*scale, self._imageID)
		#print pos[1]-bs*scale/2
		#if self._showExpandArrow:
		#	if self._selected:
		#		opengl.glDrawTexturedQuad(pos[0]+bs*scale/2-bs*scale/4*1.2, pos[1]-bs*scale/2*1.2, bs*scale/4, bs*scale/4, 1)
		#	else:
		#		opengl.glDrawTexturedQuad(pos[0]+bs*scale/2-bs*scale/4*1.2, pos[1]-bs*scale/2*1.2, bs*scale/4, bs*scale/4, 1, 2)
		glPushMatrix()
		glTranslatef(pos[0], pos[1], 0)
		glDisable(GL_TEXTURE_2D)
		if self._focus:
			glTranslatef(0, -0.55*bs*scale, 0)

			glPushMatrix()
			glColor4ub(60,60,60,255)
			glTranslatef(-1, -1, 0)
			opengl.glDrawStringCenter(self._tooltip)
			glTranslatef(0, 2, 0)
			opengl.glDrawStringCenter(self._tooltip)
			glTranslatef(2, 0, 0)
			opengl.glDrawStringCenter(self._tooltip)
			glTranslatef(0, -2, 0)
			opengl.glDrawStringCenter(self._tooltip)
			glPopMatrix()

			glColor4ub(255,255,255,255)
			opengl.glDrawStringCenter(self._tooltip)
			glPopMatrix()
			if 0:
				if self._glDittoTexture is None:
					self._glDittoTexture = opengl.loadGLTexture('import_text2.png')

				glBindTexture(GL_TEXTURE_2D, self._glDittoTexture)
				glEnable(GL_TEXTURE_2D)
				glPushMatrix()
				glColor4f(1,1,1,1)
				glTranslate(180, 160,100)
				glScale(160,49,100)
				glBegin(GL_QUADS)
				glTexCoord2f(1, 0)
				glVertex2f(0,-1)
				glTexCoord2f(0, 0)
				glVertex2f(-1,-1)
				glTexCoord2f(0, 1)
				glVertex2f(-1, 0)
				glTexCoord2f(1, 1)
				glVertex2f(0, 0)
			glEnd()
			glDisable(GL_TEXTURE_2D)
			
		glPopMatrix()

class glTextLabelSetting(glGuiControl):
	def __init__(self, parent, tooltip, pos, Xnudge = 0, Ynudge = 0, fontSize = 12, advanced = False, colour = (50,50,50)):
		self._fontSize = fontSize
		#self._buttonSize = size
		self._hidden = False
		self._advanced = advanced
		super(glTextLabelSetting, self).__init__(parent,pos)
		self._tooltip = tooltip
		self._parent = parent
		#self._callback = callback
		self._selected = False
		self._focus = False
		self._disabled = False
		self._showExpandArrow = False
		self._progressBar = None
		self._altTooltip = ''
		self._Xnudge = Xnudge
		self._Ynudge = Ynudge
		self._default_Ynudge = Ynudge
		self._glDittoTexture = None
		self._colour = colour
		self.loaded = False
		
		self._tooltipText = tooltipText.tooltipText(200, 200, self._tooltip, "HelveticaNeueLTStd-Lt.otf", self._fontSize, self._colour) #(43,182,115)
		self._tooltipText.makeText()
		
	def setTooltip(self, value):
		self._tooltip = value
	
	def getTooltip(self):
		return self._tooltip
		
	def setSelected(self, value):
		self._selected = value

	def setExpandArrow(self, value):
		self._showExpandArrow = value

	def setHidden(self, value):
		self._hidden = value

	def setDisabled(self, value):
		self._disabled = value

	def setProgressBar(self, value):
		self._progressBar = value

	def getProgressBar(self):
		return self._progressBar

	def setBottomText(self, value):
		self._altTooltip = value

	def getSelected(self):
		return self._selected

	def getMinSize(self):
		if self._hidden:
			return 0, 0
		#if self._buttonSize is not None:
		#	return self._buttonSize, self._buttonSize
		return self._base._buttonSize, self._base._buttonSize

	def _getPixelPos(self):
		windowWidth,windowHeight = self._parent.GetSize()
		x0, y0, w, h = self.getSize()
		x0 = self._Xnudge
		y0 = windowHeight - self._Ynudge
		return x0 + w / 2, y0 + h / 2

	def draw(self):
		if self._parent.settingsOpen == False:
			self._hidden = True
		else:
			self._hidden = False
		if self._hidden:
			return
			
		#print self._parent.advancedOpen
		#print self._advanced5
		if self._advanced == True and self._parent.advancedOpen == False:
			return
		if self._advanced == False and self._parent.advancedOpen == False:
			self._Ynudge = self._default_Ynudge - 70
		else:
			self._Ynudge = self._default_Ynudge
		#cx = (self._imageID % 4) / 4
		#cy = int(self._imageID / 4) / 4
		bs = self.getMinSize()[0] #i don't use this anymore
		pos = self._getPixelPos()
		#glBindTexture(GL_TEXTURE_2D, self._base._glButtonsTexture)
			

		if self._disabled:
			glColor4ub(128,128,128,128)
		else:
			glColor4ub(255,255,255,255)
			
		#scale = 0.8
		#if self._selected:
		#	scale = 0.85
		#	glColor4ub(255,25,0,255)
		#elif self._focus:
			#scale = 0.9
		#	if self._imageID != 21: #not the upper left logo 
		#		glColor4ub(43,222,115,255)

		#opengl.glDrawTexturedQuad(self._Xnudge+pos[0]-bs*scale/2, self._Ynudge + pos[1]-bs*scale/2, bs*scale, bs*scale, 0)
		#opengl.glDrawTexturedQuad(pos[0]-64*scale/2, pos[1]-64*scale/2, 64*scale, 64*scale, self._imageID)
		#print pos[1]-bs*scale/2
		glEnd()
		glPushMatrix()
		#glTranslatef(pos[0], pos[1], 0)
		glDisable(GL_TEXTURE_2D)
		#glColor4ub(255,255,255,255)
		#if self.loaded == False:
		#	self.abc = testtext.font_data("HelveticaNeueLTStd-Lt.otf",self._fontSize)
		#	self.loaded = True
		
		windowWidth,windowHeight = self._parent.GetSize()
		#self.abc.glPrint(500,500,str(self.bla))
		#self.abc.glPrint(pos[0],windowHeight-pos[1],self._tooltip)

		self._tooltipText._x = pos[0]
		self._tooltipText._y = pos[1]
		self._tooltipText._text = self._tooltip
		
		self._tooltipText.makeText()
		self._tooltipText.displayText()

		
		if self._focus:
			glTranslatef(0, -0.55*bs*scale, 0)

			glPushMatrix()
			glColor4ub(60,60,60,255)
			glTranslatef(-1, -1, 0)
			opengl.glDrawStringCenter(self._tooltip)
			glTranslatef(0, 2, 0)
			opengl.glDrawStringCenter(self._tooltip)
			glTranslatef(2, 0, 0)
			opengl.glDrawStringCenter(self._tooltip)
			glTranslatef(0, -2, 0)
			opengl.glDrawStringCenter(self._tooltip)
			glPopMatrix()

			glColor4ub(255,255,255,255)
			opengl.glDrawStringCenter(self._tooltip)
			glPopMatrix()
			if self._glDittoTexture is None:
				self._glDittoTexture = opengl.loadGLTexture('import_text2.png')

			glBindTexture(GL_TEXTURE_2D, self._glDittoTexture)
			glEnable(GL_TEXTURE_2D)
			glPushMatrix()
			glColor4f(1,1,1,1)
			glTranslate(180, 160,100)
			glScale(160,49,100)
			glBegin(GL_QUADS)
			glTexCoord2f(1, 0)
			glVertex2f(0,-1)
			glTexCoord2f(0, 0)
			glVertex2f(-1,-1)
			glTexCoord2f(0, 1)
			glVertex2f(-1, 0)
			glTexCoord2f(1, 1)
			glVertex2f(0, 0)
			glEnd()
			glDisable(GL_TEXTURE_2D)
			
		glPopMatrix()
		progress = self._progressBar
		if progress is not None:
			glColor4ub(60,60,60,255)
			opengl.glDrawQuad(pos[0]-bs/2, pos[1]+bs/2, bs, bs / 4)
			glColor4ub(255,255,255,255)
			opengl.glDrawQuad(pos[0]-bs/2+2, pos[1]+bs/2+2, (bs - 5) * progress + 1, bs / 4 - 4)
		elif len(self._altTooltip) > 0:
			glPushMatrix()
			glTranslatef(pos[0], pos[1], 0)
			glTranslatef(0.6*bs*scale, 0, 0)

			glPushMatrix()
			glColor4ub(60,60,60,255)
			glTranslatef(-1, -1, 0)
			opengl.glDrawStringLeft(self._altTooltip)
			glTranslatef(0, 2, 0)
			opengl.glDrawStringLeft(self._altTooltip)
			glTranslatef(2, 0, 0)
			opengl.glDrawStringLeft(self._altTooltip)
			glTranslatef(0, -2, 0)
			opengl.glDrawStringLeft(self._altTooltip)
			glPopMatrix()

			glColor4ub(255,255,0,255)
			opengl.glDrawStringLeft(self._altTooltip)
			glPopMatrix()

	def _checkHit(self, x, y):
		if self._hidden or self._disabled:
			return False
		bs = self.getMinSize()[0]
		pos = self._getPixelPos()
		return -bs * 0.5 <= x - pos[0] <= bs * 0.5 and -bs * 0.5 <= y - pos[1] <= bs * 0.5

	def OnMouseMotion(self, x, y):
		if self._tooltip != '':
			return
		if self._checkHit(x, y):
			self._focus = True
			return True
		self._focus = False
		return False

	def OnMouseDown(self, x, y, button):
		if self._tooltip != '':
			return
		if self._checkHit(x, y):
			self._callback(button)
			#self.setSelected(True)
			return True
		return False
		