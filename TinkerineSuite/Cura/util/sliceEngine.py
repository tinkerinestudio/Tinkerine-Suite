__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"
import subprocess
import time
import math
import numpy
import os
import warnings
import threading
import traceback
import platform
import sys
import urllib
import urllib2
import hashlib
import wx
import inspect
import shutil
from Cura.util import meshLoader
from Cura.util import profile
from Cura.util import profile2
from Cura.util import version
from Cura.util import sliceRun
from Cura.util import gcodeInterpreter
from Cura.util import exporer
from Cura.util import mesh
from Cura.util import mesh2
from Cura.util import stl2
def getEngineFilename():
	if platform.system() == 'Windows':
		if os.path.exists('C:/Software/Cura_SteamEngine/_bin/Release/Cura_SteamEngine.exe'):
			return 'C:/Software/Cura_SteamEngine/_bin/Release/Cura_SteamEngine.exe'
		return os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'CuraEngine.exe'))
	if hasattr(sys, 'frozen'):
		return os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..', 'CuraEngine'))
	return os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'CuraEngine'))

def getTempFilename():
	warnings.simplefilter('ignore')
	ret = os.tempnam(None, "Cura_Tmp")
	warnings.simplefilter('default')
	return ret
class Action(object):
	pass

class Slicer(object):
	def __init__(self, progressCallback):
		self._process = None
		self._thread = None
		self._callback = progressCallback
		self._binaryStorageFilename = getTempFilename()
		self._exportFilename = getTempFilename()
		self._progressSteps = ['inset', 'skin', 'export']
		self._objCount = 0
		self._sliceLog = []
		#self._printTimeSeconds = None
		self._totalMoveTimeMinute = None
		self._basicSettings = []
		self._extrusionAmount = None
		self._filamentMM = None
		self._modelHash = None
		self.extruderOffset = [
			numpy.array([0,0,0]),
			numpy.array([profile.getPreferenceFloat('extruder_offset_x1'), profile.getPreferenceFloat('extruder_offset_y1'), 0]),
			numpy.array([profile.getPreferenceFloat('extruder_offset_x2'), profile.getPreferenceFloat('extruder_offset_y2'), 0]),
			numpy.array([profile.getPreferenceFloat('extruder_offset_x3'), profile.getPreferenceFloat('extruder_offset_y3'), 0])]
			
		self._pspw = None
	def cleanup(self):
		self.abortSlicer()
		try:
			os.remove(self._binaryStorageFilename)
		except:
			pass
		try:
			os.remove(self._exportFilename)
		except:
			pass

	def abortSlicer(self):
		if self._process is not None:
			try:
				self._process.terminate()
			except:
				pass
			self._thread.join()
		self._thread = None

	def wait(self):
		if self._thread is not None:
			self._thread.join()

	def getGCodeFilename(self):
		return self._exportFilename

	def getSliceLog(self):
		return self._sliceLog

	def getFilamentWeight(self):
		#Calculates the weight of the filament in kg
		radius = float(profile.getProfileSetting('filament_diameter')) / 2
		volumeM3 = (self._filamentMM * (math.pi * radius * radius)) / (1000*1000*1000)
		return volumeM3 * profile.getPreferenceFloat('filament_physical_density')

	def getFilamentCost(self):
		cost_kg = profile.getPreferenceFloat('filament_cost_kg')
		cost_meter = profile.getPreferenceFloat('filament_cost_meter')
		if cost_kg > 0.0 and cost_meter > 0.0:
			return "%.2f / %.2f" % (self.getFilamentWeight() * cost_kg, self._filamentMM / 1000.0 * cost_meter)
		elif cost_kg > 0.0:
			return "%.2f" % (self.getFilamentWeight() * cost_kg)
		elif cost_meter > 0.0:
			return "%.2f" % (self._filamentMM / 1000.0 * cost_meter)
		return None

	def getPrintTime(self):
		if int(self._printTimeSeconds / 60 / 60) < 1:
			return '%d minutes' % (int(self._printTimeSeconds / 60) % 60)
		if int(self._printTimeSeconds / 60 / 60) == 1:
			return '%d hour %d minutes' % (int(self._printTimeSeconds / 60 / 60), int(self._printTimeSeconds / 60) % 60)
		return '%d hours %d minutes' % (int(self._printTimeSeconds / 60 / 60), int(self._printTimeSeconds / 60) % 60)

	def getFilamentAmount(self):
		#return '%0.2f meter %0.0f gram' % (float(self._filamentMM) / 1000.0, self.getFilamentWeight() * 1000.0)
		return "out spot"
	#def runSlicer(self, scene):
	#	extruderCount = 1
	#	print "runSlicer"
	def runSlicer(self, list, name, sceneView):
		#dlg=wx.FileDialog(self, "Save project gcode file", os.path.split(profile2.getPreference('lastFile'))[0], style=wx.FD_SAVE)
		#dlg.SetWildcard("GCode file (*.gcode)|*.gcode")
		#if dlg.ShowModal() != wx.ID_OK:
		#	dlg.Destroy()
		#	return
		#print sceneView
		resultFilename = name
		#dlg.Destroy()

		put = profile.setTempOverride
		oldProfile = profile.getGlobalProfileString()
		
		put('add_start_end_gcode', 'False')
		put('gcode_extension', 'project_tmp')
		#if self.printMode == 0:
		if 0:
			clearZ = 0
			actionList = []
			for item in list:
				if item.profile != None and os.path.isfile(item.profile):
					profile.loadGlobalProfile(item.profile)
				put('object_center_x', item.centerX - self.extruderOffset[item.extruder][0])
				put('object_center_y', item.centerY - self.extruderOffset[item.extruder][1])
				put('model_scale', item.scale)
				put('flip_x', item.flipX)
				put('flip_y', item.flipY)
				put('flip_z', item.flipZ)
				put('model_rotate_base', item.rotate)
				put('swap_xz', item.swapXZ)
				put('swap_yz', item.swapYZ)
				
				action = Action()
				action.sliceCmd = sliceRun.getSliceCommand(item.filename)
				action.centerX = item.centerX
				action.centerY = item.centerY
				action.temperature = profile.getProfileSettingFloat('print_temperature')
				action.extruder = item.extruder
				action.filename = item.filename
				clearZ = max(clearZ, item.getSize()[2] * item.scale + 5.0)
				action.clearZ = clearZ
				action.leaveResultForNextSlice = False
				action.usePreviousSlice = False
				actionList.append(action)

				if list.index(item) > 0 and item.isSameExceptForPosition(list[list.index(item)-1]):
					actionList[-2].leaveResultForNextSlice = True
					actionList[-1].usePreviousSlice = True

				if item.profile != None:
					profile.loadGlobalProfileFromString(oldProfile)
			
		else:
			#self._saveCombinedSTL(resultFilename + "_temp_.stl", list)
			meshLoader.saveMeshes(resultFilename + "_temp_.stl", list)

			put('model_scale', 1.0)
			put('flip_x', False)
			put('flip_y', False)
			put('flip_z', False)
			put('model_rotate_base', 0)
			put('swap_xz', False)
			put('swap_yz', False)
			put('object_center_x', sceneView._scene.getMinMaxPosition()[0] + (profile.getPreferenceFloat('machine_width') / 2))
			put('object_center_y', sceneView._scene.getMinMaxPosition()[1] + (profile.getPreferenceFloat('machine_depth') / 2))  
			actionList = []
			#print sceneView._scene.getMinMaxPosition()
			action = Action()
			action.sliceCmd = sliceRun.getSliceCommand(resultFilename + "_temp_.stl")
			action.centerX = profile.getPreferenceFloat('machine_width') / 2 #these dont do squat! but they have to be here. 
			action.centerY = profile.getPreferenceFloat('machine_depth') / 2
			#action.centerX = 0
			#action.centerY = 300
			action.temperature = profile.getProfileSettingFloat('print_temperature')
			action.extruder = 0
			action.filename = resultFilename + "_temp_.stl"
			action.clearZ = 0
			action.leaveResultForNextSlice = False
			action.usePreviousSlice = False

			actionList.append(action)
		
		#Restore the old profile.
		profile.resetTempOverride()
		
		self._pspw = ProjectSliceProgressWindow(self, actionList, resultFilename, sceneView)
		self._pspw.extruderOffset = self.extruderOffset
		self._pspw.Centre()

		if version.isDevVersion():
			self._pspw.Show(True) #DEBUG
	"""
	def runSlicer(self, scene):
		extruderCount = 1
		for obj in scene.objects():
			if scene.checkPlatform(obj):
				extruderCount = max(extruderCount, len(obj._meshList))

		commandList = [getEngineFilename(), '-vv']
		for k, v in self._engineSettings(extruderCount).iteritems():
			commandList += ['-s', '%s=%s' % (k, str(v))]
		commandList += ['-o', self._exportFilename]
		commandList += ['-b', self._binaryStorageFilename]
		self._objCount = 0
		with open(self._binaryStorageFilename, "wb") as f:
			hash = hashlib.sha512()
			order = scene.printOrder()
			if order is None:
				pos = numpy.array(profile.getMachineCenterCoords()) * 1000
				commandList += ['-s', 'posx=%d' % int(pos[0]), '-s', 'posy=%d' % int(pos[1])]

				vertexTotal = 0
				for obj in scene.objects():
					if scene.checkPlatform(obj):
						for mesh in obj._meshList:
							vertexTotal += mesh.vertexCount

				f.write(numpy.array([vertexTotal], numpy.int32).tostring())
				for obj in scene.objects():
					if scene.checkPlatform(obj):
						for mesh in obj._meshList:
							vertexes = (numpy.matrix(mesh.vertexes, copy = False) * numpy.matrix(obj._matrix, numpy.float32)).getA()
							vertexes -= obj._drawOffset
							vertexes += numpy.array([obj.getPosition()[0], obj.getPosition()[1], 0.0])
							f.write(vertexes.tostring())
							hash.update(mesh.vertexes.tostring())

				commandList += ['#']
				self._objCount = 1
			else:
				for n in order:
					obj = scene.objects()[n]
					for mesh in obj._meshList:
						f.write(numpy.array([mesh.vertexCount], numpy.int32).tostring())
						s = mesh.vertexes.tostring()
						f.write(s)
						hash.update(s)
					pos = obj.getPosition() * 1000
					pos += numpy.array(profile.getMachineCenterCoords()) * 1000
					commandList += ['-m', ','.join(map(str, obj._matrix.getA().flatten()))]
					commandList += ['-s', 'posx=%d' % int(pos[0]), '-s', 'posy=%d' % int(pos[1])]
					commandList += ['#' * len(obj._meshList)]
					self._objCount += 1
			self._modelHash = hash.hexdigest()
		if self._objCount > 0:
			self._thread = threading.Thread(target=self._watchProcess, args=(commandList, self._thread))
			self._thread.daemon = True
			self._thread.start()

	def _watchProcess(self, commandList, oldThread):
		if oldThread is not None:
			if self._process is not None:
				self._process.terminate()
			oldThread.join()
		self._callback(-1.0, False)
		try:
			self._process = self._runSliceProcess(commandList)
		except OSError:
			traceback.print_exc()
			return
		if self._thread != threading.currentThread():
			self._process.terminate()
		self._callback(0.0, False)
		self._sliceLog = []
		self._printTimeSeconds = None
		self._filamentMM = None

		line = self._process.stdout.readline()
		objectNr = 0
		while len(line):
			line = line.strip()
			if line.startswith('Progress:'):
				line = line.split(':')
				if line[1] == 'process':
					objectNr += 1
				elif line[1] in self._progressSteps:
					progressValue = float(line[2]) / float(line[3])
					progressValue /= len(self._progressSteps)
					progressValue += 1.0 / len(self._progressSteps) * self._progressSteps.index(line[1])

					progressValue /= self._objCount
					progressValue += 1.0 / self._objCount * objectNr
					try:
						self._callback(progressValue, False)
					except:
						pass
			elif line.startswith('Print time:'):
				self._printTimeSeconds = int(line.split(':')[1].strip())
			elif line.startswith('Filament:'):
				self._filamentMM = int(line.split(':')[1].strip())
			else:
				self._sliceLog.append(line.strip())
			line = self._process.stdout.readline()
		for line in self._process.stderr:
			self._sliceLog.append(line.strip())
		returnCode = self._process.wait()
		try:
			if returnCode == 0:
				pluginError = profile.runPostProcessingPlugins(self._exportFilename)
				if pluginError is not None:
					print pluginError
					self._sliceLog.append(pluginError)
				self._callback(1.0, True)
			else:
				for line in self._sliceLog:
					print line
				self._callback(-1.0, False)
		except:
			pass
		self._process = None
	"""
	def _engineSettings(self, extruderCount): #not used!
		settings = {
			'layerThickness': int(profile.getProfileSettingFloat('layer_height') * 1000),
			'initialLayerThickness': int(profile.getProfileSettingFloat('bottom_thickness') * 1000) if profile.getProfileSettingFloat('bottom_thickness') > 0.0 else int(profile.getProfileSettingFloat('layer_height') * 1000),
			'filamentDiameter': int(profile.getProfileSettingFloat('filament_diameter') * 1000),
			'filamentFlow': int(profile.getProfileSettingFloat('filament_flow')),
			'extrusionWidth': int(profile.calculateEdgeWidth() * 1000),
			'insetCount': int(profile.calculateLineCount()),
			'downSkinCount': int(profile.calculateSolidLayerCount()) if profile.getProfileSetting('solid_bottom') == 'True' else 0,
			'upSkinCount': int(profile.calculateSolidLayerCount()) if profile.getProfileSetting('solid_top') == 'True' else 0,
			'sparseInfillLineDistance': int(100 * profile.calculateEdgeWidth() * 1000 / profile.getProfileSettingFloat('fill_density')) if profile.getProfileSettingFloat('fill_density') > 0 else -1,
			'infillOverlap': int(profile.getProfileSettingFloat('fill_overlap')),
			'initialSpeedupLayers': int(4),
			'initialLayerSpeed': int(profile.getProfileSettingFloat('bottom_layer_speed')),
			'printSpeed': int(profile.getProfileSettingFloat('print_speed')),
			'infillSpeed': int(profile.getProfileSettingFloat('infill_speed')) if int(profile.getProfileSettingFloat('infill_speed')) > 0 else int(profile.getProfileSettingFloat('print_speed')),
			'moveSpeed': int(profile.getProfileSettingFloat('travel_speed')),
			'fanOnLayerNr': int(profile.getProfileSettingFloat('fan_layer')),
			'fanSpeedMin': int(profile.getProfileSettingFloat('fan_speed')) if profile.getProfileSetting('fan_enabled') == 'True' else 0,
			'fanSpeedMax': int(profile.getProfileSettingFloat('fan_speed_max')) if profile.getProfileSetting('fan_enabled') == 'True' else 0,
			'supportAngle': int(-1) if profile.getProfileSetting('support') == 'None' else int(60),
			'supportEverywhere': int(1) if profile.getProfileSetting('support') == 'Everywhere' else int(0),
			'supportLineWidth': int(profile.getProfileSettingFloat('support_rate') * profile.calculateEdgeWidth() * 1000 / 100),
			'retractionAmount': int(profile.getProfileSettingFloat('retraction_amount') * 1000) if profile.getProfileSetting('retraction_enable') == 'True' else 0,
			'retractionSpeed': int(profile.getProfileSettingFloat('retraction_speed')),
			'retractionAmountExtruderSwitch': int(profile.getProfileSettingFloat('retraction_dual_amount') * 1000),
			'multiVolumeOverlap': int(profile.getProfileSettingFloat('overlap_dual') * 1000),
			'objectSink': int(profile.getProfileSettingFloat('object_sink') * 1000),
			'minimalLayerTime': int(profile.getProfileSettingFloat('cool_min_layer_time')),
			'minimalFeedrate': int(profile.getProfileSettingFloat('cool_min_feedrate')),
			'coolHeadLift': 1 if profile.getProfileSetting('cool_head_lift') == 'True' else 0,
			'startCode': profile.getAlterationFileContents('start.gcode', extruderCount),
			'endCode': profile.getAlterationFileContents('end.gcode', extruderCount),

			'extruderOffset[1].X': int(profile.getPreferenceFloat('extruder_offset_x1') * 1000),
			'extruderOffset[1].Y': int(profile.getPreferenceFloat('extruder_offset_y1') * 1000),
			'extruderOffset[2].X': int(profile.getPreferenceFloat('extruder_offset_x2') * 1000),
			'extruderOffset[2].Y': int(profile.getPreferenceFloat('extruder_offset_y2') * 1000),
			'extruderOffset[3].X': int(profile.getPreferenceFloat('extruder_offset_x3') * 1000),
			'extruderOffset[3].Y': int(profile.getPreferenceFloat('extruder_offset_y3') * 1000),
			'fixHorrible': 0,
		}
		if profile.getProfileSetting('platform_adhesion') == 'Brim':
			settings['skirtDistance'] = 0
			settings['skirtLineCount'] = int(profile.getProfileSettingFloat('brim_line_count'))
		elif profile.getProfileSetting('platform_adhesion') == 'Raft':
			settings['skirtDistance'] = 0
			settings['skirtLineCount'] = 0
			settings['raftMargin'] = int(profile.getProfileSettingFloat('raft_margin') * 1000)
			settings['raftBaseThickness'] = int(profile.getProfileSettingFloat('raft_base_thickness') * 1000)
			settings['raftBaseLinewidth'] = int(profile.getProfileSettingFloat('raft_base_linewidth') * 1000)
			settings['raftInterfaceThickness'] = int(profile.getProfileSettingFloat('raft_interface_thickness') * 1000)
			settings['raftInterfaceLinewidth'] = int(profile.getProfileSettingFloat('raft_interface_linewidth') * 1000)
		else:
			settings['skirtDistance'] = int(profile.getProfileSettingFloat('skirt_gap') * 1000)
			settings['skirtLineCount'] = int(profile.getProfileSettingFloat('skirt_line_count'))

		if profile.getProfileSetting('fix_horrible_union_all_type_a') == 'True':
			settings['fixHorrible'] |= 0x01
		if profile.getProfileSetting('fix_horrible_union_all_type_b') == 'True':
			settings['fixHorrible'] |= 0x02
		if profile.getProfileSetting('fix_horrible_use_open_bits') == 'True':
			settings['fixHorrible'] |= 0x10
		if profile.getProfileSetting('fix_horrible_extensive_stitching') == 'True':
			settings['fixHorrible'] |= 0x04

		if settings['layerThickness'] <= 0:
			settings['layerThickness'] = 1000
		return settings

	def _runSliceProcess(self, cmdList):
		kwargs = {}
		if subprocess.mswindows:
			su = subprocess.STARTUPINFO()
			su.dwFlags |= subprocess.STARTF_USESHOWWINDOW
			su.wShowWindow = subprocess.SW_HIDE
			kwargs['startupinfo'] = su
			kwargs['creationflags'] = 0x00004000 #BELOW_NORMAL_PRIORITY_CLASS
		return subprocess.Popen(cmdList, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)

	def submitSliceInfoOnline(self):
		if profile.getPreference('submit_slice_information') != 'True':
			return
		if version.isDevVersion():
			return
		data = {
			'processor': platform.processor(),
			'machine': platform.machine(),
			'platform': platform.platform(),
			'profile': profile.getGlobalProfileString(),
			'preferences': profile.getGlobalPreferencesString(),
			'modelhash': self._modelHash,
			'version': version.getVersion(),
		}
		try:
			f = urllib2.urlopen("http://www.youmagine.com/curastats/", data = urllib.urlencode(data), timeout = 1)
			f.read()
			f.close()
		except:
			pass
	def _saveCombinedSTL(self, filename, list):
		totalCount = 0
		for item in list:
			totalCount += item.mesh.vertexCount
		output = mesh2.mesh()
		output._prepareVertexCount(totalCount)
		for item in list:
			offset = numpy.array([item.centerX, item.centerY, 0])
			for v in item.mesh.vertexes:
				v0 = v * item.scale + offset
				output.addVertex(v0[0], v0[1], v0[2])
		stl2.saveAsSTL(output, filename)
