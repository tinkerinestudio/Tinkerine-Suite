from __future__ import absolute_import

import wx

from Cura.gui import configBase
from Cura.util import validators
from Cura.util import sliceEngine
from Cura.util import profile
class sliceMenu(wx.Frame):
	"Expert configuration window"
	def __init__(self, sceneView):
		super(sliceMenu, self).__init__(None, title='Slice Menu', style=wx.DEFAULT_DIALOG_STYLE)
		
		wx.EVT_CLOSE(self, self.OnClose)
		self.panel = configBase.configPanelBase(self)
		
		self.sceneView = sceneView
        #self._scene.objects()
		left, right, self.main = self.panel.CreateConfigPanel(self)
		self.hidden = False
		self._slicer = sliceEngine.Slicer(self._updateSliceProgress)
        
		self.advancedList = []
		
		self.changeMachineButton = wx.Button(left, -1, 'Litto')
		left.GetSizer().Add(self.changeMachineButton, (left.GetSizer().GetRows(), 3))
		self.Bind(wx.EVT_BUTTON, lambda e: self.changeMachine(), self.changeMachineButton)
		
		configBase.TitleRow(left, "Print Settings")

		c = configBase.SettingRow(left, "Filament Diameter", 'filament_diameter', '1.75', 'decription of filament diameter')
		validators.validInt(c, 0)
		
		
		c = configBase.TitleRow(left, "Advanced Settings")
		self.advancedList.append(c)

		c = configBase.SettingRow(left, "Print Speed", 'print_speed', '0', 'decription of print speed')
		validators.validInt(c, 0)
		self.advancedList.append(c)
		
		c = configBase.SettingRow(left, "Print Temperature", 'print_temperature', '190', 'Degrees C')
		validators.validInt(c, 0)
		self.advancedList.append(c)
		
		c = configBase.SettingRow(left, "Enable ym", 'support', ['None', 'Exterior Only', 'Everywhere'], 'Hah! You better have BURN HEAL!')
		self.advancedList.append(c)
		
		c = configBase.SettingRow(left, "Add raft", 'enable_raft', True, 'the ~~~R~~~~~~~~~~ word')
		self.advancedList.append(c)
		#validators.validInt(c, 0, 100)
		#c = configBase.SettingRow(left, "Fan speed max (%)", 'fan_speed_max', '100', 'When the fan is turned on, it is enabled at this speed setting. If cool slows down the layer, the fan is adjusted between the min and max speed. Maximal fan speed is used if the layer is slowed down due to cooling by more then 200%.')
		#validators.validInt(c, 0, 100)


		#configBase.TitleRow(left, "Support")
		#c = configBase.SettingRow(left, "Material amount (%)", 'support_rate', '100', 'Amount of material used for support, less material gives a weaker support structure which is easier to remove.')
		#validators.validFloat(c, 0.0)
		#c = configBase.SettingRow(left, "Distance from object (mm)", 'support_distance', '0.5', 'Distance between the support structure and the object. Empty gap in which no support structure is printed.')
		#validators.validFloat(c, 0.0)

		c = configBase.TitleRow(right, "")
		self.advancedList.append(c)
		
		c = configBase.SettingRow(right, "Infill %", 'fill_density', '10', 'INFILL!')
		self.advancedList.append(c)
		
		c = configBase.SettingRow(right, "Wall Thickness", 'wall_thickness', '0.3', 'Wall Thickness in mm')
		validators.validFloat(c, 0.0)
		self.advancedList.append(c)
		
		self.okButton = wx.Button(right, -1, 'Slice')
		right.GetSizer().Add(self.okButton, (right.GetSizer().GetRows(), 1))
		self.Bind(wx.EVT_BUTTON, lambda e: self.RunSlice(), self.okButton)
        
		self.hideButton = wx.Button(right, -1, 'Hide')
		right.GetSizer().Add(self.hideButton, (right.GetSizer().GetRows()+1, 1))
		self.Bind(wx.EVT_BUTTON, lambda e: self.HideAdvanced(), self.hideButton)
		self.main.Fit()
		self.Fit()
        
	def changeMachine(self):
		if self.changeMachineButton.GetLabel() == 'Litto':
			self.changeMachineButton.SetLabel("Ditto+")
			profile.putPreference('machine_width', '210')
			profile.putPreference('machine_depth', '185')
			profile.putPreference('machine_height', '230')
		else:
			self.changeMachineButton.SetLabel("Litto")
			profile.putPreference('machine_width', '130')
			profile.putPreference('machine_depth', '120')
			profile.putPreference('machine_height', '175')
		self.sceneView.sceneUpdated()
		self.sceneView.updateProfileToControls()
        
	def HideAdvanced(self):
		#self.hideButton.Hide()  
		#print self.advancedList
		if self.hidden == False:
			for c in self.advancedList:
				c.HideSelf()
			#self.c.HideSelf()
			#self.c2.HideSelf()
			self.hidden = True
			self.main.Fit()
			self.Fit()
		else:
			for c in self.advancedList:
				c.ShowSelf()
			#self.c.ShowSelf()
			#self.c2.ShowSelf()
			self.hidden = False
			self.main.Fit()
			self.Fit()
	def RunSlice(self):
		self._slicer.runSlicer(self.sceneView._scene.objects(), "goodjob.g", self.sceneView)
		self.Destroy()

	def OnClose(self, e):
		#self._slicer.runSlicer(self.sceneView._scene.objects(), "goodjob.gcode", self.sceneView)
		self.Destroy()
	def _updateSliceProgress(self, progressValue, ready):
		if not ready:
			if self.printButton.getProgressBar() is not None and progressValue >= 0.0 and abs(self.printButton.getProgressBar() - progressValue) < 0.01:
				return
		self.printButton.setDisabled(not ready)
		if progressValue >= 0.0:
			self.printButton.setProgressBar(progressValue)
		else:
			self.printButton.setProgressBar(None)
		if self._gcode is not None:
			self._gcode = None
			for layerVBOlist in self._gcodeVBOs:
				for vbo in layerVBOlist:
					self.glReleaseList.append(vbo)
			self._gcodeVBOs = []
		if ready:
			self.printButton.setProgressBar(None)
			cost = self._slicer.getFilamentCost()
			if cost is not None:
				self.printButton.setBottomText('%s\n%s\n%s' % (self._slicer.getPrintTime(), self._slicer.getFilamentAmount(), cost))
			else:
				self.printButton.setBottomText('%s\n%s' % (self._slicer.getPrintTime(), self._slicer.getFilamentAmount()))
			self._gcode = gcodeInterpreter.gcode()
			self._gcodeFilename = self._slicer.getGCodeFilename()
		else:
			self.printButton.setBottomText('')
		self.QueueRefresh()