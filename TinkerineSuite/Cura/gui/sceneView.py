from __future__ import absolute_import
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import numpy
import time
import os
import traceback
import threading
import math
import shutil
import platform

import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GLU import *
from OpenGL.GL import *

from Cura.gui import printWindow
from Cura.gui import sliceMenu
from Cura.gui import expertConfig
from Cura.util import profile
from Cura.util import profile2
from Cura.util import meshLoader
from Cura.util import objectScene
from Cura.util import resources
from Cura.util import sliceEngine
from Cura.util import sliceRun
from Cura.util import machineCom
from Cura.util import removableStorage
from Cura.util import gcodeInterpreter
from Cura.util import mesh
from Cura.util import stl2
from Cura.gui.util import previewTools
from Cura.gui.util import opengl
from Cura.gui.util import openglGui
from Cura.util import deleteSupport
from Cura.util import version

class SceneView(openglGui.glGuiPanel):
	def __init__(self, parent):
		super(SceneView, self).__init__(parent)

		self.varitronicsBrandString = "varitronics"

		self.list = []

		self._konamCode = []

		self.debug = False
		self.busyInfo = None

		self._scene = objectScene.Scene()
		self._gcode = None
		self._counter = 0
		self._gcodeVBOs = []
		self._gcodeFilename = None
		self._gcodeLoadThread = None
		self._objectShader = None
		self._objectLoadShader = None
		self._focusObj = None
		self._selectedObj = None
		self._objColors = [None,None,None,None]
		self._mouseX = -1
		self._mouseY = -1
		self._mouseState = None

		self._yaw = -20
		self._pitch = 59
		self._zoom = 339
		self._viewTarget = numpy.array([0,0,0], numpy.float32)

		self._animView = None
		self._animZoom = None
		self._platformditto = meshLoader.loadMeshes(resources.getPathForMesh('ditto+.stl'))[0]##
		self._platformditto._drawOffset = numpy.array([40,0,0], numpy.float32)

		self._platformlitto = meshLoader.loadMeshes(resources.getPathForMesh('litto4.stl'))[0]##
		self._platformlitto._drawOffset = numpy.array([40,0,0], numpy.float32)

		self._platformdittopro = meshLoader.loadMeshes(resources.getPathForMesh(_('DittoPro3.stl')))[0]##
		self._platformdittopro._drawOffset = numpy.array([40,0,0], numpy.float32)

		self._isSimpleMode = True

		self._isSlicing = False

		self._anObjectIsOutsidePlatform = False

		self._viewport = None
		self._modelMatrix = None
		self._projMatrix = None
		self.tempMatrix = None

		self._degree = unichr(176)

		self.cameraMode = 'default'

		self.settingsOpen = False
		self.cameraOpen = False
		self.viewmodeOpen = False

		self.advancedOpen = False

		self.saveMenuOpen = False

		self.rotationLock = True

		self.supportLines = []
		#self.trimList = numpy.zeros((0,3), numpy.float32)
		self.trimList = []
		self.trimList2 = []


		self.scaleList = []
		self.rotateList = []
		self.viewModeList = []
		self.cameraList = []

		self.resultFilename = ""

		self.openFileButton      = openglGui.glButton(self, 23, _('IMPORT'), _('Add an object to the build platform'), (0,-1.5), self.showLoadModel, 0, 0, None, "left")
		self.settingsButton      = openglGui.glButton(self, 24, _('SETTINGS'), _('Edit Slicing Settings'), (0,-0.5), self.showSettings, 0, 0, None, "left")
		#self.deleteButton      = openglGui.glButton(self, 25, 'DELETE', _('Delete selected model'), (0,0.5), self.deleteSelection, 0, 0, None, "left")
		self.printButton         = openglGui.glButton(self, 26, _('SLICE'), _('Slice current build platform'), (0,0.5), self.OnPrintButton, 0, 0, None, "left")

		self.abortButton         = openglGui.glButton(self, 10, _('ABORT'), '', (2.7,0.6), self.OnAbortButton, 0, 0, 40, "left")
		self.abortButton._tooltipNudgeX = -10
		self.abortButton._tooltipNudgeY = 5

		#print self.abortButton._tooltipTextTitle._colour

		group = []
		group6 = []
		#self.cameraButton      = openglGui.glButton(self, 26, 'Camera', (8,-1), self.OnToolSelect)
		self.cameraButton  = openglGui.glRadioButton(self, 20, _('CAMERA VIEW'), '', (-1.5,-1), group, self.showCamera, 0, 0, None, 1, "bottom")
		self.moveButton      = openglGui.glRadioButton(self, 21, _('MODEL VIEW'), '', (-0.5,-1), group, self.showViewmode, 0, 0, None, 1, "bottom")
		self.changeModeButton  = openglGui.glRadioButton(self, 22, _('PRINT '), '', (-30,-1), group6, self.OnToolSelect, 0, 0, None, 1, "bottom")
		self.rotateToolButton = openglGui.glRadioButton(self, 19, _('ROTATE '), '', (0.5,-1), group, self.showRotate, 0, 0, None, 1, "bottom")
		self.scaleToolButton  = openglGui.glRadioButton(self, 18, _('SCALE '), '', (1.5,-1), group, self.showScale, 0, 0, None, 1, "bottom")

		#self.mirrorToolButton  = openglGui.glRadioButton(self, 10, 'Mirror', (1,-1), group, self.OnToolSelect)

		self.resetRotationButton = openglGui.glButton(self, 30, '', '', (-0.88,-1.85), self.OnRotateReset, 0, -2, 45, "bottom", True)
		self.layFlatButton       = openglGui.glButton(self, 31, '', '', (0.35,-1.85), self.OnLayFlat, 0, -2, 45, "bottom", True)
		self.resetRotationButton._extraHitbox = (-30,67,-30,30)
		self.layFlatButton._extraHitbox = (-30,67,-30,30)

		self.sdSaveButton = openglGui.glButton(self, 35, '', '', (1.1,-2), self.OnCopyToSD, 0, -2, 100)
		self.sdSaveButton._hidden = True

		self.sdEjectButton = openglGui.glButton(self, 36, '', '', (2,-2), self.OnSafeRemove, 0, -2, 35)
		self.sdEjectButton._hidden = True


		self.directorySaveButton       = openglGui.glButton(self, 22, '', '', (3.8,-2), self.OnCopyToDirectory, 0, -2, 100)
		self.directorySaveButton._hidden = True

		self.closeSaveButton       = openglGui.glButton(self, 15, '', '', (5.0,-2.8), self.CloseSavePrompt, 0, -2, 30)
		self.closeSaveButton._hidden = True


		self.saveText       = openglGui.glLabel(self, _('Choose Save Destination'), (3.0,-3), 18, (139,197,63))
		self.saveText._hidden = True

		self.saveStatusText      = openglGui.glLabel(self, '', (3.0,-1.2), 18, (139,197,63))
		self.saveStatusText._hidden = True

		self.printTimeEstimationText      = openglGui.glLabel(self, '', (2.75,-1.55), 18, (139,197,63))
		self.printTimeEstimationText._hidden = True

		#resetRotationLabel = openglGui.glLabel(self, 'RESET', (-0.21,-2.06))
		#self.rotateList.append(resetRotationLabel)
		#layLabel = openglGui.glLabel(self, 'LAY', (1.02,-2.13))
		#self.rotateList.append(layLabel)
		#flatLabel = openglGui.glLabel(self, 'FLAT', (1.04,-1.98))
		#self.rotateList.append(flatLabel)

		#self.resetRotationButton._tooltipTextTitle.mode = "follow"

		#reset rotation

		self.infillPlusCounter = 0
		self.infillMinusCounter = 0
		self.infillCounter = int(profile.getProfileSettingFloat('fill_density'))
		self.filamentCounter = float(profile.getProfileSettingFloat('filament_diameter'))

		self.resolutionCounter = int(profile.getProfileSettingFloat('layer_height'))
		self.wallCounter = int(profile.getProfileSettingFloat('wall_thickness'))
		self.supportCounter = int(profile.getProfileSettingFloat('support_angle'))
		self.speedCounter = int(profile.getProfileSettingFloat('print_speed'))
		self.temperatureCounter = int(profile.getProfileSettingFloat('print_temperature'))
		self.temperaturebedCounter = int(profile.getProfileSettingFloat('print_bed_temperature'))

		#self.supportCounter = int(profile.getProfileSettingFloat('support'))
		#self.vaseCounter = int(profile.getProfileSettingFloat('vase'))

		self.mirrorXButton       = openglGui.glButton(self, 14, '', 'Mirror X', (1,-3), lambda button: self.OnMirror(0))
		self.mirrorYButton       = openglGui.glButton(self, 18, '', 'Mirror Y', (2,-3), lambda button: self.OnMirror(1))
		self.mirrorZButton       = openglGui.glButton(self, 22, '', 'Mirror Z', (3,-3), lambda button: self.OnMirror(2))

		group2 = []
		if version.getBrand() == "varitronics":
			self.dittoProButton       = openglGui.glRadioButtonSetting(self, 72, '', (0,1), group2, self.changeToDittoPro, 80,235, 60, 0.6)
		else:
			self.littoButton       = openglGui.glRadioButtonSetting(self, 1, '', (0,1), group2, self.changeToLitto, 80,235, 60, 0.6)
			self.dittoButton       = openglGui.glRadioButtonSetting(self, 2, '', (0,2), group2, self.changeToDitto, 120,235, 60, 0.6)
			self.dittoProButton       = openglGui.glRadioButtonSetting(self, 3, '', (0,3), group2, self.changeToDittoPro, 160,235, 60, 0.6)

		group3 = []
		self.lowResButton      = openglGui.glRadioButtonSetting(self, 4, '', (0,1), group3, self.lowResolution, 80,196, 60, 0.6)
		self.medResButton      = openglGui.glRadioButtonSetting(self, 5, '', (0,2), group3, self.medResolution, 120,196, 60, 0.6)
		self.highResButton      = openglGui.glRadioButtonSetting(self, 6, '', (0,3), group3, self.highResolution, 160,196, 60, 0.6)
		self.ultraResButton      = openglGui.glRadioButtonSetting(self, 7, '', (0,4), group3, self.ultraResolution, 200,196, 60, 0.6)

		self.decreaseInfillButton       = openglGui.glButtonSetting(self, 8, '', (0,0), self.decreaseInfill, 40,160, 56, 0.4)
		self.increaseInfillButton       = openglGui.glButtonSetting(self, 9, '', (0,0), self.increaseInfill, 115,160, 56, 0.4)

		self.decreaseFilamentButton       = openglGui.glButtonSetting(self, 8, '', (0,0), self.decreaseFilament, 240,160, 56, 0.4)
		self.increaseFilamentButton       = openglGui.glButtonSetting(self, 9, '', (0,0), self.increaseFilament, 310,160, 56, 0.4)

		self.decreaseWallThicknessButton       = openglGui.glButtonSetting(self, 8, '', (0,0), self.decreaseWallThickness, 40,125, 56, 0.4, True)
		self.IncreaseWallThicknessButton       = openglGui.glButtonSetting(self, 9, '', (0,0), self.increaseWallThickness, 115,125, 56, 0.4, True)

		group1 = []
		self.brimOnButton =  openglGui.glRadioButtonSetting(self, 73, 'Helps bed adhesion by having the skirt touch the object', (0,1), group1, self.brimOn, 274,124, 40, 0.6, True)
		self.brimOffButton =  openglGui.glRadioButtonSetting(self, 69, '', (0,2), group1, self.brimOff, 241,124, 40, 0.6, True)

		self.decreaseTemperatureButton       = openglGui.glButtonSetting(self, 8, '', (0,0), self.decreaseTemperature, 40,97, 56, 0.4, True)
		self.increaseTemperatureButton       = openglGui.glButtonSetting(self, 9, '', (0,0), self.increaseTemperature, 115,97, 56, 0.4, True)

		group33 = []
		self.supportOffButton      = openglGui.glRadioButtonSetting(self, 37, '', (0,1), group33, self.supportOff, 241,97, 40, 0.6, True)
		self.supportExtButton      = openglGui.glRadioButtonSetting(self, 38, _('Build support only on the Exterior of the object'), (0,2), group33, self.supportExt, 275,97, 40, 0.6, True)
		self.supportAllButton      = openglGui.glRadioButtonSetting(self, 39, _('Build support everywhere it needs'), (0,3), group33, self.supportAll, 309,97, 40, 0.6, True)

		self.decreaseSupportButton       = openglGui.glButtonSetting(self, 8, '', (0,0), self.decreaseSupport, 240,78, 56, 0.35, True)
		self.IncreaseSupportButton       = openglGui.glButtonSetting(self, 9, '', (0,0), self.increaseSupport, 310,78, 56, 0.35, True)

		self.decreasePrintSpeedButton       = openglGui.glButtonSetting(self, 8, '', (0,0), self.decreasePrintSpeed, 40,78, 56, 0.4, True)
		self.increasePrintSpeedButton       = openglGui.glButtonSetting(self, 9, '', (0,0), self.increasePrintSpeed, 115,78, 56, 0.4, True)

		#self.decreaseBedTemperatureButton       = openglGui.glButtonSetting(self, 8, '', (0,0), self.decreaseBedTemperature, 210,64, 56, 0.4, True)
		#self.increaseBedTemperatureButton       = openglGui.glButtonSetting(self, 7, '', (0,0), self.increaseBedTemperature, 285,64, 56, 0.4, True)

		self.closeButton       = openglGui.glButtonSetting(self, 15, '', (0,0), self.showSettings, 344,259, 30, 0.65)
		self.saveButton       = openglGui.glButtonSetting(self, 34, _('Save Settings'), (0,0), self.saveSettings, 322,259, 30, 0.65)
		self.advancedTabButton       = openglGui.glButtonSetting(self, 17, '', (0,0), lambda button: self.showAdvancedSettings(self.advancedTabButton), 160,131, 24, 1.0, None)


		if profile.getProfileSetting('skirt_gap') != '0':
			self.brimOffButton.setSelected(True)
		else:
			self.brimOnButton.setSelected(True)

		#self.vaseOnOffButton       = openglGui.glButtonSetting(self, 9, '', (0,0), lambda button: self.vaseOnOff(self.vaseOnOffButton), 255,100, 45, 0.7, True)
		#if profile.getProfileSetting('vase') == 'False':
		#	self.vaseOnOffButton.setImageID(9)
		#else:
		#	self.vaseOnOffButton.setImageID(10)


		group4 = []
		self.cameraDefaultButton  = openglGui.glCameraRadioButtonSetting(self, 14, (-10,1.89), group4, self.cameraDefault, -104,0, 40, 'camera')
		self.cameraFrontButton  = openglGui.glCameraRadioButtonSetting(self, 13, (-11,1.89), group4, self.cameraFront, -36,0, 40, 'camera')
		self.cameraSideButton   = openglGui.glCameraRadioButtonSetting(self, 12, (-12,1.89), group4, self.cameraSide, 33,0, 40, 'camera')
		self.cameraTopButton     = openglGui.glCameraRadioButtonSetting(self, 11, (-13,1.89), group4, self.cameraTop, 102,0, 40, 'camera')

		#self.cameraTopButton       = openglGui.glButton(self, 12, 'Top View', 'aaaaaaaa', (0.7,-1.75), self.cameraTop, 0, -2, 40, "bottom")

		group5 = []
		self.modelViewButton     = openglGui.glCameraRadioButtonSetting(self, 27, (-10,1.885), group5, lambda button: self.setModelView(0), -128, 0, 40, 'viewmode')
		self.overhangViewButton    = openglGui.glCameraRadioButtonSetting(self, 29, (-11,1.885), group5, lambda button: self.setModelView(1), -24, 0,40, 'viewmode')
		self.gcodeViewButton  = openglGui.glCameraRadioButtonSetting(self, 28, (-10,1.885), group5, lambda button: self.setModelView(4), 82, 0, 40, 'viewmode')
		self.modelViewButton._extraHitbox = (-30,80,-30,30)
		self.gcodeViewButton._extraHitbox = (-30,80,-30,30)
		self.overhangViewButton._extraHitbox = (-30,85,-30,30)
		#defaultViewLabel = openglGui.glLabel(self, 'DEFAULT', (-1.02,-2.06))
		#self.viewModeList.append(defaultViewLabel)
		#supportViewLabel = openglGui.glLabel(self, 'SUPPORT', (0.35,-2.06))
		#self.viewModeList.append(supportViewLabel)
		#layerViewLabel = openglGui.glLabel(self, 'LAYER', (1.75,-2.06))
		#self.viewModeList.append(layerViewLabel)


		#self.profileLabelText       = openglGui.glTextLabelSetting(self, "PROFILE", (0,4), -12,213, 11, False)
		if version.getBrand() == "varitronics":
			currentMachineString = _("DittoPro 3D Printer")
			self.dittoProButton.setSelected(True)
			profile.putPreference('machine_width', '219')
			profile.putPreference('machine_depth', '165')
			profile.putPreference('machine_height', '219')
		else:
			if profile.getPreferenceFloat('machine_width') == 130: #litto width
				currentMachineString = _("Litto 3D Printer")
				self.littoButton.setSelected(True)
			elif profile.getPreferenceFloat('machine_width') == 210: #ditto width
				currentMachineString = _("Ditto+ 3D Printer")
				self.dittoButton.setSelected(True)
			else:
				currentMachineString = _("DittoPro 3D Printer")
				self.dittoProButton.setSelected(True)
		self.machineText       = openglGui.glTextLabelSetting(self, currentMachineString, (0,4), 230,225, 12, False)

		if profile.getProfileSettingFloat('layer_height') == 0.3:
			resolutionString = _("Low: 300 micron")
			self.lowResButton.setSelected(True)
		elif profile.getProfileSettingFloat('layer_height') == 0.2:
			resolutionString = _("Medium: 200 micron")
			self.medResButton.setSelected(True)
		elif profile.getProfileSettingFloat('layer_height') == 0.1:
			resolutionString = _("High: 100 micron")
			self.highResButton.setSelected(True)
		else:
			resolutionString = _("Ultra: 50 micron")
			self.ultraResButton.setSelected(True)

		if profile.getProfileSetting('support') == 'None':
			self.supportOffButton.setSelected(True)
		elif profile.getProfileSetting('support') == 'Exterior Only':
			self.supportExtButton.setSelected(True)
		else:
			self.supportAllButton.setSelected(True)

		#self.resolutionLabelText       = openglGui.glTextLabelSetting(self, "RESOLTUION", (0,4), -12,176, 11, False)
		self.resolutionText       = openglGui.glTextLabelSetting(self, resolutionString, (0,4), 230,188, 12, False)

		#self.infillLabelText       = openglGui.glTextLabelSetting(self, "INFILL", (0,4), -12,138, 11, False)
		infillString = str(int(profile.getProfileSettingFloat('fill_density'))) + '%'
		self.infillText       = openglGui.glTextLabelSetting(self, infillString, (0,4), 65,152, 12, False)
		###
		if self.debug:
			self.xText       = openglGui.glTextLabelSetting(self, "X:", (0,4), 375,220, 12, False, (0,0,0))
			self.yText       = openglGui.glTextLabelSetting(self, "Y:", (0,4), 375,190, 12, False, (0,0,0))
			self.zText       = openglGui.glTextLabelSetting(self, "Z:", (0,4), 375,160, 12, False, (0,0,0))
		#print self.infillText.getTooltip()
		#self.infillText.setTooltip('wowoow database')

		#self.filamentLabelText       = openglGui.glTextLabelSetting(self, "FILAMENT", (0,4), 175,139, 11, False)
		filamentString = str(profile.getProfileSettingFloat(_('filament_diameter')))
		self.filamentText       = openglGui.glTextLabelSetting(self, filamentString, (0,4), 263,152, 12, False)

		#self.shellLabelText       = openglGui.glTextLabelSetting(self, "WALLS", (0,4), -12,103, 11, True)
		shellString = str(int(profile.getProfileSettingFloat(_('wall_thickness'))))
		self.shellText       = openglGui.glTextLabelSetting(self, shellString, (0,4), 73,117, 12, True)

		#self.shellLabelText       = openglGui.glTextLabelSetting(self, "WALLS", (0,4), -12,103, 11, True)
		supportString = str(int(profile.getProfileSettingFloat(_('support_angle')))) + self._degree
		self.supportText       = openglGui.glTextLabelSetting(self, supportString, (0,4), 267,70, 12, True)

		#self.speedLabelText       = openglGui.glTextLabelSetting(self, "SPEED", (0,4), -12,66, 11, True)
		speedString = str(int(profile.getProfileSettingFloat(_('print_speed')))) + _("mm/s")
		self.speedText       = openglGui.glTextLabelSetting(self, speedString, (0,4), 54,70, 12, True)

		#self.temperatureLabelText       = openglGui.glTextLabelSetting(self, "TEMP", (0,4), 172,67, 11, True)

		#self.tempLabelText       = openglGui.glTextLabelSetting(self, "Hotend", (0,4), 300,74, 11, True)
		temperatureString = str(int(profile.getProfileSettingFloat(_('print_temperature')))) + self._degree + _("C")
		self.temperatureText       = openglGui.glTextLabelSetting(self, temperatureString, (0,4), 60,88, 12, True)

		#self.bedtempLabelText       = openglGui.glTextLabelSetting(self, "Bed", (0,4), 300,57, 11, True)
		#bedtemperatureString = str(int(profile.getProfileSettingFloat('print_bed_temperature'))) + self._degree + "C"
		#self.bedTemperatureText       = openglGui.glTextLabelSetting(self, bedtemperatureString, (0,4), 233,56, 12, True, (self.textColour))

		#self.supportLabelText       = openglGui.glTextLabelSetting(self, "SUPPORT", (0,4), 175,110, 11, True)
		#self.vaseLabelText       = openglGui.glTextLabelSetting(self, "VASE", (0,4), 300,200, 11, False)


		self.savedLabel = openglGui.glTextLabelSetting(self, _("*Settings Saved*"), (0,4), 180,260, 16, False)
		self.savedLabel._timer = 0

		#print self.testButton._Xnudge
		#	def __init__(self, parent, imageID, tooltip, callback, Xnudge = 0, Ynudge = 0, size = None):

		#self.rotateToolButton.setExpandArrow(True)
		#self.scaleToolButton.setExpandArrow(True)
		#self.mirrorToolButton.setExpandArrow(True)

		self.scaleForm = openglGui.glFrame(self, (13, -1))
		openglGui.glGuiLayoutGrid(self.scaleForm)



		#widthLabel = openglGui.glLabel(self, 'WIDTH', (-1.32,-2.25))
		#self.scaleList.append(widthLabel)

		#depthLabel = openglGui.glLabel(self, 'DEPTH', (-0.25,-2.25))
		#self.scaleList.append(depthLabel)

		#heightLabel = openglGui.glLabel(self, 'HEIGHT', (.8,-2.25))
		#self.scaleList.append(heightLabel)

		#uniformLabel = openglGui.glLabel(self, 'UNIFORM', (1.99,-2.58))
		#self.scaleList.append(uniformLabel)

		#scalingLabel = openglGui.glLabel(self, 'SCALING', (2.00,-2.43))
		#self.scaleList.append(scalingLabel)

		#resetLabel = openglGui.glLabel(self, 'RESET', (2.01,-2.03))
		#self.scaleList.append(resetLabel)

		self.scaleXctrl = openglGui.glNumberCtrl(self, '0', (-1.59,-2.17), lambda value: self.OnScaleEntry(value, 0), True)
		self.scaleList.append(self.scaleXctrl)

		self.scaleYctrl = openglGui.glNumberCtrl(self, '0', (-0.50,-2.17), lambda value: self.OnScaleEntry(value, 1), True)
		self.scaleList.append(self.scaleYctrl)

		self.scaleZctrl = openglGui.glNumberCtrl(self, '0', (0.55,-2.17), lambda value: self.OnScaleEntry(value, 2), True)
		self.scaleList.append(self.scaleZctrl)

		self.scaleXmmctrl = openglGui.glNumberCtrl(self, '0.0', (-1.5,-1.69), lambda value: self.OnScaleEntryMM(value, 0))
		self.scaleList.append(self.scaleXmmctrl)

		self.scaleYmmctrl = openglGui.glNumberCtrl(self, '0.0', (-0.41,-1.69), lambda value: self.OnScaleEntryMM(value, 1))
		self.scaleList.append(self.scaleYmmctrl)

		self.scaleZmmctrl = openglGui.glNumberCtrl(self, '0.0', (0.64,-1.69), lambda value: self.OnScaleEntryMM(value, 2))
		self.scaleList.append(self.scaleZmmctrl)

		self.resetScaleButton = openglGui.glButton(self, 30, '', '', (1.34,-1.84), self.OnScaleReset, 0, -2, 45, "bottom", True)
		self.scaleList.append(self.resetScaleButton)
		self.resetScaleButton._extraHitbox = (-27,75,-19,19)

		self.rotationLockButton = openglGui.glButton(self, 32, '', '', (1.34,-2.37), lambda button: self.OnRotationLock(self.rotationLockButton), 0, -2, 45, "bottom", True)
		self.rotationLockButton._extraHitbox = (-27,75,-19,19)

		self.scaleUniform = openglGui.glCheckbox(self.scaleForm, True, (1,8), None)

		#self.resetScaleButton    = openglGui.glButton(self, 13, '', 'Reset', (17,7), self.OnScaleReset,0,0,32)
		self.scaleMaxButton      = openglGui.glButton(self, 17, '', 'To max', (2,-2), self.OnScaleMax)

		#self.layFlatButton       = openglGui.glButton(self, 31, '', '', (1.3,-1.75), self.OnLayFlat, 0, -2, 40, "bottom")

		self.modelView = 0
		#self.viewSelection = openglGui.glComboButton(self, 'View mode', '', [7,19,11,15,23], ['Normal', 'Overhang', 'Transparent', 'X-Ray', 'Layers'], (-1,1), self.OnViewChange)
		self.layerSelect = openglGui.glSlider(self, 10000, 0, 1, (-1.11,-2), lambda : self.QueueRefresh())

		self.notification = openglGui.glNotification(self, (0, 0))

		self._slicer = sliceEngine.Slicer(self._updateSliceProgress)
		self._sceneUpdateTimer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self._onRunSlicer, self._sceneUpdateTimer)
		self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
		self.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)

		self.OnViewChange()
		self.OnToolSelect(0)
		self.updateToolButtons()
		self.updateProfileToControls()

	def setModelView(self, value):
		self.modelView = value
		self.OnViewChange()
	def getModelView(self):
		return self.modelView

	def showSettings(self, e):
		#print "Yaw: " + str(self._yaw)
		#print "Pitch: " + str(self._pitch)
		#print "Zoom: " + str(self._zoom)
		#print "viewTarget[0]: " + str(self._viewTarget[0])
		#print "viewTarget[1]: " + str(self._viewTarget[1])
		
		if self.settingsOpen == True:
			self.settingsOpen = False
		else:
			self.settingsOpen = True
		self.CloseSavePrompt(e)
	def saveSettings(self, e):		
		profile.putProfileSetting('fill_density', int(self.infillCounter))
		profile.putProfileSetting('filament_diameter', float(self.filamentCounter))
		profile.putProfileSetting('wall_thickness', int(self.wallCounter))
		profile.putProfileSetting('support_angle', int(self.supportCounter))
		profile.putProfileSetting('print_speed', int(self.speedCounter))
		profile.putProfileSetting('print_temperature', int(self.temperatureCounter))
		profile.putProfileSetting('print_bed_temperature', int(self.temperaturebedCounter))

		self.updateProfileToControls()
		#self.infillCounter = 0
		self.savedLabel._timer = 30
	def showAdvancedSettings(self, button):
	
		if self.advancedOpen == True:
			self.advancedOpen = False
			button.setImageID(17)
		else:
			self.advancedOpen = True
			button.setImageID(16)
	def showCamera(self,e): 
		self.moveButton._selected = False #this is the viewmode button
		self.viewmodeOpen = False
		if self.cameraOpen == True:
			self.cameraOpen = False
		else:
			self.cameraOpen = True
		self.OnToolSelect(0)
	def showViewmode(self,e):
		self.cameraButton._selected = False
		self.cameraOpen = False
		if self.viewmodeOpen == True:
			self.viewmodeOpen = False
		else:
			self.viewmodeOpen = True
		self.OnToolSelect(0)
	def showRotate(self,e):
		self.setModelView(0)
		self.cameraButton._selected = False
		self.cameraOpen = False
		self.moveButton._selected = False #this is the viewmode button
		self.viewmodeOpen = False
		
		#if self.viewmodeOpen == True:
		#	self.viewmodeOpen = False
		#else:
		#	self.viewmodeOpen = True
		self.OnToolSelect(e)
	def showScale(self,e):
		self.setModelView(0)
		self.cameraButton._selected = False
		self.cameraOpen = False
		self.moveButton._selected = False #this is the viewmode button
		self.viewmodeOpen = False
		
		#if self.viewmodeOpen == True:
		#	self.viewmodeOpen = False
		#else:
		#	self.viewmodeOpen = True
		self.OnToolSelect(e)
		
	def showLoadModel(self, button = 1):
		if button == 1:
			dlg=wx.FileDialog(self, _('Open 3D model'), os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST|wx.FD_MULTIPLE)
			dlg.SetWildcard(meshLoader.loadWildcardFilter() + "|GCode file (*.gcode)|*.g;*.gcode;*.G;*.GCODE")
			if dlg.ShowModal() != wx.ID_OK:
				dlg.Destroy()
				return
			filenames = dlg.GetPaths()
			dlg.Destroy()
			if len(filenames) < 1:
				return False
			for filename in filenames:
				ext = filename[filename.rfind('.')+1:].upper()
				if ext == "EXPERTPASS":
					ecw = expertConfig.expertConfigWindow(self)
					ecw.Centre()
					ecw.Show(True)
					return
			profile.putPreference('lastFile', filenames[0])
			gcodeFilename = None
			for filename in filenames:
				self.GetParent().GetParent().addToModelMRU(filename)
				ext = filename[filename.rfind('.')+1:].upper()
				if ext == 'G' or ext == 'GCODE':
					gcodeFilename = filename
			if gcodeFilename is not None:
				if self._gcode is not None:
					self._gcode = None
					for layerVBOlist in self._gcodeVBOs:
						for vbo in layerVBOlist:
							self.glReleaseList.append(vbo)
					self._gcodeVBOs = []
				self._gcode = gcodeInterpreter.gcode()
				self._gcodeFilename = gcodeFilename
				#print self._gcodeFilename
				self.printButton.setBottomText('')
				self.setModelView(4)
				self.printButton.setDisabled(False)
				self.OnSliceDone(gcodeFilename)
				self.OnViewChange()
			else:
				if self.getModelView() == 4:
					self.setModelView(0)
					self.OnViewChange()
				try:
					self.loadScene(filenames)
				except:
					pass

	def testgcodeload(self,filename):
		self.busyInfo = wx.BusyInfo(_("loading gcode... please wait..."), self)
		gcodeFilename = filename
		self.supportLines = []
		if self._gcode is not None:
			self._gcode = None
			for layerVBOlist in self._gcodeVBOs:
				for vbo in layerVBOlist:
					self.glReleaseList.append(vbo)
				self._gcodeVBOs = []
		self._gcode = gcodeInterpreter.gcode()
		self._gcodeFilename = gcodeFilename

		if self._slicer._totalMoveTimeMinute != None:
			self._gcode.totalMoveTimeMinute = self._slicer._totalMoveTimeMinute
			self._gcode.extrusionAmount = self._slicer._extrusionAmount
			self._gcode.basicSettings = self._slicer._basicSettings
			self._slicer._totalMoveTimeMinute = None

		else:
			self._gcode.load(filename)
		#print self._gcodeFilename
		self.printButton.setBottomText('')
		self.setModelView(4)
		self.printButton.setDisabled(False)
		self.OnViewChange()
		self.busyInfo = None

	def showSaveModel(self):
		if len(self._scene.objects()) < 1:
			return
		defPath = profile.getPreference('lastFile')
		defPath = defPath[0:defPath.rfind('.')] + '_export' + '.stl'
		
		dlg=wx.FileDialog(self, _('Save 3D model'), os.path.split(profile.getPreference('lastFile'))[0], defPath, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
		dlg.SetWildcard(meshLoader.saveWildcardFilter())
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		filename = dlg.GetPath()
		dlg.Destroy()
		busyInfo = wx.BusyInfo(_("Saving model(s), please wait..."), self)
		meshLoader.saveMeshes(filename, self._scene.objects())
		busyInfo.Destroy()

	def OnPrintButton(self, button):
		if len(self._scene.objects()) < 1:
			return
		if self.getProgressBar() is not None:
			return
		if not self._anObjectIsOutsidePlatform:
			return
		self.setModelView(0)
		defPath = profile.getPreference('lastFile')
		defPath = defPath[0:defPath.rfind('.')] + '.g'
		
		#dlg=wx.FileDialog(self, "Save project gcode file", os.path.split(profile.getPreference('lastFile'))[0], defPath, style=wx.FD_SAVE)
		#dlg.SetWildcard("GCode file (*.g, *.gcode)|*.g;*.gcode;*.G;*.GCODE")
		#if dlg.ShowModal() != wx.ID_OK:
		#	dlg.Destroy()
		#	return
		#resultFilename = dlg.GetPath()
		resultFilename = defPath
		#dlg.Destroy()
		self.saveSettings(button)
		self._isSlicing = True

		self.setCursorToBusy()

		self._slicer.runSlicer(self._scene.objects(), resultFilename, self)
		self.setProgressBar(0.001)
		self.abortButton._hidden = False

		#smw = sliceMenu.sliceMenu(self)
		#smw.Centre()
		#smw.Show(True)

        def OnPrintButton2(self, button):

		dlg=wx.FileDialog(self, "Save project gcode file", os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_SAVE)
		dlg.SetWildcard("GCode file (*.gcode)|*.gcode")
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		resultFilename = dlg.GetPath()
		dlg.Destroy()
		#for item in self._scene.objects():
		#	print item.name
		self._slicer.runSlicer(self._scene.objects(), resultFilename, self)
		#print(self._gcodeFilename)
		#self.testgcodeload("C:\Users\Just\Desktop\66.gcode")
		# if button == 1:
			# if machineCom.machineIsConnected():
				# self.showPrintWindow()
			# elif len(removableStorage.getPossibleSDcardDrives()) > 0:
				# drives = removableStorage.getPossibleSDcardDrives()
				# if len(drives) > 1:
					# dlg = wx.SingleChoiceDialog(self, "Select SD drive", "Multiple removable drives have been found,\nplease select your SD card drive", map(lambda n: n[0], drives))
					# if dlg.ShowModal() != wx.ID_OK:
						# dlg.Destroy()
						# return
					# drive = drives[dlg.GetSelection()]
					# dlg.Destroy()
				# else:
					# drive = drives[0]
				# filename = self._scene._objectList[0].getName() + '.gcode'
				# threading.Thread(target=self._copyFile,args=(self._gcodeFilename, drive[1] + filename, drive[1])).start()
			# else:
				# self.showSaveGCode()
		# if button == 3:
			# menu = wx.Menu()
			# self.Bind(wx.EVT_MENU, lambda e: self.showPrintWindow(), menu.Append(-1, 'Print with USB'))
			# self.Bind(wx.EVT_MENU, lambda e: self.showSaveGCode(), menu.Append(-1, 'Save GCode...'))
			# self.Bind(wx.EVT_MENU, lambda e: self._showSliceLog(), menu.Append(-1, 'Slice engine log...'))
			# self.PopupMenu(menu)
			# menu.Destroy()

	def setCursorToBusy(self):
		mainWindow = self.GetParent().GetParent()
		mainWindow.setCursorToBusy()

	def setCursorToDefault(self):
		mainWindow = self.GetParent().GetParent()
		mainWindow.setCursorToDefault()


	def OnAbortButton(self, button):
		#self.setProgressBar(None)
		self.abortButton._hidden = True
		print button
		try:
			self._slicer._pspw.OnAbort(button)
		except:
			print "abort failed"
		self.setCursorToDefault()
		#self.setProgressBar(None)
		
	def showPrintWindow(self):
		if self._gcodeFilename is None:
			return
		printWindow.printFile(self._gcodeFilename)
		if self._gcodeFilename == self._slicer.getGCodeFilename():
			self._slicer.submitSliceInfoOnline()

	def showSaveGCode(self):
		defPath = profile.getPreference('lastFile')
		defPath = defPath[0:defPath.rfind('.')] + '.gcode'
		dlg=wx.FileDialog(self, _('Save toolpath'), defPath, style=wx.FD_SAVE)
		dlg.SetFilename(self._scene._objectList[0].getName())
		dlg.SetWildcard('Toolpath (*.gcode)|*.gcode;*.g')
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		filename = dlg.GetPath()
		dlg.Destroy()

		threading.Thread(target=self._copyFile,args=(self._gcodeFilename, filename)).start()
	
	def OnSliceDone(self, resultFilename):
		self.testgcodeload(resultFilename)
		self.setProgressBar(None)
		self.saveMenuOpen = True
		self.sdSaveButton._hidden = False
		self.setCursorToDefault()
		#self.sdEjectButton._hidden = False
		self.directorySaveButton._hidden = False
		self.closeSaveButton._hidden = False
		self.saveText._hidden = False
		self.saveStatusText._hidden = False
		self.saveStatusText._label = ""
		self.printTimeEstimationText._label = "Est. Print time - %02dh:%02dm | Weight: %.2fg" % (int(self._gcode.totalMoveTimeMinute / 60), int(self._gcode.totalMoveTimeMinute % 60), self._gcode.calculateWeight()*1000)
		if version.isDevVersion():
			for settingPair in self._gcode.basicSettings:
				try:
					self.saveStatusText._label += settingPair
				except:
					pass
  		self.printTimeEstimationText._hidden = False
		self.resultFilename = resultFilename
		self.settingsOpen = False
		#text = "Would you like to copy the sliced file to SD card: [" + profile.getPreference('sdpath') + "]?"

		
	def OnCopyToSD(self, e):
		if profile.getPreference('sdpath') != '':
			filename = os.path.basename(self.resultFilename)
			if profile.getPreference('sdshortnames') == 'True':
				filename = self.getShortFilename(filename)
			try:
				shutil.copy(self.resultFilename, os.path.join(profile.getPreference('sdpath'), filename))
				self.saveStatusText._label = str(filename) + " saved to [" + str(profile.getPreference('sdpath')) +"]"
			except:
				print "could not save to sd card"
				self.saveStatusText._label = _("Unable to save to SD Card")
			
	def getShortFilename(self,filename):
		ext = filename[filename.rfind('.'):]
		filename = filename[: filename.rfind('.')]
		return filename[:8] + ext[:2]
			
	def OnCopyToDirectory(self, e):
		filename = os.path.basename(self.resultFilename)
		#print self.resultFilename
		dlg=wx.FileDialog(self, _("Save project gcode file"), os.path.split(self.resultFilename)[0], filename, style=wx.FD_SAVE)
		dlg.SetWildcard("GCode file (*.g, *.gcode)|*.g;*.gcode;*.G;*.GCODE")
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		path = dlg.GetPath()
		print path
		#self.resultFilename = dlg.GetPath()
		#resultFilename = defPath
		dlg.Destroy()
		try:
			shutil.copy(self.resultFilename, path)
			self.saveStatusText._label = dlg.GetFilename() + _(" saved to directory")
			print "copied " + filename + " into directory"
		except shutil.Error:
			traceback.print_exc()
			#print "could not shutil the file: " + path + " to directory"
			self.saveStatusText._label = _("File Already Exists in Directory")
			#print 'My exception occurred, value:', e.value
			
	def OnSafeRemove(self, e):
		import platform
		try:
			if len(removableStorage.getPossibleSDcardDrives()) != 0 and profile.getPreference('sdpath'):
				removableStorage.ejectDrive(profile.getPreference('sdpath'))
				self.saveStatusText._label = _("SD Card Ejected")

		except:
			self.saveStatusText._label = _("Unable to Eject SD Card")
	def CloseSavePrompt(self, e):
		self.saveMenuOpen = False
		self.sdSaveButton._hidden = True
		self.sdEjectButton._hidden = True
		self.directorySaveButton._hidden = True
		self.closeSaveButton._hidden = True
		self.saveText._hidden = True
		self.saveStatusText._hidden = True
		self.printTimeEstimationText._hidden = True
		self.saveStatusText._label = ""
	def _copyFile(self, fileA, fileB, allowEject = False):
		try:
			size = float(os.stat(fileA).st_size)
			with open(fileA, 'rb') as fsrc:
				with open(fileB, 'wb') as fdst:
					while 1:
						buf = fsrc.read(16*1024)
						if not buf:
							break
						fdst.write(buf)
						self.printButton.setProgressBar(float(fsrc.tell()) / size)
						self._queueRefresh()
		except:
			import sys
			print sys.exc_info()
			self.notification.message(_("Failed to save"))
		else:
			if allowEject:
				self.notification.message("Saved as %s" % (fileB), lambda : self.notification.message('You can now eject the card.') if removableStorage.ejectDrive(allowEject) else self.notification.message('Safe remove failed...'))
			else:
				self.notification.message("Saved as %s" % (fileB))
		self.printButton.setProgressBar(None)
		if fileA == self._slicer.getGCodeFilename():
			self._slicer.submitSliceInfoOnline()

	def _showSliceLog(self):
		dlg = wx.TextEntryDialog(self, "The slicing engine reported the following", "Engine log...", '\n'.join(self._slicer.getSliceLog()), wx.TE_MULTILINE | wx.OK | wx.CENTRE)
		dlg.ShowModal()
		dlg.Destroy()

	def OnToolSelect(self, button):
		if self.rotateToolButton.getSelected():
			self.tool = previewTools.toolRotate(self)
		elif self.scaleToolButton.getSelected():
			self.tool = previewTools.toolScale(self)
			
		#elif self.mirrorToolButton.getSelected():
		#	self.tool = previewTools.toolNone(self)
		else:
			self.tool = previewTools.toolNone(self)
		self.resetRotationButton.setHidden(not self.rotateToolButton.getSelected())
		self.layFlatButton.setHidden(not self.rotateToolButton.getSelected())
		
		for item in self.scaleList:
			item.setHidden(not self.scaleToolButton.getSelected())
		for item in self.rotateList:
			item.setHidden(not self.rotateToolButton.getSelected())
			
		for item in self.viewModeList:
			item.setHidden(not self.viewmodeOpen)
		for item in self.cameraList:
			item.setHidden(not self.scaleToolButton.getSelected())
			
		
		self.resetScaleButton.setHidden(not self.scaleToolButton.getSelected())
		self.rotationLockButton.setHidden(not self.scaleToolButton.getSelected())
		#self.resetScaleButton.setHidden(True)
		#self.scaleMaxButton.setHidden(not self.scaleToolButton.getSelected())
		self.scaleMaxButton.setHidden(True)
		#self.scaleForm.setHidden(not self.scaleToolButton.getSelected())
		self.scaleForm.setHidden(True)
		#self.mirrorXButton.setHidden(not self.mirrorToolButton.getSelected())
		#self.mirrorYButton.setHidden(not self.mirrorToolButton.getSelected())
		#self.mirrorZButton.setHidden(not self.mirrorToolButton.getSelected())
		self.mirrorXButton.setHidden(True)
		self.mirrorYButton.setHidden(True)
		self.mirrorZButton.setHidden(True)
	def updateToolButtons(self):
		if self._selectedObj is None:
			hidden = True
		else:
			hidden = False
		#self.rotateToolButton.setHidden(hidden)
		#self.scaleToolButton.setHidden(hidden)
		#self.mirrorToolButton.setHidden(hidden)
		if hidden:
			self.rotateToolButton.setSelected(False)
			self.scaleToolButton.setSelected(False)
			#self.mirrorToolButton.setSelected(False)
			self.OnToolSelect(0)

	def OnViewChange(self):
		if self.getModelView() == 4:
			self.viewMode = 'gcode'
			if self._gcode is not None and self._gcode.layerList is not None:
				self.layerSelect.setRange(1, len(self._gcode.layerList) - 1)
			self._selectObject(None)
			self.gcodeViewButton.setSelected(True)
			self.overhangViewButton.setSelected(False)
			self.modelViewButton.setSelected(False)
		elif self.getModelView() == 1:
			self.viewMode = 'overhang'
			self.gcodeViewButton.setSelected(False)
			self.overhangViewButton.setSelected(True)
			self.modelViewButton.setSelected(False)
		elif self.getModelView() == 2:
			self.viewMode = 'transparent'
		elif self.getModelView() == 3:
			self.viewMode = 'xray'
		else:
			self.viewMode = 'normal'
			self.gcodeViewButton.setSelected(False)
			self.overhangViewButton.setSelected(False)
			self.modelViewButton.setSelected(True)
		self.layerSelect.setHidden(self.viewMode != 'gcode')
		self.QueueRefresh()

	def OnRotateReset(self, button):
		if self._selectedObj is None:
			return
		self._selectedObj.resetRotation()
		self._scene.pushFree()
		self._selectObject(self._selectedObj)
		self.sceneUpdated()

	def OnLayFlat(self, button):
		if self._selectedObj is None:
			return
		self._selectedObj.layFlat()
		self._scene.pushFree()
		self._selectObject(self._selectedObj)
		self.sceneUpdated()

	def OnScaleReset(self, button):
		if self._selectedObj is None:
			return
		self._selectedObj.resetScale()
		self._selectObject(self._selectedObj)
		self.updateProfileToControls()
		self.sceneUpdated()
		
	def OnRotationLock(self, button):
		if button.getImageID() == 32:
			self.rotationLock = False
			button.setImageID(33)
		else:
			button.setImageID(32)
			self.rotationLock = True
		self.sceneUpdated()
		

	def OnScaleMax(self, button):
		if self._selectedObj is None:
			return
		self._selectedObj.scaleUpTo(self._machineSize - numpy.array(profile.calculateObjectSizeOffsets() + [0.0], numpy.float32) * 2 - numpy.array([1,1,1], numpy.float32))
		self._scene.pushFree()
		self._selectObject(self._selectedObj)
		self.updateProfileToControls()
		self.sceneUpdated()
	def supportOnOff(self, button):
		if button.getImageID() == 9:
			profile.putProfileSetting('support', 'Exterior Only')
			button.setImageID(10)
		else:
			profile.putProfileSetting('support', 'None')
			button.setImageID(9)
			
	def supportOff(self, button):
		profile.putProfileSetting('support', 'None')
		
	def supportExt(self, button):
		profile.putProfileSetting('support', 'Exterior Only')

	def supportAll(self, button):
		profile.putProfileSetting('support', 'Everywhere')

			
	def vaseOnOff(self, button):
		if button.getImageID() == 9:
			button.setImageID(10)
			#print profile.getProfileSettingFloat('fill_density')
			profile.putProfileSetting('temp_infill', profile.getProfileSettingFloat('fill_density'))
			profile.putProfileSetting('fill_density', '0')
			profile.putProfileSetting('vase', 'True')
			profile.putProfileSetting('top_surface_thickness_layers', '0')
			self.infillText.setTooltip(str(int(profile.getProfileSettingFloat('fill_density'))) + '%')
			self.sceneUpdated()
			
		else:
			button.setImageID(9)
			#profile.putProfileSetting('temp_infill', )
			profile.putProfileSetting('fill_density', profile.getProfileSettingFloat('temp_infill'))
			profile.putProfileSetting('vase', 'False')
			profile.putProfileSetting('top_surface_thickness_layers', profile.getProfileSettingDefault('top_surface_thickness_layers'))
			self.infillText.setTooltip(str(int(profile.getProfileSettingFloat('fill_density'))) + '%')
			self.sceneUpdated()

	def changeToCustom(self, e):
		profile.putPreference('machine_width',profile.getProfileSettingFloat('custom_machine_width'))
		profile.putPreference('machine_depth', profile.getProfileSettingFloat('custom_machine_depth'))
		profile.putPreference('machine_height', profile.getProfileSettingFloat('custom_machine_height'))
		self.machineText.setTooltip('Custom 3D Printer')
		self.sceneUpdated()
		self.updateProfileToControls()

	def brimOn(self, e):
		profile.putProfileSetting('skirt_gap', '0')
		profile.putProfileSetting('skirt_line_count', '5')

	def brimOff(self, e):
		profile.putProfileSetting('skirt_gap', '3')
		profile.putProfileSetting('skirt_line_count', '3')

	def changeToLitto(self, e):
		profile.putPreference('machine_width', '130')
		profile.putPreference('machine_depth', '120')
		profile.putPreference('machine_height', '175')
		self.machineText.setTooltip('Litto 3D Printer')
		self.sceneUpdated()
		self.updateProfileToControls()

	def changeToDitto(self, e):
		profile.putPreference('machine_width', '210')
		profile.putPreference('machine_depth', '180')
		profile.putPreference('machine_height', '230')
		self.machineText.setTooltip('Ditto+ 3D Printer')
		self.sceneUpdated()
		self.updateProfileToControls()

	def changeToDittoPro(self, e):
		profile.putPreference('machine_width', '219')
		profile.putPreference('machine_depth', '165')
		profile.putPreference('machine_height', '219')
		self.machineText.setTooltip(_('DittoPro 3D Printer'))
		self.sceneUpdated()
		self.updateProfileToControls()

	def lowResolution(self, e):
		profile.putProfileSetting('layer_height', '0.3')
		profile.putProfileSetting('edge_width_mm', '0.44')
		profile.putProfileSetting('print_flow', '0.94')
		profile.putProfileSetting('infill_width', '0.4')
		profile.putProfileSetting('bridge_feed_ratio', '100')
		profile.putProfileSetting('bridge_flow_ratio', '105')

		#profile.putProfileSetting('perimeter_flow_ratio', '75')

		profile.putProfileSetting('top_surface_thickness_layers', '3')

		self.resolutionText.setTooltip('Low: 300 micron')
		self.sceneUpdated()
		self.updateProfileToControls()
	def medResolution(self, e):
		profile.putProfileSetting('layer_height', '0.2')
		profile.putProfileSetting('edge_width_mm', '0.44')
		profile.putProfileSetting('print_flow', '1')
		#profile.putProfileSetting('edge_width_mm', '0.15')
		profile.putProfileSetting('infill_width', '0.4')
		profile.putProfileSetting('bridge_feed_ratio', '100')
		profile.putProfileSetting('bridge_flow_ratio', '105')

		#profile.putProfileSetting('perimeter_flow_ratio', '75')

		profile.putProfileSetting('top_surface_thickness_layers', '3')

		self.resolutionText.setTooltip('Medium: 200 micron')
		self.sceneUpdated()
		self.updateProfileToControls()

	def highResolution(self, e):
		profile.putProfileSetting('layer_height', '0.1')
		profile.putProfileSetting('edge_width_mm', '0.4')
		profile.putProfileSetting('print_flow', '1')
		#profile.putProfileSetting('edge_width_mm', '0.15') #220

		profile.putProfileSetting('infill_width', '0.4')
		profile.putProfileSetting('bridge_feed_ratio', '90')
		profile.putProfileSetting('bridge_flow_ratio', '155')
		
		#profile.putProfileSetting('perimeter_flow_ratio', '75')
		
		profile.putProfileSetting('top_surface_thickness_layers', '6')
		
		self.resolutionText.setTooltip('High: 100 micron')
		self.sceneUpdated()
		self.updateProfileToControls()

	def ultraResolution(self, e):

		profile.putProfileSetting('layer_height', '0.05')
		profile.putProfileSetting('edge_width_mm', '0.44')
		#profile.putProfileSetting('edge_width_mm', '0.15') //220
		profile.putProfileSetting('print_flow', '1.20') #20% increase
		#profile.putProfileSetting('bottom_thickness', '0.15')

		profile.putProfileSetting('infill_width', '0.4')
		profile.putProfileSetting('bridge_feed_ratio', '90')
		profile.putProfileSetting('bridge_flow_ratio', '150')
		
		#profile.putProfileSetting('perimeter_flow_ratio', '75')
		
		profile.putProfileSetting('top_surface_thickness_layers', '12')
		
		self.resolutionText.setTooltip('Ultra: 50 micron')
		self.sceneUpdated()
		self.updateProfileToControls()
		
	def decreaseInfill(self, e):
		if profile.getProfileSetting('vase') == 'True':
			return	#TODO: put popup saying vase is enabled therefore infill is set to 0. disable vase to change infill settings.	
		if int(self.infillCounter) > 0:
			#profile.putProfileSetting('fill_density', profile.getProfileSettingFloat('fill_density')-1)
			self.infillPlusCounter = 0
			self.infillMinusCounter +=1
			if 5 < self.infillMinusCounter < 10:
				self.infillCounter -= 2
			elif 11 < self.infillMinusCounter:
				self.infillCounter -= 5
			else:
				self.infillCounter -= 1
			if self.infillCounter < 0:
				self.infillCounter = 0
			self.infillText.setTooltip(str(self.infillCounter) + '%')
			self.sceneUpdated()
			self.updateProfileToControls()

	def increaseInfill(self, e):
		if profile.getProfileSetting('vase') == 'True':
			return #TODO: put popup saying vase is enabled therefore infill is set to 0. disable vase to change infill settings.
		if int(self.infillCounter) < 100:
			#profile.putProfileSetting('fill_density', profile.getProfileSettingFloat('fill_density')+1)
			
			self.infillPlusCounter += 1
			self.infillMinusCounter = 0
			if 5 < self.infillPlusCounter < 10:
				self.infillCounter += 2
			elif 11 < self.infillPlusCounter:
				self.infillCounter += 5
			else:
				self.infillCounter += 1
			if self.infillCounter > 100:
				self.infillCounter = 100
			self.infillText.setTooltip(str(self.infillCounter) + '%')

			#self.infillText.setTooltip(str(int(profile.getProfileSettingFloat('fill_density'))) + '%')
			self.sceneUpdated()
			self.updateProfileToControls()

		
	def	decreaseFilament(self, e):
		#profile.putProfileSetting('filament_diameter', profile.getProfileSettingFloat('filament_diameter')-0.01)
		self.filamentCounter -= 0.01
		self.filamentText.setTooltip(str(self.filamentCounter))
		self.sceneUpdated()
		self.updateProfileToControls()
		
	def	increaseFilament(self, e):
		#profile.putProfileSetting('filament_diameter', profile.getProfileSettingFloat('filament_diameter')+0.01)
		self.filamentCounter += 0.01
		self.filamentText.setTooltip(str(self.filamentCounter))
		#self.filamentText.setTooltip(str(profile.getProfileSettingFloat('filament_diameter')))
		self.sceneUpdated()
		self.updateProfileToControls()

	def decreaseWallThickness(self, e):
		if int(self.wallCounter) > 1:
			self.wallCounter -= 1
			#profile.putProfileSetting('wall_thickness', profile.getProfileSettingFloat('wall_thickness')-1)
			self.shellText.setTooltip(str(self.wallCounter))
			self.sceneUpdated()
			self.updateProfileToControls()
		#getProfileSetting
	def increaseWallThickness(self, e):
		self.wallCounter += 1
		#profile.putProfileSetting('wall_thickness', profile.getProfileSettingFloat('wall_thickness')+1)
		self.shellText.setTooltip(str(self.wallCounter))
		#self.shellText.setTooltip(str(int(profile.getProfileSettingFloat('wall_thickness'))))
		self.sceneUpdated()
		self.updateProfileToControls()
		#getProfileSetting
		
	def decreaseSupport(self, e):
		if int(self.supportCounter) > 1:
			self.supportCounter -= 1
			#profile.putProfileSetting('wall_thickness', profile.getProfileSettingFloat('wall_thickness')-1)
			self.supportText.setTooltip(str(self.supportCounter)+self._degree )
			self.sceneUpdated()
			self.updateProfileToControls()
		#getProfileSetting
	def increaseSupport(self, e):
		self.supportCounter += 1
		#profile.putProfileSetting('wall_thickness', profile.getProfileSettingFloat('wall_thickness')+1)
		self.supportText.setTooltip(str(self.supportCounter)+self._degree )
		#self.shellText.setTooltip(str(int(profile.getProfileSettingFloat('wall_thickness'))))
		self.sceneUpdated()
		self.updateProfileToControls()
		#getProfileSetting
		
	def decreasePrintSpeed(self, e):
		if int(self.speedCounter) > 0:
			#profile.putProfileSetting('print_speed', profile.getProfileSettingFloat('print_speed')-5)
			self.speedCounter -= 5
			self.speedText.setTooltip(str(int(self.speedCounter)) + "mm/s")
			self.sceneUpdated()
			self.updateProfileToControls()
		#getProfileSetting
		
	def increasePrintSpeed(self, e):
		if int(self.speedCounter) < 120:
			#profile.putProfileSetting('print_speed', profile.getProfileSettingFloat('print_speed')+5)
			self.speedCounter += 5
			self.speedText.setTooltip(str(int(self.speedCounter)) + "mm/s")
			self.sceneUpdated()
			self.updateProfileToControls()
		#getProfileSetting
	
	def decreaseTemperature(self, e):
		if int(self.temperatureCounter) > 0:
			self.temperatureCounter -= 5
			#profile.putProfileSetting('print_temperature', profile.getProfileSettingFloat('print_temperature')-5)
			self.temperatureText.setTooltip(str(int(self.temperatureCounter)) + self._degree + "C")
			self.sceneUpdated()
			self.updateProfileToControls()
		
	def increaseTemperature(self, e):
		if int(self.temperatureCounter) < 240:
			self.temperatureCounter += 5
			#profile.putProfileSetting('print_temperature', profile.getProfileSettingFloat('print_temperature')+5)
			self.temperatureText.setTooltip(str(int(self.temperatureCounter)) + self._degree + "C")
			self.sceneUpdated()
			self.updateProfileToControls()
	
	def decreaseBedTemperature(self, e):
		if int(self.temperaturebedCounter) > 0:
			#profile.putProfileSetting('print_bed_temperature', profile.getProfileSettingFloat('print_bed_temperature')-5)
			self.temperaturebedCounter -= 5
			self.bedTemperatureText.setTooltip(str(int(self.temperaturebedCounter)) + self._degree + "C")
			self.sceneUpdated()
			self.updateProfileToControls()
		
	def increaseBedTemperature(self, e):
		if int(self.temperaturebedCounter) < 150:
			#profile.putProfileSetting('print_bed_temperature', profile.getProfileSettingFloat('print_bed_temperature')+5)
			self.temperaturebedCounter += 5
			self.bedTemperatureText.setTooltip(str(int(self.temperaturebedCounter)) + self._degree + "C")
			self.sceneUpdated()
			self.updateProfileToControls()
		
	#def OnSettingChange(self, e):
	#	if self.type == 'profile':
	#		profile.putProfileSetting(self.configName, self.GetValue())
	#	else:
	#		profile.putPreference(self.configName, self.GetValue())
		
	def OnMirror(self, axis):
		if self._selectedObj is None:
			return
		self._selectedObj.mirror(axis)
		self.sceneUpdated()

	def OnScaleEntry(self, value, axis):
		if self._selectedObj is None:
			return
		try:
			value = float(value)
		except:
			return
		self._selectedObj.setScale(value/100, axis, self.rotationLock)
		self.updateProfileToControls()
		self._scene.pushFree()
		self._selectObject(self._selectedObj)
		self.sceneUpdated()

	def OnScaleEntryMM(self, value, axis):
		if self._selectedObj is None:
			return
		try:
			value = float(value)
		except:
			return
		self._selectedObj.setSize(value, axis, self.rotationLock)
		self.updateProfileToControls()
		self._scene.pushFree()
		self._selectObject(self._selectedObj)
		self.sceneUpdated()

	def OnDeleteAll(self, e):
		while len(self._scene.objects()) > 0:
			self._deleteObject(self._scene.objects()[0])
		self._animView = openglGui.animation(self, self._viewTarget.copy(), numpy.array([0,0,0], numpy.float32), 0.5)
	def deleteSelection(self, e):
		if self._selectedObj is not None:
			self._deleteObject(self._selectedObj)
			self.QueueRefresh()
	
	def cameraTop(self,e):
		self._yaw = 0
		self._pitch = 75
		self._zoom = 800
		self._viewTarget[0] = -4
		self._viewTarget[1] = 315
	def cameraSide(self,e):
		self._yaw = -90
		self._pitch = 77
		self._zoom = 910
		self._viewTarget[0] = -393
		self._viewTarget[1] = 1
	def cameraFront(self,e):
		self._yaw = 0
		self._pitch = 0
		self._zoom = 550
		self._viewTarget[0] = -2
		self._viewTarget[1] = -2
	def cameraDefault(self,e):
		self._yaw = -20
		self._pitch = 59
		self._zoom = 339
		self._viewTarget[0] = 0
		self._viewTarget[1] = 0
		
		
	def cameraChange(self):
		if self.cameraMode == 'default':
			self._yaw = 0
			self._pitch = 75
			self._zoom = 800
			self._viewTarget[0] = -4
			self._viewTarget[1] = 315
			self.cameraMode = 'front'
		elif self.cameraMode == 'front':
			self._yaw = 0
			self._pitch = 0
			self._zoom = 550
			self._viewTarget[0] = -2
			self._viewTarget[1] = -2
			self.cameraMode = 'top'
		elif self.cameraMode == 'top':
			self._yaw = -90
			self._pitch = 77
			self._zoom = 910
			self._viewTarget[0] = -393
			self._viewTarget[1] = 1
			self.cameraMode = 'right'
		else:
			self._yaw = -20
			self._pitch = 59
			self._zoom = 339
			self._viewTarget[0] = 0
			self._viewTarget[1] = 0
			self.cameraMode = 'default'
		self.sceneUpdated()
	def OnMultiply(self, e):
		if self._focusObj is None:
			return
		obj = self._focusObj
		dlg = wx.NumberEntryDialog(self, _("How many copies do you want?"), _("Copies"), _("Multiply"), 1, 1, 100)
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		busyInfo = wx.BusyInfo(_("working... please wait..."), self)
		cnt = dlg.GetValue()
		dlg.Destroy()
		n = 0
		while True:
			n += 1
			newObj = obj.copy()
			self._scene.add(newObj)
			self.list.append(newObj)
			self._scene.centerAll()
			#if not self._scene.checkPlatform(newObj):
			#	break
			if n > cnt:
				break
		#if n <= cnt:
		#	self.notification.message("Could not create more then %d items" % (n - 1))
		self._scene.remove(newObj)
		self._scene.centerAll()
		self.sceneUpdated()

	def OnSplitObject(self, e):
		if self._focusObj is None:
			return
		self._scene.remove(self._focusObj)
		for obj in self._focusObj.split(self._splitCallback):
			if numpy.max(obj.getSize()) > 2.0:
				self._scene.add(obj)
				self.list.append(obj)
		self._scene.centerAll()
		self._selectObject(None)
		self.sceneUpdated()
	def OnCenter(self, e):
		if self._focusObj is None:
			return
		self._focusObj.setPosition(numpy.array([0.0, 0.0]))
		self._scene.pushFree()
		newViewPos = numpy.array([self._focusObj.getPosition()[0], self._focusObj.getPosition()[1], self._focusObj.getSize()[2] / 2])
		self._animView = openglGui.animation(self, self._viewTarget.copy(), newViewPos, 0.5)
		self.sceneUpdated()
	def _splitCallback(self, progress):
		print progress

	def OnMergeObjects(self, e):
		if self._selectedObj is None or self._focusObj is None or self._selectedObj == self._focusObj:
			print "could not merge"
			return
		self._scene.merge(self._selectedObj, self._focusObj)
		self.sceneUpdated()

	def sceneUpdated(self):
		self._sceneUpdateTimer.Start(500, True)
		#self._slicer.abortSlicer()
		self._scene.setSizeOffsets(numpy.array(profile.calculateObjectSizeOffsets(), numpy.float32))
		self.QueueRefresh()

	def _onRunSlicer(self, e):
		#if self._isSimpleMode:
		#	self.GetTopLevelParent().simpleSettingsPanel.setupSlice()
		#self._slicer.runSlicer(self._scene)
		if self._isSimpleMode:
			profile.resetTempOverride()

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

	def _loadGCode(self):
		self._gcode.progressCallback = self._gcodeLoadCallback
		self._gcode.load(self._gcodeFilename)

	def _gcodeLoadCallback(self, progress):
		if self._gcode is None:
			return True
		if len(self._gcode.layerList) % 15 == 0:
			time.sleep(0.1)
		if self._gcode is None:
			return True
		self.layerSelect.setRange(1, len(self._gcode.layerList) - 1)
		if self.viewMode == 'gcode':
			self._queueRefresh()
		self.Refresh()
		return False

	def loadScene(self, fileList):
		self.busyInfo = wx.BusyInfo(_("loading model... please wait..."), self)
		for filename in fileList:
			try:
				objList = meshLoader.loadMeshes(filename)
			except MemoryError:
				traceback.print_exc()
				dial = wx.MessageDialog(None, "The model could not be imported because it is too large. Try reducing the number of polygons/triangles and importing again.", "Error encountered during Model Import", wx.OK|wx.ICON_EXCLAMATION)
				dial.ShowModal()
				dial.Destroy()
				self.busyInfo = None

			else:
				self.busyInfo = None
				for obj in objList:
					if self._objectLoadShader is not None:
						obj._loadAnim = openglGui.animation(self, 0, 0, 0.1) #j
					else:
						obj._loadAnim = None
					self._scene.add(obj)
					#stl.saveAsSTL(obj._meshList[0], filename)
					#print obj._meshList[0]
					item = ProjectObject(self, filename)
					self.list.append(item)
					self._scene.centerAll()
					self._selectObject(obj)
					#print obj
		self.sceneUpdated()

	def _deleteObject(self, obj):
		if obj == self._selectedObj:
			self._selectObject(None)
		if obj == self._focusObj:
			self._focusObj = None
		self._scene.remove(obj)
		for m in obj._meshList:
			if m.vbo is not None and m.vbo.decRef():
				self.glReleaseList.append(m.vbo)
		import gc
		gc.collect()
		self.sceneUpdated()

	def _selectObject(self, obj, zoom = True):
		if obj != self._selectedObj:
			self._selectedObj = obj
			self.updateProfileToControls()
			self.updateToolButtons()
		if zoom and obj is not None:
			newViewPos = numpy.array([obj.getPosition()[0], obj.getPosition()[1], obj.getMaximum()[2] / 2])
			self._animView = openglGui.animation(self, self._viewTarget.copy(), newViewPos, 0.5)
			newZoom = obj.getBoundaryCircle() * 6
			if newZoom > numpy.max(self._machineSize) * 3:
				newZoom = numpy.max(self._machineSize) * 3
			self._animZoom = openglGui.animation(self, self._zoom, newZoom, 0.5)
	def updateScaleForm(self, x, y, z, scaleX, scaleY, scaleZ, axis):
		if self._selectedObj is not None:
			#scale = self._selectedObj.getScale()
			#size = self._selectedObj.getSize()
			#str(int(round(float(scale[0])*100)))
			self.scaleXmmctrl.setValue(round(x, 1))
			self.scaleYmmctrl.setValue(round(y, 1))
			self.scaleZmmctrl.setValue(round(z, 1))
			

			if axis == "X":
				self.scaleXctrl.setValue(int(round(float(scaleX)*100)))
			elif axis == "Y":	
				self.scaleYctrl.setValue(int(round(float(scaleY)*100)))
			elif axis == "Z":
				self.scaleZctrl.setValue(int(round(float(scaleZ)*100)))
			elif axis == "XYZ":
				self.scaleXctrl.setValue(int(round(float(scaleX)*100)))
				self.scaleYctrl.setValue(int(round(float(scaleY)*100)))
				self.scaleZctrl.setValue(int(round(float(scaleZ)*100)))
			
	def updateProfileToControls(self):
		oldSimpleMode = self._isSimpleMode
		self._isSimpleMode = profile.getPreference('startMode') == 'Simple'
		if self._isSimpleMode and not oldSimpleMode:
			self._scene.arrangeAll()
			self.sceneUpdated()
		self._machineSize = numpy.array([profile.getPreferenceFloat('machine_width'), profile.getPreferenceFloat('machine_depth'), profile.getPreferenceFloat('machine_height')])
		self._objColors[0] = profile.getPreferenceColour('model_colour')
		self._objColors[1] = profile.getPreferenceColour('model_colour2')
		self._objColors[2] = profile.getPreferenceColour('model_colour3')
		self._objColors[3] = profile.getPreferenceColour('model_colour4')
		self._scene.setMachineSize(self._machineSize)
		self._scene.setSizeOffsets(numpy.array(profile.calculateObjectSizeOffsets(), numpy.float32))
		self._scene.setHeadSize(profile.getPreferenceFloat('extruder_head_size_min_x'), profile.getPreferenceFloat('extruder_head_size_max_x'), profile.getPreferenceFloat('extruder_head_size_min_y'), profile.getPreferenceFloat('extruder_head_size_max_y'), profile.getPreferenceFloat('extruder_head_size_height'))

		if self._selectedObj is not None:
			scale = self._selectedObj.getScale()
			size = self._selectedObj.getSize()
			#str(int(round(float(scale[0])*100)))
			
			self.scaleXctrl.setValue(int(round(float(scale[0])*100)))
			self.scaleYctrl.setValue(int(round(float(scale[1])*100)))
			self.scaleZctrl.setValue(int(round(float(scale[2])*100)))
			self.scaleXmmctrl.setValue(round(size[0], 1))
			self.scaleYmmctrl.setValue(round(size[1], 1))
			self.scaleZmmctrl.setValue(round(size[2], 1))

	def OnKeyChar(self, keyCode):
		if keyCode == wx.WXK_DELETE or keyCode == wx.WXK_NUMPAD_DELETE:
			if self._selectedObj is not None:
				self._deleteObject(self._selectedObj)
				self.QueueRefresh()
		if keyCode == wx.WXK_UP:
			self.layerSelect.setValue(self.layerSelect.getValue() + 1)
			self.QueueRefresh()
			
			if len(self._konamCode) == 0:
				self._konamCode.append("U")
			elif len(self._konamCode) == 1:
				self._konamCode.append("U")
			else:
				self._konamCode = []

		elif keyCode == wx.WXK_DOWN:
			self.layerSelect.setValue(self.layerSelect.getValue() - 1)
			self.QueueRefresh()
			
			if len(self._konamCode) == 2:
				self._konamCode.append("D")
			elif len(self._konamCode) == 3:
				self._konamCode.append("D")
			else:
				self._konamCode = []
				
		elif keyCode == wx.WXK_LEFT:
			if len(self._konamCode) == 4:
				self._konamCode.append("L")
			elif len(self._konamCode) == 6:
				self._konamCode.append("L")
			else:
				self._konamCode = []
		elif keyCode == wx.WXK_RIGHT:
			if len(self._konamCode) == 5:
				self._konamCode.append("R")
			elif len(self._konamCode) == 7:
				self._konamCode.append("R")				
			else:
				self._konamCode = []
				
		elif keyCode == 98:
			if len(self._konamCode) == 8:
				self._konamCode.append("B")
			else:
				self._konamCode = []
		elif keyCode == 97:
			if len(self._konamCode) == 9:
				self._konamCode.append("A")
			else:
				self._konamCode = []
		elif keyCode == wx.WXK_RETURN:
			if len(self._konamCode) == 10:
				print self._konamCode
				self._konamCode = []
				ecw = expertConfig.expertConfigWindow(self)
				ecw.Centre()
				ecw.Show(True)
				return
				
		elif keyCode == wx.WXK_PAGEUP:
			self.layerSelect.setValue(self.layerSelect.getValue() + 10)
			self.QueueRefresh()
		elif keyCode == wx.WXK_PAGEDOWN:
			self.layerSelect.setValue(self.layerSelect.getValue() - 10)
			self.QueueRefresh()
		
		
		if keyCode == wx.WXK_F3 and wx.GetKeyState(wx.WXK_SHIFT):
			shaderEditor(self, self.ShaderUpdate, self._objectLoadShader.getVertexShader(), self._objectLoadShader.getFragmentShader())
		if keyCode == wx.WXK_F4 and wx.GetKeyState(wx.WXK_SHIFT):
			from collections import defaultdict
			from gc import get_objects
			self._beforeLeakTest = defaultdict(int)
			for i in get_objects():
				self._beforeLeakTest[type(i)] += 1
		if keyCode == wx.WXK_F5 and wx.GetKeyState(wx.WXK_SHIFT):
			from collections import defaultdict
			from gc import get_objects
			self._afterLeakTest = defaultdict(int)
			for i in get_objects():
				self._afterLeakTest[type(i)] += 1
			for k in self._afterLeakTest:
				if self._afterLeakTest[k]-self._beforeLeakTest[k]:
					print k, self._afterLeakTest[k], self._beforeLeakTest[k], self._afterLeakTest[k] - self._beforeLeakTest[k]
		if keyCode == wx.WXK_SPACE:
			self._konamCode = []
			self.cameraChange()
	def ShaderUpdate(self, v, f):
		s = opengl.GLShader(v, f)
		if s.isValid():
			self._objectLoadShader.release()
			self._objectLoadShader = s
			for obj in self._scene.objects():
				obj._loadAnim = openglGui.animation(self, 1, 0, 1.5)
			self.QueueRefresh()

	def OnMouseDown(self,e):
		#for b in self.supportLines:
		#	print b
		#print self.supportLines
		self._mouseX = e.GetX()
		self._mouseY = e.GetY()
		self._mouseClick3DPos = self._mouse3Dpos
		self._mouseClickFocus = self._focusObj
		#print self._mouseClick3DPos
		#self.xText.setTooltip("X: " + str(self._mouseClick3DPos[0]))
		#self.yText.setTooltip("Y: " + str(self._mouseClick3DPos[1]))
		#self.zText.setTooltip("Z: " + str(self._mouseClick3DPos[2]))
		###self._mouseClick3DPos
		#p = glReadPixels(self._mouseX, self._mouseY, 1, 1, GL_RGBA, GL_UNSIGNED_INT_8_8_8_8)[0][0] >> 8

		if e.ButtonDClick():
			self._mouseState = 'doubleClick'
		else:
			self._mouseState = 'dragOrClick'
		
		p0, p1 = self.getMouseRay(self._mouseX, self._mouseY)
		p0 -= self.getObjectCenterPos() - self._viewTarget
		p1 -= self.getObjectCenterPos() - self._viewTarget
		if self.tool.OnDragStart(p0, p1):
			self._mouseState = 'tool'
		if self._mouseState == 'dragOrClick':
			if e.GetButton() == 1:
				if self._focusObj is not None:
					self._selectObject(self._focusObj, False)
					self.QueueRefresh()
		if self.debug:
			if self._mouseState is not None and self.modelView == 4 and e.GetButton() == 1:
				###	
				z = max(0, self._mouseClick3DPos[2])
				p0, p1 = self.getMouseRay(self._mouseX, self._mouseY)
				p2, p3 = self.getMouseRay(e.GetX(), e.GetY())
				#p0+=self._viewTarget[0]
				#p1+=self._viewTarget[1]
				#p2+=self._viewTarget[0]
				#p3+=self._viewTarget[1]
				p0[2] -= z
				p1[2] -= z
				p2[2] -= z
				p3[2] -= z
				cursorZ0 = p0 - (p1 - p0) * (p0[2] / (p1[2] - p0[2])) +self._viewTarget[0]
				cursorZ1 = p2 - (p3 - p2) * (p2[2] / (p3[2] - p2[2])) +self._viewTarget[1]
				
				mouseBedX = cursorZ0[0]+(210.0/2)
				mouseBedY = cursorZ1[1]+(180.0/2)

				self.xText.setTooltip("X: " + str(mouseBedX))
				self.yText.setTooltip("Y: " + str(mouseBedY))
				#self.zText.setTooltip(str(self._viewTarget))
				
				#if not wx.GetKeyState(wx.WXK_SHIFT):
				
				self.trimList = []
				#print self.supportLines
				blag = []
				blag.append((( 105.008, 85.06700134,0.60000002),( 105.008, 85.06700134,0.60000002)))
				blag.append((( 105.008, 85.06700134,0.60000002),( 109.991,85.06700134, 0.60000002)))
				blag.append((( 109.992, 86.53299713 , 0.60000002),( 105.00800323 ,  86.53299713  ,  0.60000002)))
				
				for s in self.supportLines:
					x1 = s[0][0]
					y1 = s[0][1]
					x2 = s[1][0]
					y2 = s[1][1]
					z = s[0][2]
					if self.testCollision(mouseBedX, mouseBedY, x1, y1, x2, y2, z):
						#deleteSupport.delete(self.resultFilename, x1, y1, x2, y2, self)
						self.zText.setTooltip( str(x1)+ " " + str(y1) + " " + str(x2) + " " + str(y2) )

						self.trimList.append(s)
						#self.trimList.append((x1,y1,z))
						#self.trimList.append((x2,y2,z))

						#newSupportList = numpy.concatenate((newSupportList, s))

						#for layerVBOlist in self._gcodeVBOs:
						#	for vbo in layerVBOlist:
						#		self.glReleaseList.append(vbo)
						#self._gcodeVBOs = []
						#print self.trimList
						#self.OnSliceDone(self.resultFilename)
						#for x in xrange(1, len(self._gcode.layerList)):
								#self.glReleaseList.append(self._gcodeVBOs[x][8])
						#self._gcodeVBOs[z][8]._asdf = []
						#print self._gcodeVBOs[z][8]._asdf
						#for x in xrange(1, len(self._gcodeVBOs[z][8]._asdf)):
						#for x in xrange(1, len(self._gcode.layerList)):
							#print "old"
							#print self._gcodeVBOs[x][8]._asdf
							#print "new"
							#print self._gcodeVBOs[x][8]._asdf[0:0,0:0]
							#print "---"
						#self._gcodeVBOs[z][8]._asdf = numpy.delete(self._gcodeVBOs[z][8]._asdf, 
					else:
						pass
						#self.zText.setTooltip("nope")
				for i in self.trimList:
					pass
					#print i[0][2]
					#if 0.299 < i[0][2] < 0.301:
						#pass
						#print i
				if not wx.GetKeyState(wx.WXK_SHIFT):
					for x in xrange(1, len(self._gcode.layerList)):
						self._gcodeVBOs[x][8]._asdf = self._gcodeVBOs[x][8]._asdf[0:0]
					
				newSupportList = numpy.zeros((0,3), numpy.float32)

				for j in self.trimList:
					newSupportList = numpy.concatenate((newSupportList, j))
				#print newSupportList
				newSupportList = newSupportList.reshape((-1 , 6))
				print newSupportList
				print "---"
				#ret = []
				#ret.append(opengl.GLVBO(newSupportList))
				#print ret._asdf
				#self._gcodeVBOs[2][8] = ret
				for x in newSupportList:
					print x
					z = x[2]
					#z = float(z) * 10
					#print x[2]
					if z%0.3 < 0.01 or z%0.3 > 0.299 :
						z = int(round(z/0.3)) #TODO. hahaha this doesn't work.
						
						
						#start = (x[0],x[1],x[2],x[0],x[1],x[2])
						#self._gcodeVBOs[z][8]._asdf = numpy.append(self._gcodeVBOs[z][8]._asdf, start)
						#print z
						#print "\n"
					#print z
						#if x not in self._gcodeVBOs[z][8]._asdf:
						
						#self._gcodeVBOs[z][8]._asdf = numpy.append(self._gcodeVBOs[z][8]._asdf, x) #ONLY ADD IF IT DOESNT EXIST
						
						self._gcodeVBOs[z][8]._asdf = numpy.append(self._gcodeVBOs[z][8]._asdf, x) #ONLY ADD IF IT DOESNT EXIST
						#self._gcodeVBOs[z][8]._asdf = numpy.sort(self._gcodeVBOs[z][8]._asdf) 

					#print self._gcodeVBOs[z][8]._asdf
						#self._gcodeVBOs[z][8]._asdf = numpy.append(self._gcodeVBOs[z][8]._asdf, ((110,110,0),(111,110,0)))
				#self._gcodeVBOs[2][8]._asdf = newSupportList
				#self._gcodeVBOs[2][8]._asdf = numpy.append(self._gcodeVBOs[2][8]._asdf, newSupportList)
				#print self._gcodeVBOs[1][8]._asdf 
				#print "***"
				self._gcodeVBOs[2][8]._asdf = self._gcodeVBOs[2][8]._asdf.reshape((-1 , 3))
				print len(self._gcodeVBOs[2][8]._asdf )
				print len(self._gcodeVBOs[2][7]._asdf )
				print self._gcodeVBOs[2][7]._asdf 
				print "---"
				print self._gcodeVBOs[2][8]._asdf 
				print "***"
				self._gcodeVBOs[2][8]._asdf = self._gcodeVBOs[2][8]._asdf.reshape((-1 , 3))

				#print self._gcodeVBOs[2][8]._asdf.reshape((len(self._gcodeVBOs[2][8]._asdf) / 2 , 6))
				#drawUpTill = min(len(self._gcode.layerList), self.layerSelect.getValue() + 1)
				
				#for x in xrange(1, len(self._gcode.layerList)):
				
				#print self._gcodeVBOs[2][7]._asdf

				
				if 0:
					drawUpTill = min(len(self._gcode.layerList), self.layerSelect.getValue() + 1)
					toRefresh = set()
					toTrim = set()
					count = 0
					#for n in xrange(1, len(self._gcode.layerList)):
					for n in xrange(1, 2):
					#n = 1
						a = self._gcodeVBOs[n][7]._asdf
						a = a.reshape((len(a) / 2 , 6))
						toDelete = []
						for j in self.trimList:
							#print j[0][2]
							
							for x in xrange(1, len(a)):
								#print 
								if str(j[0][2]) == str(a[x][5]): #z
									if str(j[0][0]) == str(a[x][0]): #x1
										if str(j[0][1]) == str(a[x][1]): #y1
											if str(j[1][0]) == str(a[x][3]): #x2
												if str(j[1][1]) == str(a[x][4]): #y2
													#count +=4
													if self.compareLines2(a[x],j):
														#self._gcodeVBOs[n][8]._asdf = numpy.append(self._gcodeVBOs[n][8]._asdf, [a[x]])
														#b = numpy.append(b, [a[x]])
														#toDelete.append(x)
														#toTrim.add(j)
														#self._gcodeVBOs[n][8]._asdf = b
														count +=1
						for k in toTrim:
							self.trimList.remove(k)
						toTrim = set()
						if len(toDelete) > 0:
							a = numpy.delete(a,[toDelete],0)
						#print a
							self._gcodeVBOs[n][7]._asdf = a.reshape((len(a) *2 , 3))

						self._gcodeVBOs[n][7].refresh()
						self._gcodeVBOs[n][8].refresh()

				n=1
				self.sceneUpdated()
				if len(self._gcodeVBOs[n][7]._asdf) > 0 and 0:
					print "old:"
					print self._gcodeVBOs[n][7]._asdf
					print "new:"
					self._gcodeVBOs[n][7]._asdf = self._gcodeVBOs[n][7]._asdf.reshape((len(self._gcodeVBOs[n][7]._asdf) /2 , 6))
					print self._gcodeVBOs[n][7]._asdf
					print "---"
					if len(self._gcodeVBOs[n][8]._asdf) == 0:
						#self._gcodeVBOs[n][8]._asdf = numpy.array([[10,10,0.3]])
						#for q in self._gcodeVBOs[n][7]._asdf:
						#self._gcodeVBOs[n][8]._asdf = numpy.concatenate((self._gcodeVBOs[n][8]._asdf, self._gcodeVBOs[n][7]._asdf))
						self._gcodeVBOs[n][8]._asdf = self._gcodeVBOs[n][7]._asdf
						self._gcodeVBOs[n][8].refresh()
						#print "victory"

					self._gcodeVBOs[n][7].refresh()
			try:
				for x in xrange(1, len(self._gcode.layerList)):
					#self._gcodeVBOs[x][7].refresh()
					self._gcodeVBOs[x][8].refresh()
			except:
				print "could not refresh"
				
						
	def testCollision(self, mouseX, mouseY, x1, y1, x2, y2, z):
		#given a line, create a rectangle (with a thickness of x) and see if the mouse pos collides with it!
		#for s in self.supportLines:
		currentZ = self.layerSelect.getValue()
		z = int(round(z/0.3)) #TODO. hahaha this doesn't work.
		if currentZ != z+1:
			pass
			#return False
		#print currentZ
		#print z
		#	x1 = s[0][0]
		#	y1 = s[0][1]
		#	x2 = s[1][0]
		#	y2 = s[1][1]
		if x1 < x2:
			x1 -= 0.3
			x2 += 0.3
		else:
			x1 += 0.3
			x2 -= 0.3
			
		if y1 < y2:
			y1 -= 0.3
			y2 += 0.3
		else:
			y1 += 0.3
			y2 -= 0.3
		betweenX = False
		betweenY = False
		
		if x1 > mouseX > x2 or x1 < mouseX < x2:
			betweenX = True
		if y1 > mouseY > y2 or y1 < mouseY < y2:
			betweenY = True
		
		if x1 == x2 and y1 == y2:
			print "yeah"
			#return True
			
		
		#if x1 > mouseX > x2 and y1 > mouseY > y2 or x1 < mouseX < x2 and y1 > mouseY > y2:
		if betweenX and betweenY:
			return True
		else:
			return False
			
	#	if x1-0.3 < mouseX < x2+0.3 and y1-0.3 < mouseY < y2+0.3 or x1+0.3 > mouseX > x2-0.3 and y1-0.3 < mouseY < y2+0.3:
		#	return True
		#else:
		#	return False
					
	def OnMouseUp(self, e):


		if self._selectedObj != None:
			profile.putPreference('selectedFile', self._selectedObj._name)
		else:
			profile.putPreference('selectedFile', '')
		if e.LeftIsDown() or e.MiddleIsDown() or e.RightIsDown():
			return
		if self._mouseState == 'dragOrClick':
			if e.GetButton() == 1:
				self._selectObject(self._focusObj)
			if e.GetButton() == 3:

					menu = wx.Menu()
					if self._focusObj is not None:
						self.Bind(wx.EVT_MENU, lambda e: self._deleteObject(self._focusObj), menu.Append(-1, _('Delete')))
						self.Bind(wx.EVT_MENU, self.OnMultiply, menu.Append(-1, _('Multiply')))
						self.Bind(wx.EVT_MENU, self.OnCenter, menu.Append(-1, _('Center on platform')))
						if version.isDevVersion():
							self.Bind(wx.EVT_MENU, self.OnSplitObject, menu.Append(-1, _('Split')))
					if self._selectedObj != self._focusObj and self._focusObj is not None and int(profile.getPreference('extruder_amount')) > 1:
						self.Bind(wx.EVT_MENU, self.OnMergeObjects, menu.Append(-1, 'Dual extrusion merge'))
					if len(self._scene.objects()) > 0:
						self.Bind(wx.EVT_MENU, self.OnDeleteAll, menu.Append(-1, _('Delete all')))
					if menu.MenuItemCount > 0:
						self.PopupMenu(menu)
					menu.Destroy()
		elif self._mouseState == 'dragObject' and self._selectedObj is not None:
			self._scene.pushFree()
			self.sceneUpdated()
		elif self._mouseState == 'tool':
			busyInfo = wx.BusyInfo(_("working... please wait..."), self)
			if self.tempMatrix is not None and self._selectedObj is not None:
				self._selectedObj.applyMatrix(self.tempMatrix)
				self._scene.pushFree()
				self._selectObject(self._selectedObj)
			self.tempMatrix = None
			self.tool.OnDragEnd()
			self.sceneUpdated()
			self.updateProfileToControls()
		self._mouseState = None

	def OnMouseMotion(self,e):
		p0, p1 = self.getMouseRay(e.GetX(), e.GetY())
		p0 -= self.getObjectCenterPos() - self._viewTarget
		p1 -= self.getObjectCenterPos() - self._viewTarget
		

		
		if e.Dragging() and self._mouseState is not None:
			if self._mouseState == 'tool':
				self.tool.OnDrag(p0, p1)
			elif not e.LeftIsDown() and not e.RightIsDown() and e.MiddleIsDown():
					a = math.cos(math.radians(self._yaw)) / 3.0
					b = math.sin(math.radians(self._yaw)) / 3.0
					self._viewTarget[0] += float(e.GetX() - self._mouseX) * -a
					self._viewTarget[1] += float(e.GetX() - self._mouseX) * b
					self._viewTarget[0] += float(e.GetY() - self._mouseY) * b
					self._viewTarget[1] += float(e.GetY() - self._mouseY) * a
					#print self._viewTarget[0]
					#print self._viewTarget[1]
					#print "-----------------"
			elif not e.LeftIsDown() and e.RightIsDown():
				self._mouseState = 'drag'
				if wx.GetKeyState(wx.WXK_SHIFT):
					a = math.cos(math.radians(self._yaw)) / 3.0
					b = math.sin(math.radians(self._yaw)) / 3.0
					self._viewTarget[0] += float(e.GetX() - self._mouseX) * -a
					self._viewTarget[1] += float(e.GetX() - self._mouseX) * b
					self._viewTarget[0] += float(e.GetY() - self._mouseY) * b
					self._viewTarget[1] += float(e.GetY() - self._mouseY) * a
				else:
					self._yaw += e.GetX() - self._mouseX
					self._pitch -= e.GetY() - self._mouseY
				if self._pitch > 180:
					self._pitch = 180
				if self._pitch < 0:
					self._pitch = 0
			#elif (e.LeftIsDown() and e.RightIsDown()) or e.MiddleIsDown():
			elif (e.LeftIsDown() and e.RightIsDown()):
				self._mouseState = 'drag'
				self._zoom += e.GetY() - self._mouseY
				if self._zoom < 1:
					self._zoom = 1
				if self._zoom > numpy.max(self._machineSize) * 3:
					self._zoom = numpy.max(self._machineSize) * 3
			elif e.LeftIsDown() and self._selectedObj is not None and self._selectedObj == self._mouseClickFocus:
				self._mouseState = 'dragObject'
				z = max(0, self._mouseClick3DPos[2])
				p0, p1 = self.getMouseRay(self._mouseX, self._mouseY)
				p2, p3 = self.getMouseRay(e.GetX(), e.GetY())
				p0[2] -= z
				p1[2] -= z
				p2[2] -= z
				p3[2] -= z
				cursorZ0 = p0 - (p1 - p0) * (p0[2] / (p1[2] - p0[2]))
				cursorZ1 = p2 - (p3 - p2) * (p2[2] / (p3[2] - p2[2]))
				diff = cursorZ1 - cursorZ0
				self._selectedObj.setPosition(self._selectedObj.getPosition() + diff[0:2])

		if not e.Dragging() or self._mouseState != 'tool':
			self.tool.OnMouseMove(p0, p1)

		self._mouseX = e.GetX()
		self._mouseY = e.GetY()


 
	def OnMouseWheel(self, e):
		if wx.GetKeyState(wx.WXK_SHIFT):
			delta = float(e.GetWheelRotation()) / float(e.GetWheelDelta())
			delta = max(min(delta,1),-1)
			self.layerSelect.setValue(int(self.layerSelect.getValue() + delta))
			self.Refresh()
			return
	
		delta = float(e.GetWheelRotation()) / float(e.GetWheelDelta())
		delta = max(min(delta,4),-4)
		self._zoom *= 1.0 - delta / 10.0
		if self._zoom < 1.0:
			self._zoom = 1.0
		if self._zoom > numpy.max(self._machineSize) * 4:
			self._zoom = numpy.max(self._machineSize) * 4
		self.Refresh()

	def OnMouseLeave(self, e):
		self._mouseX = -1

	def getMouseRay(self, x, y):
		if self._viewport is None:
			return numpy.array([0,0,0],numpy.float32), numpy.array([0,0,1],numpy.float32)
		p0 = opengl.unproject(x, self._viewport[1] + self._viewport[3] - y, 0, self._modelMatrix, self._projMatrix, self._viewport)
		p1 = opengl.unproject(x, self._viewport[1] + self._viewport[3] - y, 1, self._modelMatrix, self._projMatrix, self._viewport)
		p0 -= self._viewTarget
		p1 -= self._viewTarget
		return p0, p1

	def _init3DView(self):
		# set viewing projection
		size = self.GetSize()
		glViewport(0, 0, size.GetWidth(), size.GetHeight())
		glLoadIdentity()

		glLightfv(GL_LIGHT0, GL_POSITION, [0.2, 0.2, 1.0, 0.0])

		glDisable(GL_RESCALE_NORMAL)
		glDisable(GL_LIGHTING)
		glDisable(GL_LIGHT0)
		glEnable(GL_DEPTH_TEST)
		glDisable(GL_CULL_FACE)
		glDisable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

		glClearColor(1, 1, 1, 1.0)
		glClearStencil(0)
		glClearDepth(1.0)

		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		aspect = float(size.GetWidth()) / float(size.GetHeight())
		gluPerspective(45.0, aspect, 1.0, numpy.max(self._machineSize) * 4)

		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)

	def OnPaint(self,e):
		#if machineCom.machineIsConnected():
		#	self.printButton._imageID = 6
		#	self.printButton._tooltip = 'Print'
		#el


		if len(removableStorage.getPossibleSDcardDrives()) > 0:
			#self.printButton._imageID = 2
				drives = removableStorage.getPossibleSDcardDrives()
				#if len(drives) > 1:
				#	dlg = wx.SingleChoiceDialog(self, "Select SD drive", "Multiple removable drives have been found,\nplease select your SD card drive", map(lambda n: n[0], drives))
				#	if dlg.ShowModal() != wx.ID_OK:
				#		dlg.Destroy()
				#		return
				#	drive = drives[dlg.GetSelection()]
				#	dlg.Destroy()
				#else:
				drive = drives[0]
				if str(drive[1]) != str(profile.getPreference('sdpath')):
					#print drive
					#print profile.getPreference('sdpath')
					profile.putPreference('sdpath', drive[1])
		else:
			self.printButton._imageID = 26
			#self.printButton._tooltip = 'Save toolpath'
		if len(removableStorage.getPossibleSDcardDrives()) == 0 and profile.getPreference('sdpath'):
			profile.putPreference('sdpath', '')
			self.sdEjectButton._hidden = True
		elif len(removableStorage.getPossibleSDcardDrives()) > 0  and self.sdEjectButton._hidden == True and self.saveMenuOpen:
			self.sdEjectButton._hidden = False


		if self.sdSaveButton._focus:
			if len(removableStorage.getPossibleSDcardDrives()) > 0:
				self.saveText._label = _("Save to SD Card: [") + str(profile.getPreference('sdpath'))+"]"
				self.sdSaveButton._highlight = True
			else:
				self.saveText._label = _("No SD Card Detected")
				self.sdSaveButton._highlight = False
		elif self.directorySaveButton._focus:
			self.saveText._label = _("Browse Destination")
		elif self.sdEjectButton._focus:
			if len(removableStorage.getPossibleSDcardDrives()) > 0:
				self.saveText._label = _("Safely eject SD card")
			else:
				self.saveText._label = _("No SD Card Detected")
		else:
			self.saveText._label = _("Choose Save Destination")

		if not self._isSlicing and self.getProgressBar() is not None:
			self.setProgressBar(None)

		if self._animView is not None:
			self._viewTarget = self._animView.getPosition()
			if self._animView.isDone():
				self._animView = None
		if self._animZoom is not None:
			self._zoom = self._animZoom.getPosition()
			if self._animZoom.isDone():
				self._animZoom = None
		if self.viewMode == 'gcode' and self._gcode is not None:
			try:
				self._viewTarget[2] = self._gcode.layerList[self.layerSelect.getValue()][-1]['points'][0][2]
			except:
				pass
		if self._objectShader is None:
			if opengl.hasShaderSupport():
				self._objectShader = opengl.GLShader("""
varying float light_amount;

void main(void)
{
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    gl_FrontColor = gl_Color;

	light_amount = abs(dot(normalize(gl_NormalMatrix * gl_Normal), normalize(gl_LightSource[0].position.xyz)));
	light_amount += 0.2;
}
				""","""
varying float light_amount;

void main(void)
{
	gl_FragColor = vec4(gl_Color.xyz * light_amount, gl_Color[3]);
}
				""")
				self._objectOverhangShader = opengl.GLShader("""
uniform float cosAngle;
uniform mat3 rotMatrix;
varying float light_amount;

void main(void)
{
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    gl_FrontColor = gl_Color;

	light_amount = abs(dot(normalize(gl_NormalMatrix * gl_Normal), normalize(gl_LightSource[0].position.xyz)));
	light_amount += 0.2;
	if (normalize(rotMatrix * gl_Normal).z < -cosAngle)
	{
		light_amount = -10.0;
	}
}
				""","""
varying float light_amount;

void main(void)
{
	if (light_amount == -10.0)
	{
		gl_FragColor = vec4(1.0, 0.0, 0.0, gl_Color[3]);
	}else{
		gl_FragColor = vec4(gl_Color.xyz * light_amount, gl_Color[3]);
	}
}
				""")
				self._objectLoadShader = opengl.GLShader("""
uniform float intensity;
uniform float scale;
varying float light_amount;

void main(void)
{
	vec4 tmp = gl_Vertex;
    tmp.x += sin(tmp.z/5.0+intensity*30.0) * scale * intensity;
    tmp.y += sin(tmp.z/3.0+intensity*40.0) * scale * intensity;
    gl_Position = gl_ModelViewProjectionMatrix * tmp;
    gl_FrontColor = gl_Color;

	light_amount = abs(dot(normalize(gl_NormalMatrix * gl_Normal), normalize(gl_LightSource[0].position.xyz)));
	light_amount += 0.2;
}
			""","""
uniform float intensity;
varying float light_amount;

void main(void)
{
	gl_FragColor = vec4(gl_Color.xyz * light_amount, 1.0-intensity);
}
				""")
			if self._objectShader == None or not self._objectShader.isValid():
				self._objectShader = opengl.GLFakeShader()
				self._objectOverhangShader = opengl.GLFakeShader()
				self._objectLoadShader = None
		self._init3DView()

		glTranslate(0,0,-self._zoom)
		glRotate(-self._pitch, 1,0,0)
		glRotate(self._yaw, 0,0,1)
		glTranslate(-self._viewTarget[0],-self._viewTarget[1],-self._viewTarget[2])

		self._viewport = glGetIntegerv(GL_VIEWPORT)
		self._modelMatrix = glGetDoublev(GL_MODELVIEW_MATRIX)
		self._projMatrix = glGetDoublev(GL_PROJECTION_MATRIX)

		glClearColor(1,1,1,1)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)

		if self.viewMode != 'gcode':
			for n in xrange(0, len(self._scene.objects())):
				obj = self._scene.objects()[n]
				glColor4ub((n >> 16) & 0xFF, (n >> 8) & 0xFF, (n >> 0) & 0xFF, 0xFF)
				self._renderObject(obj)

		if self._mouseX > -1:
			glFlush()
			n = glReadPixels(self._mouseX, self.GetSize().GetHeight() - 1 - self._mouseY, 1, 1, GL_RGBA, GL_UNSIGNED_INT_8_8_8_8)[0][0] >> 8
			if n < len(self._scene.objects()):
				self._focusObj = self._scene.objects()[n]
			else:
				self._focusObj = None
			f = glReadPixels(self._mouseX, self.GetSize().GetHeight() - 1 - self._mouseY, 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT)[0][0]
			#self.GetTopLevelParent().SetTitle(hex(n) + " " + str(f))
			self._mouse3Dpos = opengl.unproject(self._mouseX, self._viewport[1] + self._viewport[3] - self._mouseY, f, self._modelMatrix, self._projMatrix, self._viewport)
			self._mouse3Dpos -= self._viewTarget

		self._init3DView()
		glTranslate(0,0,-self._zoom)
		glRotate(-self._pitch, 1,0,0)
		glRotate(self._yaw, 0,0,1)
		glTranslate(-self._viewTarget[0],-self._viewTarget[1],-self._viewTarget[2])

		if self.viewMode == 'gcode':
			if self._gcode is not None and self._gcode.layerList is None:
				self._gcodeLoadThread = threading.Thread(target=self._loadGCode)
				self._gcodeLoadThread.daemon = True
				self._gcodeLoadThread.start()
			if self._gcode is not None and self._gcode.layerList is not None:
				glPushMatrix()
				glTranslate(-self._machineSize[0] / 2, -self._machineSize[1] / 2, 0)
				t = time.time()
				drawUpTill = min(len(self._gcode.layerList), self.layerSelect.getValue() + 1)
				for n in xrange(0, drawUpTill):
					c = 1.0 - float(drawUpTill - n) / 15
					c = max(0.3, c)
					if len(self._gcodeVBOs) < n + 1:
						self._counter+=1
						self._gcodeVBOs.append(self._generateGCodeVBOs(self._gcode.layerList[n]))
						if time.time() - t > 0.5:
							self.QueueRefresh()
							break
					###['WALL-OUTER', 'WALL-INNER', 'FILL', 'SUPPORT', 'SKIRT', selected support]

					if n == drawUpTill - 1: #current layer
						#print len(self._gcodeVBOs[n])
						if len(self._gcodeVBOs[n]) < 10:
							self._gcodeVBOs[n] += self._generateGCodeVBOs2(self._gcode.layerList[n])

						glColor3ub(140, 198, 63) #perimeter
						self._gcodeVBOs[n][9].render(GL_QUADS)
						glColor3ub(0,0,0)#not sure
						self._gcodeVBOs[n][10].render(GL_QUADS)
						glColor3ub(204,204,204)#not sure
						self._gcodeVBOs[n][11].render(GL_QUADS)
						glColor3ub(255,0,0)#support? don't think so?
						self._gcodeVBOs[n][12].render(GL_QUADS)

						glColor3ub(57, 181, 74) #loops
						self._gcodeVBOs[n][13].render(GL_QUADS)
						glColor3ub(251, 176, 59) #infill
						self._gcodeVBOs[n][14].render(GL_QUADS)
						glColor3ub(204,204,204) #skirt
						self._gcodeVBOs[n][15].render(GL_QUADS)
						glColor3ub(0, 0, 204)
						self._gcodeVBOs[n][17].render(GL_QUADS)
						glColor3ub(204,204,204)#support
						self._gcodeVBOs[n][16].render(GL_QUADS)


					else: #not current layer
						glColor3ub(173, 203, 132) #perimeter
						self._gcodeVBOs[n][0].render(GL_LINES)
						glColor3ub(0, 0, 0) #does nothing
						#self._gcodeVBOs[n][1].render(GL_LINES)
						glColor3ub(0, 0, 0) #does nothing
						#self._gcodeVBOs[n][2].render(GL_LINES)
						glColor3ub(0, 0, 0) #does nothing
						#self._gcodeVBOs[n][3].render(GL_LINES)

						glColor3ub(190, 190, 190) #bridge i think
						self._gcodeVBOs[n][4].render(GL_LINES)

						#if n < 3:
						glColor3ub(255, 226, 183) #infill
						self._gcodeVBOs[n][5].render(GL_LINES)


						glColor3ub(204, 204, 204) #skirt
						self._gcodeVBOs[n][6].render(GL_LINES)


						glColor3ub(0, 0, 0) #Support2. doesn't seem to do anything
						#self._gcodeVBOs[n][8].render(GL_LINES)
						glColor3ub(204, 204, 204) #support
						self._gcodeVBOs[n][7].render(GL_LINES)
						#if len(self._gcodeVBOs[n][8]._asdf) != 0:
						#	for x in self._gcodeVBOs[n][8]._asdf:
						#		pass
								#print x
						#for p in self.trimList:
						#	if self._gcodeVBOs[n][6] == p:
						#		glColor3ub(204, 0, 0)


				glPopMatrix()
		else:
			glStencilFunc(GL_ALWAYS, 1, 1)
			glStencilOp(GL_INCR, GL_INCR, GL_INCR)

			if self.viewMode == 'overhang':
				self._objectOverhangShader.bind()
				self._objectOverhangShader.setUniform('cosAngle', math.cos(math.radians(90 - 60)))
			else:
				self._objectShader.bind()
			self._anObjectIsOutsidePlatform = True
			for obj in self._scene.objects():
				if obj._loadAnim is not None:
					if obj._loadAnim.isDone():
						obj._loadAnim = None
					else:
						continue


				brightness = 0.7
				if self._focusObj == obj:
					brightness = 0.8
				elif self._focusObj is not None or self._selectedObj is not None and obj != self._selectedObj:
					brightness = 0.7
				if self._selectedObj == obj:
					brightness = 1.2
				if self._selectedObj == obj or self._selectedObj is None:
					#If we want transparent, then first render a solid black model to remove the printer size lines.
					if self.viewMode == 'transparent':
						glColor4f(0, 0, 0, 0)
						self._renderObject(obj)
						glEnable(GL_BLEND)
						glBlendFunc(GL_ONE, GL_ONE)
						glDisable(GL_DEPTH_TEST)
						brightness *= 0.5
					if self.viewMode == 'xray':
						glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
					glStencilOp(GL_INCR, GL_INCR, GL_INCR)
					glEnable(GL_STENCIL_TEST)

				if self.viewMode == 'overhang':
					if self._selectedObj == obj and self.tempMatrix is not None:
						self._objectOverhangShader.setUniform('rotMatrix', obj.getMatrix() * self.tempMatrix)
					else:
						self._objectOverhangShader.setUniform('rotMatrix', obj.getMatrix())

				if not self._scene.checkPlatform(obj):
					glColor4f(0.5 * brightness, 0.5 * brightness, 0.5 * brightness, 0.8 * brightness)
					self._renderObject(obj)
					self._anObjectIsOutsidePlatform = False
				else:
					self._renderObject(obj, brightness)
				glDisable(GL_STENCIL_TEST)
				glDisable(GL_BLEND)
				glEnable(GL_DEPTH_TEST)
				glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)

			if self.viewMode == 'xray':
				glPushMatrix()
				glLoadIdentity()
				glEnable(GL_STENCIL_TEST)
				glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
				glDisable(GL_DEPTH_TEST)
				for i in xrange(2, 15, 2):
					glStencilFunc(GL_EQUAL, i, 0xFF)
					glColor(float(i)/10, float(i)/10, float(i)/5)
					glBegin(GL_QUADS)
					glVertex3f(-1000,-1000,-10)
					glVertex3f( 1000,-1000,-10)
					glVertex3f( 1000, 1000,-10)
					glVertex3f(-1000, 1000,-10)
					glEnd()
				for i in xrange(1, 15, 2):
					glStencilFunc(GL_EQUAL, i, 0xFF)
					glColor(float(i)/10, 0, 0)
					glBegin(GL_QUADS)
					glVertex3f(-1000,-1000,-10)
					glVertex3f( 1000,-1000,-10)
					glVertex3f( 1000, 1000,-10)
					glVertex3f(-1000, 1000,-10)
					glEnd()
				glPopMatrix()
				glDisable(GL_STENCIL_TEST)
				glEnable(GL_DEPTH_TEST)

			self._objectShader.unbind()

			glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
			glEnable(GL_BLEND)
			if self._objectLoadShader is not None:
				self._objectLoadShader.bind()
				glColor4f(0.2, 0.6, 1.0, 1.0)
				for obj in self._scene.objects():
					if obj._loadAnim is None:
						continue
					self._objectLoadShader.setUniform('intensity', obj._loadAnim.getPosition())
					self._objectLoadShader.setUniform('scale', obj.getBoundaryCircle() / 10)
					self._renderObject(obj)
				self._objectLoadShader.unbind()
				glDisable(GL_BLEND)

		self._drawMachine()

		if self.viewMode == 'gcode':
			if self._gcodeLoadThread is not None and self._gcodeLoadThread.isAlive():
				glDisable(GL_DEPTH_TEST)
				glPushMatrix()
				glLoadIdentity()
				glTranslate(0,-4,-10)
				glColor4ub(60,60,60,255)
				#opengl.glDrawStringCenter('Loading toolpath for visualization...')
				glPopMatrix()
		else:
			#Draw the object box-shadow, so you can see where it will collide with other objects.
			if self._selectedObj is not None and len(self._scene.objects()) > 0:
				size = self._selectedObj.getSize()[0:2] / 2 + self._scene.getObjectExtend()
				#print self._scene.getObjectExtend()
				glPushMatrix()
				glTranslatef(self._selectedObj.getPosition()[0], self._selectedObj.getPosition()[1], 0)
				glEnable(GL_BLEND)
				glEnable(GL_CULL_FACE)
				glColor4f(0,0,0,0.12)
				glBegin(GL_QUADS)
				glVertex3f(-size[0],  size[1], 0.1)
				glVertex3f(-size[0], -size[1], 0.1)
				glVertex3f( size[0], -size[1], 0.1)
				glVertex3f( size[0],  size[1], 0.1)
				glEnd()
				glDisable(GL_CULL_FACE)
				glPopMatrix()

			#Draw the outline of the selected object, on top of everything else except the GUI.
			if self._selectedObj is not None and self._selectedObj._loadAnim is None:
				glDisable(GL_DEPTH_TEST)
				glEnable(GL_CULL_FACE)
				glEnable(GL_STENCIL_TEST)
				glDisable(GL_BLEND)
				glStencilFunc(GL_EQUAL, 0, 255)

				glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
				glLineWidth(2)
				glColor4f(0,0,0,0.8)
				self._renderObject(self._selectedObj)
				glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

				glViewport(0, 0, self.GetSize().GetWidth(), self.GetSize().GetHeight())
				glDisable(GL_STENCIL_TEST)
				glDisable(GL_CULL_FACE)
				glEnable(GL_DEPTH_TEST)

			if self._selectedObj is not None:
				glPushMatrix()
				pos = self.getObjectCenterPos()
				glTranslate(pos[0], pos[1], pos[2])
				self.tool.OnDraw()
				glPopMatrix()
		if self.viewMode == 'overhang' and not opengl.hasShaderSupport():
			glDisable(GL_DEPTH_TEST)
			glPushMatrix()
			glLoadIdentity()
			glTranslate(0,-4,-10)
			glColor4ub(60,60,60,255)
			opengl.glDrawStringCenter('Overhang view not working due to lack of OpenGL shaders support.')
			glPopMatrix()

	def _renderObject(self, obj, brightness = False, addSink = False):
		glPushMatrix()
		if addSink:
			glTranslate(obj.getPosition()[0], obj.getPosition()[1], obj.getSize()[2] / 2 - profile.getProfileSettingFloat('object_sink'))
		else:
			glTranslate(obj.getPosition()[0], obj.getPosition()[1], obj.getSize()[2] / 2)

		if self.tempMatrix is not None and obj == self._selectedObj:
			tempMatrix = opengl.convert3x3MatrixTo4x4(self.tempMatrix)
			glMultMatrixf(tempMatrix)

		offset = obj.getDrawOffset()
		glTranslate(-offset[0], -offset[1], -offset[2] - obj.getSize()[2] / 2)

		tempMatrix = opengl.convert3x3MatrixTo4x4(obj.getMatrix())
		glMultMatrixf(tempMatrix)

		n = 0
		for m in obj._meshList:
			if m.vbo is None:
				m.vbo = opengl.GLVBO(m.vertexes, m.normal)
			if brightness:
				glColor4fv(map(lambda n: n * brightness, self._objColors[n]))
				n += 1
			m.vbo.render()
		glPopMatrix()

		
	def _drawMachine(self):
		#glEnable(GL_CULL_FACE)
		glEnable(GL_BLEND)
		#if profile.getPreference('machine_type') == 'ultimaker':

		glEnable(GL_FLAT);
		glEnable(GL_SMOOTH);
		glColor4f(.5,.5,.5,1)
		self._objectShader.bind()
		if self._machineSize[0] == 210:
			self._renderObject(self._platformditto, False, False)
			offset = 20
		elif self._machineSize[0] == 130:
			self._renderObject(self._platformlitto, False, False)
			offset = 15
		else:
			self._renderObject(self._platformdittopro, False, False)
			offset = 20
		self._objectShader.unbind()
		
		glColor4ub(0, 0, 0, 64)
		glLineWidth(1) #or whatever
		glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
		size = [profile.getPreferenceFloat('machine_width'), profile.getPreferenceFloat('machine_depth'), profile.getPreferenceFloat('machine_height')]
		v0 = [ size[0] / 2, size[1] / 2, size[2]]
		v1 = [ size[0] / 2,-size[1] / 2, size[2]]
		v2 = [-size[0] / 2, size[1] / 2, size[2]]
		v3 = [-size[0] / 2,-size[1] / 2, size[2]]
		v4 = [ size[0] / 2, size[1] / 2, 0]
		v5 = [ size[0] / 2,-size[1] / 2, 0]
		v6 = [-size[0] / 2, size[1] / 2, 0]
		v7 = [-size[0] / 2,-size[1] / 2, 0]
		
		vList = [v0,v1,v3,v2, v1,v0,v4,v5, v2,v3,v7,v6, v0,v2,v6,v4, v3,v1,v5,v7]
		glEnableClientState(GL_VERTEX_ARRAY)
		glVertexPointer(3, GL_FLOAT, 3*4, vList)

		
		
		#glColor4ub(5, 171, 231, 64)
		glDrawArrays(GL_QUADS, 0, 4)
		#glColor4ub(5, 171, 231, 96)
		glDrawArrays(GL_QUADS, 4, 8)
		#glColor4ub(5, 171, 231, 128)
		glDrawArrays(GL_QUADS, 12, 8)
		glDisableClientState(GL_VERTEX_ARRAY)
		
		
		

		sx = self._machineSize[0]
		sy = self._machineSize[1]
		for x in xrange(-int(sx/20)-1, int(sx / 20) + 1):
			for y in xrange(-int(sx/20)-1, int(sy / 20) + 1):
				x1 = x * 10
				x2 = x1 + 10
				y1 = y * 10
				y2 = y1 + 10
				x1 = max(min(x1, sx/2), -sx/2)
				y1 = max(min(y1, sy/2), -sy/2)
				x2 = max(min(x2, sx/2), -sx/2)
				y2 = max(min(y2, sy/2), -sy/2)
			#	if (x & 1) == (y & 1):
			#		glColor4ub(5, 171, 231, 127)
				#else:
				#	glColor4ub(5 * 8 / 10, 171 * 8 / 10, 231 * 8 / 10, 128)
				glBegin(GL_QUADS)
				glVertex3f(x1, y1, -0.02)
				glVertex3f(x2, y1, -0.02)
				glVertex3f(x2, y2, -0.02)
				glVertex3f(x1, y2, -0.02)
				glEnd()
				
				
		#Draw the object here
		glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
		
		if 1: #this is the grey ring around the grid. the shadow thing. 
			glColor4ub(0, 0, 0, 32)
			glBegin(GL_QUADS)
			glVertex3f(-sx/2-offset, sy/2, -0.02)
			glVertex3f(sx/2+offset, sy/2, -0.02)
			glVertex3f(sx/2+offset, sy/2+offset, -0.02)
			glVertex3f(-sx/2-offset, sy/2+offset, -0.02)
			glEnd()
					
			glBegin(GL_QUADS)
			glVertex3f(-sx/2-offset, -sy/2, -0.02)
			glVertex3f(sx/2+offset, -sy/2, -0.02)
			glVertex3f(sx/2+offset, -sy/2-offset, -0.02)
			glVertex3f(-sx/2-offset, -sy/2-offset, -0.02)
			glEnd()
			
			glBegin(GL_QUADS)
			glVertex3f(-sx/2-offset, sy/2, -0.02)
			glVertex3f(-sx/2, sy/2, -0.02)
			glVertex3f(-sx/2, -sy/2, -0.02)
			glVertex3f(-sx/2-offset, -sy/2, -0.02)
			glEnd()
					
			glBegin(GL_QUADS)
			glVertex3f(sx/2, sy/2, -0.02)
			glVertex3f(sx/2+offset, sy/2, -0.02)
			glVertex3f(sx/2+offset, -sy/2, -0.02)
			glVertex3f(sx/2, -sy/2, -0.02)
			glEnd()
				
		glLineWidth(1) #also or whatever
		glColor4ub(0, 0, 0, 64)
		glDisable(GL_BLEND)
		#glDisable(GL_CULL_FACE)
	def compareLines(self, line1, line2):
		L1x1 = line1[0][0]
		L1x1 = "%.4f" % L1x1

		L1y1 = line1[0][1]
		L1y1 = "%.4f" % L1y1
		
		L1z1 = line1[0][2]
		L1z1 = "%.4f" % L1z1
		
		L1x2 = line1[1][0]
		L1x2 = "%.4f" % L1x2
		
		L1y2 = line1[1][1]
		L1y2 = "%.4f" % L1y2
		
		L1z2 = line1[1][2]
		L1z2 = "%.4f" % L1z2
		#----
		L2x1 = line2[0][0]
		L2x1 = "%.4f" % L2x1

		L2y1 = line2[0][1]
		L2y1 = "%.4f" % L2y1
		
		L2z1 = line2[0][2]
		L2z1 = "%.4f" % L2z1
		
		L2x2 = line2[1][0]
		L2x2 = "%.4f" % L2x2
		
		L2y2 = line2[1][1]
		L2y2 = "%.4f" % L2y2
		
		L2z2 = line2[1][2]
		L2z2 = "%.4f" % L2z2
		
		if L1x1 == L2x1 and L1y1 == L2y1 and L1z1 == L2z1 and L1x2 == L2x2 and L1y2 == L2y2 and L1z2 == L2z2:
			#print "why"
			return True
		else:
			#print L1x1 , L2x1, L1y1 , L2y1, L1z1 , L2z1 , L1x2 , L2x2, L1y2 , L2y2, L1z2 , L2z2
			return False
	def compareLines2(self, line1, line2): #this one uses the format [0,1,2,3,4,5] for line 1 only
		L1x1 = line1[0]
		L1x1 = "%.4f" % L1x1

		L1y1 = line1[1]
		L1y1 = "%.4f" % L1y1
		
		#L1z1 = line1[2]
		#L1z1 = "%.4f" % L1z1
		
		L1x2 = line1[3]
		L1x2 = "%.4f" % L1x2
		
		L1y2 = line1[4]
		L1y2 = "%.4f" % L1y2
		
		#L1z2 = line1[5]
		#L1z2 = "%.4f" % L1z2
		#----
		L2x1 = line2[0][0]
		L2x1 = "%.4f" % L2x1

		L2y1 = line2[0][1]
		L2y1 = "%.4f" % L2y1
		
		#L2z1 = line2[0][2]
		#L2z1 = "%.4f" % L2z1
		
		L2x2 = line2[1][0]
		L2x2 = "%.4f" % L2x2
		
		L2y2 = line2[1][1]
		L2y2 = "%.4f" % L2y2
		
		#L2z2 = line2[1][2]
		#L2z2 = "%.4f" % L2z2
		
		#if L1x1 == L2x1 and L1y1 == L2y1 and L1z1 == L2z1 and L1x2 == L2x2 and L1y2 == L2y2 and L1z2 == L2z2:
		if L1x1 == L2x1 and L1y1 == L2y1 and L1x2 == L2x2 and L1y2 == L2y2:
			#print "why"
			return True
		else:
			#print L1x1 , L2x1, L1y1 , L2y1, L1z1 , L2z1 , L1x2 , L2x2, L1y2 , L2y2, L1z2 , L2z2
			return False
		
	def _generateGCodeVBOs(self, layer):
		ret = []
		#supportLines = set() #sets have no repeating elements
		blag = []
		blag.append([[ 113.360,94.400,0.3],[ 113.360,85.220,0.3]])
		blag.append([[ 113.360,85.220,0.3],[ 121.070,85.220,0.3]])
		#blag.append([[ 50.381,55.733,0.9],[ 79.619,55.733,0.9]])
		#blag.append([[ 50.381,55.733,1.2],[ 79.619,55.733,1.2]])

		for extrudeType in ['WALL-OUTER:0', 'WALL-OUTER:1', 'WALL-OUTER:2', 'WALL-OUTER:3', 'WALL-INNER', 'FILL', 'SKIRT', 'SUPPORT']:
			if ':' in extrudeType:
				extruder = int(extrudeType[extrudeType.find(':')+1:])
				extrudeType = extrudeType[0:extrudeType.find(':')]
			else:
				extruder = None
			pointList = numpy.zeros((0,3), numpy.float32)
			pointListSupport2 = numpy.zeros((0,3), numpy.float32)
			
			count = 0
			for path in layer:
				
				if path['type'] == 'extrude' and path['pathType'] == extrudeType and (extruder is None or path['extruder'] == extruder):
					a = path['points']
					a = numpy.concatenate((a[:-1], a[1:]), 1)
					b = a
					#print "old:"
					#print b
					#print "new:"
					a = a.reshape((len(a) * 2, 3))
					#print a
					#print "try:"
					#c = a.reshape((len(a) / 2, 6))
					#print c
					#print "---"
					#print len(a)
					if extrudeType == 'SUPPORT':
						for j in b:
							x1 = j[0]
							y1 = j[1]
							x2 = j[3]
							y2 = j[4]
							z = j[5]
							
							#c.reshape((len(c) * 2, 3))

							line = ((x1,y1,z),(x2,y2,z)) #can I just use j here instead?
							self.supportLines.append(line)
							#print self.supportLines
						#self.supportLines = numpy.concatenate((self.supportLines, b))
						#print self.supportLines
						found = False
						for line in []: #blag will turn into self.trimList
							#print line
							#print a
							#print "---"
							if self.compareLines(a,line):
								#pointListSupport2 = numpy.concatenate((pointListSupport2, a))
								found = True
						
						if not found:
							pointList = numpy.concatenate((pointList, a))
							#print pointListSupport2

					else:
						pointList = numpy.concatenate((pointList, a))
						"""
				if extrudeType == 'SUPPORT':
						# in here, make a b and c
						# b will have lines that are not selected, c are selected
						# iterate through a and then put not selected into b, selected into c
						b = numpy.array([])
						
						for k in a:
							numpy.concatenate(b,k)
						if a == b:
							print "they are equal"
						print b
						for j in b:
							x1 = j[0]
							y1 = j[1]
							x2 = j[3]
							y2 = j[4]
							z = j[5]
							
							#c.reshape((len(c) * 2, 3))
							if x1 == x2 and y1 == y2:
								pass
							else:
								line = ((x1,y1,z),(x2,y2,z)) #can I just use j here instead?
								self.supportLines.add(line)
							#print len(self.supportLines)
							#print line
							#print "------"
					else:
						c = 0
					"""
			#print pointList
			ret.append(opengl.GLVBO(pointList))
			if extrudeType == 'SUPPORT':
				ret.append(opengl.GLVBO(pointListSupport2))
				#print "bonus"
				#print pointList


			#print supportLines[0]
			#for q in supportLines:
			#	print q[0][0]
			#print "----"
		return ret

	def _generateGCodeVBOs2(self, layer):
		filamentRadius = profile.getProfileSettingFloat('filament_diameter') / 2
		filamentArea = math.pi * filamentRadius * filamentRadius

		#print layer
		ret = []
		for extrudeType in ['WALL-OUTER:0', 'WALL-OUTER:1', 'WALL-OUTER:2', 'WALL-OUTER:3', 'WALL-INNER', 'FILL', 'SKIRT', 'SUPPORT']:
			if ':' in extrudeType:
				extruder = int(extrudeType[extrudeType.find(':')+1:])
				extrudeType = extrudeType[0:extrudeType.find(':')]
			else:
				extruder = None
			pointList = numpy.zeros((0,3), numpy.float32)
			for path in layer:
				if path['type'] == 'extrude' and path['pathType'] == extrudeType and (extruder is None or path['extruder'] == extruder):
					a = path['points']
					if extrudeType == 'FILL':
						a[:,2] += 0.01

					normal = a[1:] - a[:-1]
					lens = numpy.sqrt(normal[:,0]**2 + normal[:,1]**2)
					normal[:,0], normal[:,1] = -normal[:,1] / lens, normal[:,0] / lens
					normal[:,2] /= lens

					ePerDist = path['extrusion'][1:] / lens
					lineWidth = ePerDist * (filamentArea / path['layerThickness'] / 2)

					normal[:,0] *= lineWidth
					normal[:,1] *= lineWidth

					b = numpy.zeros((len(a)-1, 0), numpy.float32)
					b = numpy.concatenate((b, a[1:] + normal), 1)
					b = numpy.concatenate((b, a[1:] - normal), 1)
					b = numpy.concatenate((b, a[:-1] - normal), 1)
					b = numpy.concatenate((b, a[:-1] + normal), 1)
					b = b.reshape((len(b) * 4, 3))

					if len(a) > 2:
						normal2 = normal[:-1] + normal[1:]
						lens2 = numpy.sqrt(normal2[:,0]**2 + normal2[:,1]**2)
						normal2[:,0] /= lens2
						normal2[:,1] /= lens2
						normal2[:,0] *= lineWidth[:-1]
						normal2[:,1] *= lineWidth[:-1]

						c = numpy.zeros((len(a)-2, 0), numpy.float32)
						c = numpy.concatenate((c, a[1:-1]), 1)
						c = numpy.concatenate((c, a[1:-1]+normal[1:]), 1)
						c = numpy.concatenate((c, a[1:-1]+normal2), 1)
						c = numpy.concatenate((c, a[1:-1]+normal[:-1]), 1)

						c = numpy.concatenate((c, a[1:-1]), 1)
						c = numpy.concatenate((c, a[1:-1]-normal[1:]), 1)
						c = numpy.concatenate((c, a[1:-1]-normal2), 1)
						c = numpy.concatenate((c, a[1:-1]-normal[:-1]), 1)

						c = c.reshape((len(c) * 8, 3))
						pointList = numpy.concatenate((pointList, b, c))
					else:
						pointList = numpy.concatenate((pointList, b))
			ret.append(opengl.GLVBO(pointList))
			if extrudeType == 'SUPPORT':
					ret.append(opengl.GLVBO(pointList))
		pointList = numpy.zeros((0,3), numpy.float32)
		for path in layer:
			if path['type'] == 'move':
				a = path['points'] + numpy.array([0,0,0.01], numpy.float32)
				a = numpy.concatenate((a[:-1], a[1:]), 1)
				a = a.reshape((len(a) * 2, 3))
				pointList = numpy.concatenate((pointList, a))
			if path['type'] == 'retract':
				a = path['points'] + numpy.array([0,0,0.01], numpy.float32)
				a = numpy.concatenate((a[:-1], a[1:] + numpy.array([0,0,1], numpy.float32)), 1)
				a = a.reshape((len(a) * 2, 3))
				pointList = numpy.concatenate((pointList, a))
		ret.append(opengl.GLVBO(pointList))

		return ret

	def getObjectCenterPos(self):
		if self._selectedObj is None:
			return [0.0, 0.0, 0.0]
		pos = self._selectedObj.getPosition()
		size = self._selectedObj.getSize()
		return [pos[0], pos[1], size[2]/2]

	def getObjectBoundaryCircle(self):
		if self._selectedObj is None:
			return 0.0
		return self._selectedObj.getBoundaryCircle()

	def getObjectSize(self):
		if self._selectedObj is None:
			return [0.0, 0.0, 0.0]
		return self._selectedObj.getSize()

	def getObjectMatrix(self):
		if self._selectedObj is None:
			return numpy.matrix([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
		return self._selectedObj.getMatrix()

class shaderEditor(wx.Dialog):
	def __init__(self, parent, callback, v, f):
		super(shaderEditor, self).__init__(parent, title="Shader editor", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self._callback = callback
		s = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(s)
		self._vertex = wx.TextCtrl(self, -1, v, style=wx.TE_MULTILINE)
		self._fragment = wx.TextCtrl(self, -1, f, style=wx.TE_MULTILINE)
		s.Add(self._vertex, 1, flag=wx.EXPAND)
		s.Add(self._fragment, 1, flag=wx.EXPAND)

		self._vertex.Bind(wx.EVT_TEXT, self.OnText, self._vertex)
		self._fragment.Bind(wx.EVT_TEXT, self.OnText, self._fragment)

		self.SetPosition(self.GetParent().GetPosition())
		self.SetSize((self.GetSize().GetWidth(), self.GetParent().GetSize().GetHeight()))
		self.Show()

	def OnText(self, e):
		self._callback(self._vertex.GetValue(), self._fragment.GetValue())

class ProjectObject(object):
	def __init__(self, parent, filename):
		super(ProjectObject, self).__init__()
		#print filename
		self.mesh = meshLoader.loadMesh(filename)

		self.parent = parent
		self.filename = filename
		self.scale = 1.0
		self.rotate = 0.0
		self.flipX = False
		self.flipY = False
		self.flipZ = False
		self.swapXZ = False
		self.swapYZ = False
		self.extruder = 0
		self.profile = None
		
		self.modelDisplayList = None
		self.modelDirty = False

		try:
			self.mesh.getMinimumZ()
		except:
			pass

		#print self.mesh.getMinimumZ()
		
		self.centerX = -self.getMinimum()[0] + 5
		self.centerY = -self.getMinimum()[1] + 5
		
		self.updateModelTransform()

		self.centerX = -self.getMinimum()[0] + 5
		self.centerY = -self.getMinimum()[1] + 5

	def isSameExceptForPosition(self, other):
		if self.filename != other.filename:
			return False
		if self.scale != other.scale:
			return False
		if self.rotate != other.rotate:
			return False
		if self.flipX != other.flipX:
			return False
		if self.flipY != other.flipY:
			return False
		if self.flipZ != other.flipZ:
			return False
		if self.swapXZ != other.swapXZ:
			return False
		if self.swapYZ != other.swapYZ:
			return False
		if self.extruder != other.extruder:
			return False
		if self.profile != other.profile:
			return False
		return True

	def updateModelTransform(self):
		self.mesh.setRotateMirror(self.rotate, self.flipX, self.flipY, self.flipZ, self.swapXZ, self.swapYZ)
		minZ = self.mesh.getMinimumZ()
		minV = self.getMinimum()
		maxV = self.getMaximum()
		self.mesh.vertexes -= numpy.array([minV[0] + (maxV[0] - minV[0]) / 2, minV[1] + (maxV[1] - minV[1]) / 2, minZ])
		minZ = self.mesh.getMinimumZ()
		self.modelDirty = True
	
	def getMinimum(self):
		return self.mesh.getMinimum()
	def getMaximum(self):
		return self.mesh.getMaximum()
	def getSize(self):
		return self.mesh.getSize()
	
	def clone(self):
		p = ProjectObject(self.parent, self.filename)

		p.centerX = self.centerX + 5
		p.centerY = self.centerY + 5
		
		p.filename = self.filename
		p.scale = self.scale
		p.rotate = self.rotate
		p.flipX = self.flipX
		p.flipY = self.flipY
		p.flipZ = self.flipZ
		p.swapXZ = self.swapXZ
		p.swapYZ = self.swapYZ
		p.extruder = self.extruder
		p.profile = self.profile
		
		p.updateModelTransform()
		
		return p
	
	def clampXY(self):
		if self.centerX < -self.getMinimum()[0] * self.scale + self.parent.extruderOffset[self.extruder][0]:
			self.centerX = -self.getMinimum()[0] * self.scale + self.parent.extruderOffset[self.extruder][0]
		if self.centerY < -self.getMinimum()[1] * self.scale + self.parent.extruderOffset[self.extruder][1]:
			self.centerY = -self.getMinimum()[1] * self.scale + self.parent.extruderOffset[self.extruder][1]
		if self.centerX > self.parent.machineSize[0] + self.parent.extruderOffset[self.extruder][0] - self.getMaximum()[0] * self.scale:
			self.centerX = self.parent.machineSize[0] + self.parent.extruderOffset[self.extruder][0] - self.getMaximum()[0] * self.scale
		if self.centerY > self.parent.machineSize[1] + self.parent.extruderOffset[self.extruder][1] - self.getMaximum()[1] * self.scale:
			self.centerY = self.parent.machineSize[1] + self.parent.extruderOffset[self.extruder][1] - self.getMaximum()[1] * self.scale
			