class ProjectSliceProgressWindow(wx.Frame):
	def __init__(self, parent, actionList, resultFilename, sceneView):
		super(ProjectSliceProgressWindow, self).__init__(None, title='Building')
		self.parent = parent
		self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
		self.sceneView = sceneView
		self.actionList = actionList
		self.resultFilename = resultFilename
		self.abort = False
		self.prevStep = 'start'
		self.totalDoneFactor = 0.0
		self.startTime = time.time()
		self.sliceStartTime = time.time()
		self._thread = None
		
		self.sizer = wx.GridBagSizer(2, 2) 
		self.statusText = wx.StaticText(self, -1, "Building: %s" % (resultFilename))
		self.progressGauge = wx.Gauge(self, -1)
		self.progressGauge.SetRange(10000)
		self.progressGauge2 = wx.Gauge(self, -1)
		self.progressGauge2.SetRange(len(self.actionList))
		self.abortButton = wx.Button(self, -1, "Abort")
		self.sizer.Add(self.statusText, (0,0), span=(1,5))
		self.sizer.Add(self.progressGauge, (1, 0), span=(1,5), flag=wx.EXPAND)
		self.sizer.Add(self.progressGauge2, (2, 0), span=(1,5), flag=wx.EXPAND)

		self.sizer.Add(self.abortButton, (3,0), span=(1,5), flag=wx.ALIGN_CENTER)
		self.sizer.AddGrowableCol(0)
		self.sizer.AddGrowableRow(0)

		self.Bind(wx.EVT_BUTTON, self.OnAbort, self.abortButton)
		self.SetSizer(self.sizer)
		self.Layout()
		self.Fit()
		
		threading.Thread(target=self.OnRun).start()

	def OnAbort(self, e):
		if self.abort:
			self.Close()
		else:
			self.abort = True
			#self.abortButton.SetLabel('Close')
			
			try:
				os.remove(self.resultFilename + "_temp_.stl")
			except:
				pass
			
	def SetProgress(self, stepName, layer, maxLayer):
		if self.prevStep != stepName:
			self.totalDoneFactor += sliceRun.sliceStepTimeFactor[self.prevStep]
			newTime = time.time()
			#print "#####" + str(newTime-self.startTime) + " " + self.prevStep + " -> " + stepName
			self.startTime = newTime
			self.prevStep = stepName
		
		progresValue = ((self.totalDoneFactor + sliceRun.sliceStepTimeFactor[stepName] * layer / maxLayer) / sliceRun.totalRunTimeFactor) * 10000
		self.progressGauge.SetValue(int(progresValue))
		#print (progresValue/10000)
		self.statusText.SetLabel(stepName + " [" + str(layer) + "/" + str(maxLayer) + "]")
		self.sceneView.setProgressBar(progresValue/10000)
		self.sceneView.Refresh()
		#taskbar.setProgress(self, 10000 * self.progressGauge2.GetValue() + int(progresValue), 10000 * len(self.actionList))
	
	def OnRun(self):
		resultFile = open(self.resultFilename, "w")
		put = profile.setTempOverride
		self.progressLog = []
		for action in self.actionList:
			wx.CallAfter(self.SetTitle, "Building: [%d/%d]"  % (self.actionList.index(action) + 1, len(self.actionList)))
			if not action.usePreviousSlice:
				p = sliceRun.startSliceCommandProcess(action.sliceCmd)
				line = p.stdout.readline()
		
				maxValue = 1
				while(len(line) > 0):
					if len(line) > 0:
						print line
					line = line.rstrip()

					if line[0:9] == "Progress[" and line[-1:] == "]":
						progress = line[9:-1].split(":")
						if len(progress) > 2:
							maxValue = int(progress[2])
						wx.CallAfter(self.SetProgress, progress[0], int(progress[1]), maxValue)
					else:
						try:
							self.progressLog.append(line)
							wx.CallAfter(self.statusText.SetLabel, line)
						except:
							pass
					if self.abort:
						self.sceneView._isSlicing = False
						p.terminate()
						wx.CallAfter(self.statusText.SetLabel, "Aborted by user.")
						resultFile.close()
						self.Close()
						return
					line = p.stdout.readline()
				self.returnCode = p.wait()


				if self.returnCode != 0:
					self.sceneView._isSlicing = False
					try:
						os.remove(self.resultFilename + "_temp_.stl")
					except:
						pass
					dial = wx.MessageDialog(None, 'An Error occurred during slicing. Try checking the model for errors, lowering the resolution or print settings and try slicing again.', 'Error encountered during Slicing', wx.OK|wx.ICON_EXCLAMATION)
					dial.ShowModal()
					resultFile.close()
					self.sceneView.setCursorToDefault()
					self.Close()
					return
			
			put('object_center_x', action.centerX - self.extruderOffset[action.extruder][0])
			put('object_center_y', action.centerY - self.extruderOffset[action.extruder][1])
			put('clear_z', action.clearZ)
			put('extruder', action.extruder)
			put('print_temperature', action.temperature)
			
			if action == self.actionList[0]:
				resultFile.write(';TYPE:CUSTOM\n')
				resultFile.write('T%d\n' % (action.extruder))
				currentExtruder = action.extruder
				prevTemp = action.temperature
				startGCode = profile.getAlterationFileContents('start.gcode')
				startGCode = startGCode.replace('?filename?', 'Multiple files')
				resultFile.write(startGCode)
			else:
				#reset the extrusion length, and move to the next object center.
				resultFile.write(';TYPE:CUSTOM\n')
				if prevTemp != action.temperature and action.temperature > 0:
					resultFile.write('M104 S%d\n' % (int(action.temperature)))
					prevTemp = action.temperature
				resultFile.write(profile.getAlterationFileContents('nextobject.gcode'))
			resultFile.write(';PRINTNR:%d\n' % self.actionList.index(action))
			profile.resetTempOverride()
			
			if not action.usePreviousSlice:
				f = open(sliceRun.getExportFilename(action.filename, "project_tmp"), "r")
				data = f.read(4096)
				while data != '':
					resultFile.write(data)
					data = f.read(4096)
				f.close()
				savedCenterX = action.centerX
				savedCenterY = action.centerY
			else:
				f = open(sliceRun.getExportFilename(action.filename, "project_tmp"), "r")
				for line in f:
					if line[0] != ';':
						if 'X' in line:
							line = self._adjustNumberInLine(line, 'X', action.centerX - savedCenterX)
						if 'Y' in line:
							line = self._adjustNumberInLine(line, 'Y', action.centerY - savedCenterY)
					resultFile.write(line)
				f.close()

			if not action.leaveResultForNextSlice:
				os.remove(sliceRun.getExportFilename(action.filename, "project_tmp"))
			
			wx.CallAfter(self.progressGauge.SetValue, 10000)
			self.totalDoneFactor = 0.0
			wx.CallAfter(self.progressGauge2.SetValue, self.actionList.index(action) + 1)
		
		resultFile.write(';TYPE:CUSTOM\n')
		if len(self.actionList) > 1 and self.actionList[-1].clearZ > 1:
			#only move to higher Z if we have sliced more then 1 object. This solves the "move into print after printing" problem with the print-all-at-once option.
			resultFile.write('G1 Z%f F%f\n' % (self.actionList[-1].clearZ, profile.getProfileSettingFloat('max_z_speed') * 60))
		resultFile.write(profile.getAlterationFileContents('end.gcode'))
		resultFile.close()
		
		gcode = gcodeInterpreter.gcode()
		gcode.load(self.resultFilename)
		
		self.abort = True
		sliceTime = time.time() - self.sliceStartTime
		status = "Build: %s" % (self.resultFilename)
		status += "\nSlicing took: %02d:%02d" % (sliceTime / 60, sliceTime % 60)
		status += "\nFilament: %.2fm %.2fg" % (gcode.extrusionAmount / 1000, gcode.calculateWeight() * 1000)
		status += "\nPrint time: %02d:%02d" % (int(gcode.totalMoveTimeMinute / 60), int(gcode.totalMoveTimeMinute % 60))
		cost = gcode.calculateCost()
		if cost != False:
			status += "\nCost: %s" % (cost)
		profile.replaceGCodeTags(self.resultFilename, gcode)

		self.parent._totalMoveTimeMinute = gcode.totalMoveTimeMinute
		self.parent._extrusionAmount = gcode.extrusionAmount
		self.parent._basicSettings = gcode.basicSettings

		wx.CallAfter(self.statusText.SetLabel, status)
		#self._thread = threading.Thread(target=self.OnSliceDone(self.resultFilename))# start_new(wx.CallAfter(self.OnSliceDone(self.resultFilename)))
		#wx.CallAfter(self._thread.start())
		wx.CallAfter(self.OnSliceDone)
		#wx.CallAfter(self.OnSliceDone(self.resultFilename))
		#wx.CallAfter(self.sceneView.testgcodeload(self.resultFilename))
		
        #print(self.parent)
		#print(self.parent)
		#print("wat")
		#############self.viewSelection.setValue(4)
			#self._thread = threading.Thread(target=self._watchProcess, args=(commandList, self._thread))
			#self._thread.daemon = True
			#self._thread.start()
	def _adjustNumberInLine(self, line, tag, f):
		m = re.search('^(.*'+tag+')([0-9\.]*)(.*)$', line)
		return m.group(1) + str(float(m.group(2)) + f) + m.group(3) + '\n'
	
	def OnSliceDone(self):
		self.abortButton.Destroy()
		self.closeButton = wx.Button(self, -1, "Close")
		self.printButton = wx.Button(self, -1, "Print")
		self.logButton = wx.Button(self, -1, "Show log")
		self.sizer.Add(self.closeButton, (3,0), span=(1,1))
		#self.sizer.Add(self.printButton, (3,1), span=(1,1))
		self.sizer.Add(self.logButton, (3,2), span=(1,1))
		if exporer.hasExporer():
			self.openFileLocationButton = wx.Button(self, -1, "Open file location")
			self.Bind(wx.EVT_BUTTON, self.OnOpenFileLocation, self.openFileLocationButton)
			self.sizer.Add(self.openFileLocationButton, (3,3), span=(1,1))
		if profile.getPreference('sdpath') != '':
			#SDCopyPromt(self.resultFilename)
			self.copyToSDButton = wx.Button(self, -1, "To SDCard")
			self.Bind(wx.EVT_BUTTON, self.OnCopyToSD, self.copyToSDButton)
			self.sizer.Add(self.copyToSDButton, (3,4), span=(1,1))
		self.Bind(wx.EVT_BUTTON, self.OnAbort, self.closeButton)
		#self.Bind(wx.EVT_BUTTON, self.OnPrint, self.printButton)
		self.Bind(wx.EVT_BUTTON, self.OnShowLog, self.logButton)
		self.Layout()
		self.Fit()
		
		self.sceneView.OnSliceDone(self.resultFilename)
		
		#self.sceneView.testgcodeload(self.resultFilename)
		#self.sceneView.setProgressBar(None)
		#self.sceneView.saveMenuOpen = True
		#self.sceneView.sdSaveButton._hidden = False
		#self.sceneView.directorySaveButton._hidden = False
		#self.sceneView.Refresh()
		try:
			os.remove(self.resultFilename + "_temp_.stl")
		except:
			pass
			
		if not version.isDevVersion():
			self.Close() #DEBUG
		
	def OnCopyToSD(self, e):
		filename = os.path.basename(self.resultFilename)
		if profile.getPreference('sdshortnames') == 'True':
			filename = sliceRun.getShortFilename(filename)
		shutil.copy(self.resultFilename, os.path.join(profile.getPreference('sdpath'), filename))

	def OnOpenFileLocation(self, e):
		exporer.openExporer(self.resultFilename)
	
	def OnPrint(self, e):
		printWindow.printFile(self.resultFilename)

	def OnShowLog(self, e):
		LogWindow('\n'.join(self.progressLog))
