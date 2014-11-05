from __future__ import absolute_import
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import os
import webbrowser

from Cura.gui import configBase
from Cura.gui import expertConfig
from Cura.gui import alterationPanel
from Cura.gui import pluginPanel
from Cura.gui import preferencesDialog
from Cura.gui import configWizard
from Cura.gui import firmwareInstall
from Cura.gui import sliceProgessPanel
from Cura.gui import simpleMode
from Cura.gui import sceneView
#from Cura.gui.tools import batchRun
from Cura.gui.util import dropTarget
from Cura.gui.tools import minecraftImport
from Cura.util import validators
from Cura.util import profile
from Cura.util import version
from Cura.util import meshLoader
from Cura.util import machineCom
from Cura.util import sliceEngine

class mainWindow(wx.Frame):
	def __init__(self):
		super(mainWindow, self).__init__(None, title='Cura - ' + version.getVersion())
		#super(mainWindow, self).__init__(None, title='Cura - ' + version.getVersion(),style=wx.DEFAULT_FRAME_STYLE & wx.NO_BORDER & ~wx.SYSTEM_MENU)

		self.extruderCount = int(profile.getPreference('extruder_amount'))

		wx.EVT_CLOSE(self, self.OnClose)

		self.SetDropTarget(dropTarget.FileDropTarget(self.OnDropFiles, meshLoader.loadSupportedExtensions()))

		self.normalModeOnlyItems = []

		mruFile = os.path.join(profile.getBasePath(), 'mru_filelist.ini')
		self.config = wx.FileConfig(appName="Cura", 
						localFilename=mruFile,
						style=wx.CONFIG_USE_LOCAL_FILE)
						
		self.ID_MRU_MODEL1, self.ID_MRU_MODEL2, self.ID_MRU_MODEL3, self.ID_MRU_MODEL4, self.ID_MRU_MODEL5, self.ID_MRU_MODEL6, self.ID_MRU_MODEL7, self.ID_MRU_MODEL8, self.ID_MRU_MODEL9, self.ID_MRU_MODEL10 = [wx.NewId() for line in xrange(10)]
		self.modelFileHistory = wx.FileHistory(10, self.ID_MRU_MODEL1)
		self.config.SetPath("/ModelMRU")
		self.modelFileHistory.Load(self.config)

		self.ID_MRU_PROFILE1, self.ID_MRU_PROFILE2, self.ID_MRU_PROFILE3, self.ID_MRU_PROFILE4, self.ID_MRU_PROFILE5, self.ID_MRU_PROFILE6, self.ID_MRU_PROFILE7, self.ID_MRU_PROFILE8, self.ID_MRU_PROFILE9, self.ID_MRU_PROFILE10 = [wx.NewId() for line in xrange(10)]
		self.profileFileHistory = wx.FileHistory(10, self.ID_MRU_PROFILE1)
		self.config.SetPath("/ProfileMRU")
		self.profileFileHistory.Load(self.config)

		self.menubar = wx.MenuBar()
		self.fileMenu = wx.Menu()
		i = self.fileMenu.Append(-1, 'Load model file...\tCTRL+L')
		self.Bind(wx.EVT_MENU, lambda e: self.scene.showLoadModel(), i)
		i = self.fileMenu.Append(-1, 'Save model...\tCTRL+S')
		self.Bind(wx.EVT_MENU, lambda e: self.scene.showSaveModel(), i)
		i = self.fileMenu.Append(-1, 'Clear platform')
		self.Bind(wx.EVT_MENU, lambda e: self.scene.OnDeleteAll(e), i)

		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(-1, 'Print...\tCTRL+P')
		self.Bind(wx.EVT_MENU, lambda e: self.scene.showPrintWindow(), i)
		i = self.fileMenu.Append(-1, 'Save GCode...')
		self.Bind(wx.EVT_MENU, lambda e: self.scene.showSaveGCode(), i)
		i = self.fileMenu.Append(-1, 'Show slice engine log...')
		self.Bind(wx.EVT_MENU, lambda e: self.scene._showSliceLog(), i)

		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(-1, 'Open Profile...')
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnLoadProfile, i)
		i = self.fileMenu.Append(-1, 'Save Profile...')
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnSaveProfile, i)
		i = self.fileMenu.Append(-1, 'Load Profile from GCode...')
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnLoadProfileFromGcode, i)
		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(-1, 'Reset Profile to default')
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnResetProfile, i)

		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(-1, 'Preferences...\tCTRL+,')
		self.Bind(wx.EVT_MENU, self.OnPreferences, i)
		self.fileMenu.AppendSeparator()

		# Model MRU list
		modelHistoryMenu = wx.Menu()
		self.fileMenu.AppendMenu(wx.NewId(), "&Recent Model Files", modelHistoryMenu)
		self.modelFileHistory.UseMenu(modelHistoryMenu)
		self.modelFileHistory.AddFilesToMenu()
		self.Bind(wx.EVT_MENU_RANGE, self.OnModelMRU, id=self.ID_MRU_MODEL1, id2=self.ID_MRU_MODEL10)

		# Profle MRU list
		profileHistoryMenu = wx.Menu()
		self.fileMenu.AppendMenu(wx.NewId(), "&Recent Profile Files", profileHistoryMenu)
		self.profileFileHistory.UseMenu(profileHistoryMenu)
		self.profileFileHistory.AddFilesToMenu()
		self.Bind(wx.EVT_MENU_RANGE, self.OnProfileMRU, id=self.ID_MRU_PROFILE1, id2=self.ID_MRU_PROFILE10)
		
		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(wx.ID_EXIT, 'Quit')
		self.Bind(wx.EVT_MENU, self.OnQuit, i)
		self.menubar.Append(self.fileMenu, '&File')

		toolsMenu = wx.Menu()
		i = toolsMenu.Append(-1, 'Switch to quickprint...')
		self.switchToQuickprintMenuItem = i
		self.Bind(wx.EVT_MENU, self.OnSimpleSwitch, i)
		i = toolsMenu.Append(-1, 'Switch to full settings...')
		self.switchToNormalMenuItem = i
		self.Bind(wx.EVT_MENU, self.OnNormalSwitch, i)
		toolsMenu.AppendSeparator()
		#i = toolsMenu.Append(-1, 'Batch run...')
		#self.Bind(wx.EVT_MENU, self.OnBatchRun, i)
		#self.normalModeOnlyItems.append(i)
		if minecraftImport.hasMinecraft():
			i = toolsMenu.Append(-1, 'Minecraft import...')
			self.Bind(wx.EVT_MENU, self.OnMinecraftImport, i)
		self.menubar.Append(toolsMenu, 'Tools')

		expertMenu = wx.Menu()
		i = expertMenu.Append(-1, 'Open expert settings...')
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnExpertOpen, i)
		expertMenu.AppendSeparator()
		if firmwareInstall.getDefaultFirmware() is not None:
			i = expertMenu.Append(-1, 'Install default Marlin firmware')
			self.Bind(wx.EVT_MENU, self.OnDefaultMarlinFirmware, i)
		i = expertMenu.Append(-1, 'Install custom firmware')
		self.Bind(wx.EVT_MENU, self.OnCustomFirmware, i)
		expertMenu.AppendSeparator()
		i = expertMenu.Append(-1, 'Run first run wizard...')
		self.Bind(wx.EVT_MENU, self.OnFirstRunWizard, i)
		i = expertMenu.Append(-1, 'Run bed leveling wizard...')
		self.Bind(wx.EVT_MENU, self.OnBedLevelWizard, i)
		if self.extruderCount > 1:
			i = expertMenu.Append(-1, 'Run head offset wizard...')
			self.Bind(wx.EVT_MENU, self.OnHeadOffsetWizard, i)
		self.menubar.Append(expertMenu, 'Expert')

		helpMenu = wx.Menu()
		i = helpMenu.Append(-1, 'Online documentation...')
		self.Bind(wx.EVT_MENU, lambda e: webbrowser.open('http://daid.github.com/Cura'), i)
		i = helpMenu.Append(-1, 'Report a problem...')
		self.Bind(wx.EVT_MENU, lambda e: webbrowser.open('https://github.com/daid/Cura/issues'), i)
		i = helpMenu.Append(-1, 'Check for update...')
		self.Bind(wx.EVT_MENU, self.OnCheckForUpdate, i)
		i = helpMenu.Append(-1, 'About Cura...')
		self.Bind(wx.EVT_MENU, self.OnAbout, i)
		self.menubar.Append(helpMenu, 'Help')
		self.SetMenuBar(self.menubar)
        

		self.splitter = wx.SplitterWindow(self, style = wx.SP_3D | wx.SP_LIVE_UPDATE)
		self.splitter2 = wx.SplitterWindow(self.splitter, style = wx.SP_3D | wx.SP_LIVE_UPDATE)

        
		self.leftPane = wx.Panel(self.splitter2, style=wx.BORDER_NONE)
		self.rightPane = wx.Panel(self.splitter, style=wx.BORDER_NONE)
		self.splitter.Bind(wx.EVT_SPLITTER_DCLICK, lambda evt: evt.Veto())

		##Gui components##
		#self.simpleSettingsPanel = simpleMode.simpleModePanel(self.leftPane, lambda : self.scene.sceneUpdated())
		self.normalSettingsPanel = normalSettingsPanel(self.leftPane, lambda : self.scene.sceneUpdated())
		self.abuttonthing = wx.Button(self.splitter2,2,"<", size=(15,100))
		self.abuttonthing.Bind(wx.EVT_BUTTON,self.changeMode)
		#self.abuttonthing = wx.Button(self.splitter2,2,">")
		
		
		self.leftSizer = wx.BoxSizer(wx.HORIZONTAL)
		#self.leftSizer.Add(self.abuttonthing,1)
		#self.leftSizer.Add(self.simpleSettingsPanel)
		self.leftSizer.Add(self.normalSettingsPanel, 1, wx.EXPAND)
		self.leftPane.SetSizer(self.leftSizer)
        
		self.splitter2.SplitVertically(self.abuttonthing, self.leftPane)
		self.splitter2.SetSashGravity(0)
		self.splitter2.SetSashPosition(10, True)
        
		#Preview window
		self.scene = sceneView.SceneView(self.rightPane)

		#Main sizer, to position the preview window, buttons and tab control
		sizer = wx.BoxSizer()
		self.rightPane.SetSizer(sizer)
		sizer.Add(self.scene, 1, flag=wx.EXPAND)

		# Main window sizer
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(sizer)
		sizer.Add(self.splitter, 1, wx.EXPAND)
		sizer.Layout()
		self.sizer = sizer

		#self.updateProfileToControls()

		self.SetBackgroundColour(self.normalSettingsPanel.GetBackgroundColour())

		#self.simpleSettingsPanel.Show(False)
		self.normalSettingsPanel.Show(False)

		# Set default window size & position
		self.SetSize((wx.Display().GetClientArea().GetWidth()/2,wx.Display().GetClientArea().GetHeight()/2))
		self.Centre()
		self.splitter.SetSashGravity(1)
		# Restore the window position, size & state from the preferences file
		try:
			if profile.getPreference('window_maximized') == 'True':
				self.Maximize(True)
			else:
				posx = int(profile.getPreference('window_pos_x'))
				posy = int(profile.getPreference('window_pos_y'))
				width = int(profile.getPreference('window_width'))
				height = int(profile.getPreference('window_height'))
				if posx > 0 or posy > 0:
					self.SetPosition((posx,posy))
				if width > 0 and height > 0:
					self.SetSize((width,height))
				
			self.normalSashPos = int(profile.getPreference('window_normal_sash'))
		except:
			self.normalSashPos = 0
			self.Maximize(True)
		#if self.normalSashPos < self.normalSettingsPanel.printPanel.GetBestSize()[0] + 5:
		#	self.normalSashPos = self.normalSettingsPanel.printPanel.GetBestSize()[0] + 5

		self.splitter.SplitVertically(self.rightPane, self.splitter2, self.normalSashPos)

		if wx.Display.GetFromPoint(self.GetPosition()) < 0:
			self.Centre()
		if wx.Display.GetFromPoint((self.GetPositionTuple()[0] + self.GetSizeTuple()[1], self.GetPositionTuple()[1] + self.GetSizeTuple()[1])) < 0:
			self.Centre()
		if wx.Display.GetFromPoint(self.GetPosition()) < 0:
			self.SetSize((800,600))
			self.Centre()

		self.updateSliceMode()
	def changeMode(self,e):
		isSimple = profile.getPreference('startMode') == 'Simple'
		if isSimple:
			self.OnNormalSwitch(e)
			self.abuttonthing.SetLabel(">")
		else:
			self.OnSimpleSwitch(e)
			self.abuttonthing.SetLabel("<")

	def updateSliceMode(self):
		isSimple = profile.getPreference('startMode') == 'Simple'

		self.normalSettingsPanel.Show(not isSimple)
		#self.simpleSettingsPanel.Show(isSimple)
		self.leftPane.Layout()

		for i in self.normalModeOnlyItems:
			i.Enable(not isSimple)
		self.switchToQuickprintMenuItem.Enable(not isSimple)
		self.switchToNormalMenuItem.Enable(isSimple)
		(width, height) = self.GetSize()

		# Set splitter sash position & size
		if isSimple:
			# Save normal mode sash
			self.normalSashPos = self.splitter.GetSashPosition()
			
			# Change location of sash to width of quick mode pane 
			#(width, height) = self.simpleSettingsPanel.GetSizer().GetSize() 

			self.splitter.SetSashPosition(width-60, True)
			# Disable sash
			self.splitter.SetSashSize(4)
		else:
			self.splitter.SetSashPosition(width-300, True)
			#print(self.normalSashPos)
			# Enabled sash
			self.splitter.SetSashSize(4)
		self.scene.updateProfileToControls()
								
	def OnPreferences(self, e):
		#(width, height) = self.simpleSettingsPanel.GetSizer().GetSize() 
		#width = int(profile.getPreference('window_width'))
		#self.splitter.SetSashPosition(width)
		prefDialog = preferencesDialog.preferencesDialog(self)
		prefDialog.Centre()
		prefDialog.Show()
		#self.blarg.OnSlice(e)
		
		
	def OnDropFiles(self, files):
		if len(files) > 0:
			profile.setPluginConfig([])
			self.updateProfileToControls()
		self.scene.loadScene(files)

	def OnModelMRU(self, e):
		fileNum = e.GetId() - self.ID_MRU_MODEL1
		path = self.modelFileHistory.GetHistoryFile(fileNum)
		# Update Model MRU
		self.modelFileHistory.AddFileToHistory(path)  # move up the list
		self.config.SetPath("/ModelMRU")
		self.modelFileHistory.Save(self.config)
		self.config.Flush()
		# Load Model
		profile.putPreference('lastFile', path)
		filelist = [ path ]
		self.scene.loadScene(filelist)

	def addToModelMRU(self, file):
		self.modelFileHistory.AddFileToHistory(file)
		self.config.SetPath("/ModelMRU")
		self.modelFileHistory.Save(self.config)
		self.config.Flush()
	
	def OnProfileMRU(self, e):
		fileNum = e.GetId() - self.ID_MRU_PROFILE1
		path = self.profileFileHistory.GetHistoryFile(fileNum)
		# Update Profile MRU
		self.profileFileHistory.AddFileToHistory(path)  # move up the list
		self.config.SetPath("/ProfileMRU")
		self.profileFileHistory.Save(self.config)
		self.config.Flush()
		# Load Profile	
		profile.loadProfile(path)
		self.updateProfileToControls()

	def addToProfileMRU(self, file):
		self.profileFileHistory.AddFileToHistory(file)
		self.config.SetPath("/ProfileMRU")
		self.profileFileHistory.Save(self.config)
		self.config.Flush()			

	def updateProfileToControls(self):
		self.scene.updateProfileToControls()
		self.normalSettingsPanel.updateProfileToControls()
		#self.simpleSettingsPanel.updateProfileToControls()

	def OnLoadProfile(self, e):
		dlg=wx.FileDialog(self, "Select profile file to load", os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard("ini files (*.ini)|*.ini")
		if dlg.ShowModal() == wx.ID_OK:
			profileFile = dlg.GetPath()
			profile.loadProfile(profileFile)
			self.updateProfileToControls()

			# Update the Profile MRU
			self.addToProfileMRU(profileFile)
		dlg.Destroy()

	def OnLoadProfileFromGcode(self, e):
		dlg=wx.FileDialog(self, "Select gcode file to load profile from", os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard("gcode files (*.gcode)|*.gcode;*.g")
		if dlg.ShowModal() == wx.ID_OK:
			gcodeFile = dlg.GetPath()
			f = open(gcodeFile, 'r')
			hasProfile = False
			for line in f:
				if line.startswith(';CURA_PROFILE_STRING:'):
					profile.loadProfileFromString(line[line.find(':')+1:].strip())
					hasProfile = True
			if hasProfile:
				self.updateProfileToControls()
			else:
				wx.MessageBox('No profile found in GCode file.\nThis feature only works with GCode files made by Cura 12.07 or newer.', 'Profile load error', wx.OK | wx.ICON_INFORMATION)
		dlg.Destroy()

	def OnSaveProfile(self, e):
		dlg=wx.FileDialog(self, "Select profile file to save", os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_SAVE)
		dlg.SetWildcard("ini files (*.ini)|*.ini")
		if dlg.ShowModal() == wx.ID_OK:
			profileFile = dlg.GetPath()
			profile.saveProfile(profileFile)
		dlg.Destroy()

	def OnResetProfile(self, e):
		dlg = wx.MessageDialog(self, 'This will reset all profile settings to defaults.\nUnless you have saved your current profile, all settings will be lost!\nDo you really want to reset?', 'Profile reset', wx.YES_NO | wx.ICON_QUESTION)
		result = dlg.ShowModal() == wx.ID_YES
		dlg.Destroy()
		if result:
			profile.resetProfile()
			self.updateProfileToControls()

	def OnBatchRun(self, e):
		br = batchRun.batchRunWindow(self)
		br.Centre()
		br.Show(True)

	def OnSimpleSwitch(self, e):
		profile.putPreference('startMode', 'Simple')
		self.updateSliceMode()

	def OnNormalSwitch(self, e):
		profile.putPreference('startMode', 'Normal')
		self.updateSliceMode()

	def OnDefaultMarlinFirmware(self, e):
		firmwareInstall.InstallFirmware()

	def OnCustomFirmware(self, e):
		dlg=wx.FileDialog(self, "Open firmware to upload", os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard("HEX file (*.hex)|*.hex;*.HEX")
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetPath()
			if not(os.path.exists(filename)):
				return
			#For some reason my Ubuntu 10.10 crashes here.
			self.port in machineCom.serialList(True)
			firmwareInstall.InstallFirmware(filename)

	def OnFirstRunWizard(self, e):
		configWizard.configWizard()
		self.updateProfileToControls()

	def OnBedLevelWizard(self, e):
		configWizard.bedLevelWizard()

	def OnHeadOffsetWizard(self, e):
		configWizard.headOffsetWizard()

	def OnExpertOpen(self, e):
		ecw = expertConfig.expertConfigWindow()
		ecw.Centre()
		ecw.Show(True)

	def OnMinecraftImport(self, e):
		mi = minecraftImport.minecraftImportWindow(self)
		mi.Centre()
		mi.Show(True)

	def OnCheckForUpdate(self, e):
		newVersion = version.checkForNewerVersion()
		if newVersion is not None:
			if wx.MessageBox('A new version of Cura is available, would you like to download?', 'New version available', wx.YES_NO | wx.ICON_INFORMATION) == wx.YES:
				webbrowser.open(newVersion)
		else:
			wx.MessageBox('You are running the latest version of Cura!', 'Awesome!', wx.ICON_INFORMATION)

	def OnAbout(self, e):
		info = wx.AboutDialogInfo()
		info.SetName('Cura')
		info.SetDescription('End solution for Open Source Fused Filament Fabrication 3D printing.')
		info.SetWebSite('http://software.ultimaker.com/')
		info.SetCopyright('Copyright (C) David Braam')
		info.SetLicence("""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
""")
		wx.AboutBox(info)

	def OnClose(self, e):
		profile.saveGlobalProfile(profile.getDefaultProfilePath())

		# Save the window position, size & state from the preferences file
		profile.putPreference('window_maximized', self.IsMaximized())
		if not self.IsMaximized() and not self.IsIconized():
			(posx, posy) = self.GetPosition()
			profile.putPreference('window_pos_x', posx)
			profile.putPreference('window_pos_y', posy)
			(width, height) = self.GetSize()
			profile.putPreference('window_width', width)
			profile.putPreference('window_height', height)			
			
			# Save normal sash position.  If in normal mode (!simple mode), get last position of sash before saving it...
			isSimple = profile.getPreference('startMode') == 'Simple'
			if not isSimple:
				self.normalSashPos = self.splitter.GetSashPosition()
			profile.putPreference('window_normal_sash', self.normalSashPos)

		#HACK: Set the paint function of the glCanvas to nothing so it won't keep refreshing. Which keeps wxWidgets from quiting.
		print "Closing down"
		self.scene.OnPaint = lambda e : e
		#self.scene._slicer.cleanup()
		self.Destroy()

	def OnQuit(self, e):
		self.Close()

class normalSettingsPanel(configBase.configPanelBase):
	"Main user interface window"
	def __init__(self, parent, callback = None):
		super(normalSettingsPanel, self).__init__(parent)

		#Main tabs
		self.nb = wx.Notebook(self)
		self.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
		self.GetSizer().Add(self.nb, 1, wx.EXPAND)

		(left, right) = self.CreateConfigTab(self.nb, 'Print config')
		#self._addSettingsToPanels('basic', left, right)
		#self.SizeLabelWidths(left, right)
		configBase.TitleRow(left, "Quality")
		c = configBase.SettingRow(left, "Layer height (mm)", 'layer_height', '0.2', 'Layer height in millimeters.\n0.2 is a good value for quick prints.\n0.1 gives high quality prints.')
		validators.validFloat(c, 0.0001)
		validators.warningAbove(c, lambda : (float(profile.getProfileSetting('nozzle_size')) * 80.0 / 100.0), "Thicker layers then %.2fmm (80%% nozzle size) usually give bad results and are not recommended.")
		c = configBase.SettingRow(left, "Wall thickness (mm)", 'wall_thickness', '0.8', 'Thickness of the walls.\nThis is used in combination with the nozzle size to define the number\nof perimeter lines and the thickness of those perimeter lines.')
		validators.validFloat(c, 0.0001)
		validators.wallThicknessValidator(c)
		c = configBase.SettingRow(left, "Enable retraction", 'retraction_enable', False, 'Retract the filament when the nozzle is moving over a none-printed area. Details about the retraction can be configured in the advanced tab.')

		
		#(left, right, self.advancedPanel) = self.CreateDynamicConfigTab(self.nb, 'Advanced')
		#self._addSettingsToPanels('advanced', left, right)
		#self.SizeLabelWidths(left, right)

		#Plugin page
		self.pluginPanel = pluginPanel.pluginPanel(self.nb, callback)
		if len(self.pluginPanel.pluginList) > 0:
			self.nb.AddPage(self.pluginPanel, "Plugins")
		else:
			self.pluginPanel.Show(False)

		#Alteration page
		self.alterationPanel = alterationPanel.alterationPanel(self.nb, callback)
		self.nb.AddPage(self.alterationPanel, "Start/End-GCode")

		self.Bind(wx.EVT_SIZE, self.OnSize)

		self.nb.SetSize(self.GetSize())
		#self.UpdateSize(self.printPanel)
		#self.UpdateSize(self.advancedPanel)

	def _addSettingsToPanels(self, category, left, right):
		count = len(profile.getSubCategoriesFor(category)) + len(profile.getSettingsForCategory(category))

		p = left
		n = 0
		for title in profile.getSubCategoriesFor(category):
			n += 1 + len(profile.getSettingsForCategory(category, title))
			if n > count / 2:
				p = right
			configBase.TitleRow(p, title)
			for s in profile.getSettingsForCategory(category, title):
				if s.checkConditions():
					configBase.SettingRow(p, s.getName())

	def SizeLabelWidths(self, left, right):
		leftWidth = self.getLabelColumnWidth(left)
		rightWidth = self.getLabelColumnWidth(right)
		maxWidth = max(leftWidth, rightWidth)
		self.setLabelColumnWidth(left, maxWidth)
		self.setLabelColumnWidth(right, maxWidth)

	def OnSize(self, e):
		# Make the size of the Notebook control the same size as this control
		self.nb.SetSize(self.GetSize())
		
		# Propegate the OnSize() event (just in case)
		e.Skip()
		
		# Perform out resize magic
		#self.UpdateSize(self.printPanel)
		#self.UpdateSize(self.advancedPanel)
	
	def UpdateSize(self, configPanel):
		sizer = configPanel.GetSizer()
		
		# Pseudocde
		# if horizontal:
		#     if width(col1) < best_width(col1) || width(col2) < best_width(col2):
		#         switch to vertical
		# else:
		#     if width(col1) > (best_width(col1) + best_width(col1)):
		#         switch to horizontal
		#
				
		col1 = configPanel.leftPanel
		colSize1 = col1.GetSize()
		colBestSize1 = col1.GetBestSize()
		col2 = configPanel.rightPanel
		colSize2 = col2.GetSize()
		colBestSize2 = col2.GetBestSize()

		orientation = sizer.GetOrientation()
		
		if orientation == wx.HORIZONTAL:
			if (colSize1[0] <= colBestSize1[0]) or (colSize2[0] <= colBestSize2[0]):
				configPanel.Freeze()
				sizer = wx.BoxSizer(wx.VERTICAL)
				sizer.Add(configPanel.leftPanel, flag=wx.EXPAND)
				sizer.Add(configPanel.rightPanel, flag=wx.EXPAND)
				configPanel.SetSizer(sizer)
				#sizer.Layout()
				configPanel.Layout()
				self.Layout()
				configPanel.Thaw()
		else:
			if max(colSize1[0], colSize2[0]) > (colBestSize1[0] + colBestSize2[0]):
				configPanel.Freeze()
				sizer = wx.BoxSizer(wx.HORIZONTAL)
				sizer.Add(configPanel.leftPanel, proportion=1, border=35, flag=wx.EXPAND)
				sizer.Add(configPanel.rightPanel, proportion=1, flag=wx.EXPAND)
				configPanel.SetSizer(sizer)
				#sizer.Layout()
				configPanel.Layout()
				self.Layout()
				configPanel.Thaw()

	#def updateProfileToControls(self):
	#	super(normalSettingsPanel, self).updateProfileToControls()
	#	self.alterationPanel.updateProfileToControls()
	#	self.pluginPanel.updateProfileToControls()
        
	def updateProfileToControls(self):
		super(normalSettingsPanel, self).updateProfileToControls()
		self.normalSettingsPanel.updateProfileToControls()
		self.simpleSettingsPanel.updateProfileToControls()
