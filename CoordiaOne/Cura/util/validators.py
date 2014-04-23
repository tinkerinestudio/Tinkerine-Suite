from __future__ import absolute_import
from __future__ import division

import types
import math

from Cura.util import profile

SUCCESS = 0
WARNING = 1
ERROR   = 2

class validFloat(object):
	def __init__(self, setting, minValue = None, maxValue = None):
		self.setting = setting
		self.setting.validators.append(self)
		self.minValue = minValue
		self.maxValue = maxValue
	
	def validate(self):
		try:
			f = float(eval(self.setting.GetValue().replace(',','.'), {}, {}))
			if self.minValue != None and f < self.minValue:
				return ERROR, 'This setting should not be below ' + str(self.minValue)
			if self.maxValue != None and f > self.maxValue:
				return ERROR, 'This setting should not be above ' + str(self.maxValue)
			return SUCCESS, ''
		except (ValueError, SyntaxError, TypeError):
			return ERROR, '"' + str(self.setting.GetValue()) + '" is not a valid number or expression'

class validInt(object):
	def __init__(self, setting, minValue = None, maxValue = None):
		self.setting = setting
		self.setting.validators.append(self)
		self.minValue = minValue
		self.maxValue = maxValue
	
	def validate(self):
		try:
			f = int(eval(self.setting.GetValue(), {}, {}))
			if self.minValue != None and f < self.minValue:
				return ERROR, 'This setting should not be below ' + str(self.minValue)
			if self.maxValue != None and f > self.maxValue:
				return ERROR, 'This setting should not be above ' + str(self.maxValue)
			return SUCCESS, ''
		except (ValueError, SyntaxError, TypeError):
			return ERROR, '"' + str(self.setting.GetValue()) + '" is not a valid whole number or expression'

class warningAbove(object):
	def __init__(self, setting, minValueForWarning, warningMessage):
		self.setting = setting
		self.setting.validators.append(self)
		self.minValueForWarning = minValueForWarning
		self.warningMessage = warningMessage
	
	def validate(self):
		try:
			f = float(eval(self.setting.GetValue().replace(',','.'), {}, {}))
			if isinstance(self.minValueForWarning, types.FunctionType):
				if f >= self.minValueForWarning():
					return WARNING, self.warningMessage % (self.minValueForWarning())
			else:
				if f >= self.minValueForWarning:
					return WARNING, self.warningMessage
			return SUCCESS, ''
		except (ValueError, SyntaxError, TypeError):
			#We already have an error by the int/float validator in this case.
			return SUCCESS, ''

class wallThicknessValidator(object):
	def __init__(self, setting):
		self.setting = setting
		self.setting.validators.append(self)
	
	def validate(self):
		try:
			wallThickness = profile.getProfileSettingFloat('wall_thickness')
			nozzleSize = profile.getProfileSettingFloat('nozzle_size')
			if wallThickness <= nozzleSize * 0.5:
				return ERROR, 'Trying to print walls thinner then the half of your nozzle size, this will not produce anything usable'
			if wallThickness <= nozzleSize * 0.85:
				return WARNING, 'Trying to print walls thinner then the 0.8 * nozzle size. Small chance that this will produce usable results'
			if wallThickness < nozzleSize:
				return SUCCESS, ''
			
			lineCount = int(wallThickness / nozzleSize)
			lineWidth = wallThickness / lineCount
			lineWidthAlt = wallThickness / (lineCount + 1)
			if lineWidth >= nozzleSize * 1.5 and lineWidthAlt <= nozzleSize * 0.85:
				return WARNING, 'Current selected wall thickness results in a line thickness of ' + str(lineWidthAlt) + 'mm which is not recommended with your nozzle of ' + str(nozzleSize) + 'mm'
			return SUCCESS, ''
		except ValueError:
			#We already have an error by the int/float validator in this case.
			return SUCCESS, ''

class printSpeedValidator(object):
	def __init__(self, setting):
		self.setting = setting
		self.setting.validators.append(self)

	def validate(self):
		try:
			nozzleSize = profile.getProfileSettingFloat('nozzle_size')
			layerHeight = profile.getProfileSettingFloat('layer_height')
			printSpeed = profile.getProfileSettingFloat('print_speed')
			
			printVolumePerMM = layerHeight * nozzleSize
			printVolumePerSecond = printVolumePerMM * printSpeed
			#Using 10mm3 per second with a 0.4mm nozzle (normal max according to Joergen Geerds)
			maxPrintVolumePerSecond = 10 / (math.pi*(0.2*0.2)) * (math.pi*(nozzleSize/2*nozzleSize/2))
			
			if printVolumePerSecond > maxPrintVolumePerSecond:
				return WARNING, 'You are trying to print more then %.1fmm^3 of filament per second. This might cause filament slipping. (You are printing at %0.1fmm^3 per second)' % (maxPrintVolumePerSecond, printVolumePerSecond)
			
			return SUCCESS, ''
		except ValueError:
			#We already have an error by the int/float validator in this case.
			return SUCCESS, ''