class LogWindow(wx.Frame):
	def __init__(self, logText):
		super(LogWindow, self).__init__(None, title="Slice log")
		self.textBox = wx.TextCtrl(self, -1, logText, style=wx.TE_MULTILINE|wx.TE_DONTWRAP|wx.TE_READONLY)
		self.SetSize((400,300))
		self.Centre()
		self.Show(True)
		
class SDCopyPromt(wx.Frame):
    title = "Copy to SD"
    def __init__(self, resultFilename):
		self.resultFilename = resultFilename
		wx.Frame.__init__(self, wx.GetApp().TopWindow, title=self.title, size = (315,130),style=wx.DEFAULT_DIALOG_STYLE)
		self.panel = wx.Panel(self)

		#self.panel.SetBackgroundColour(wx.Colour(73,73,75))
		vbox = wx.BoxSizer(wx.VERTICAL)
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		text = "Would you like to copy the sliced file to SD card: [" + profile.getPreference('sdpath') + "]?"
		qq22=wx.StaticText(self.panel,-1, text)
		font2 = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
		qq22.SetFont(font2)
		qq22.SetForegroundColour((0,0,0)) # set text color
        
		btn1 = wx.Button(self.panel, label='Ok', size=(70, 30))
		btn1.SetForegroundColour(wx.Colour(73,73,75))
		btn1.Bind(wx.EVT_BUTTON,self.doit)
        
		btn2 = wx.Button(self.panel, label='Cancel', size=(70, 30))
		btn2.SetForegroundColour(wx.Colour(73,73,75))
		btn2.Bind(wx.EVT_BUTTON,self.close)
        
		hbox.Add(btn2, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.RIGHT, border = 10)
		hbox.Add(btn1, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.LEFT, border = 10)
        
		vbox.Add(qq22, 1, wx.ALIGN_CENTER_HORIZONTAL| wx.TOP, 10)
		vbox.Add(hbox, 1, wx.ALIGN_CENTER_HORIZONTAL| wx.TOP, 10)
		self.panel.SetSizer(vbox)
		self.Show()
        
    def doit(self,event):
		filename = os.path.basename(self.resultFilename)
		if profile.getPreference('sdshortnames') == 'True':
			filename = sliceRun.getShortFilename(filename)
		shutil.copy(self.resultFilename, os.path.join(profile.getPreference('sdpath'), filename))
		self.Close(True)
		
    def close(self,ev):
        self.Close(True)