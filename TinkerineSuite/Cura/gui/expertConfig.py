from __future__ import absolute_import

import wx

from Cura.gui import configBase
from Cura.util import validators

class expertConfigWindow(wx.Frame):
	"Expert configuration window"
	def __init__(self, parent):
		super(expertConfigWindow, self).__init__(None, title='Expert config', style=wx.DEFAULT_DIALOG_STYLE)
		wx.EVT_CLOSE(self, self.OnClose)
		self.panel = configBase.configPanelBase(self)
		self.parent = parent
		left, right, main = self.panel.CreateConfigPanel(self)
		
		self.configList = []
		
		configBase.TitleRow(left, "Speed")
		c = configBase.SettingRow(left, "Minimum layer time (#) ", 'cool_min_layer_time', '6', 'If a layer would finish too quickly, the print will slow down so it takes this amount of time to finish the layer.')
		self.configList.append(c)
		validators.validFloat(c, 0.0)
		c = configBase.SettingRow(left, "Travel Speed (mm/s) ", 'travel_speed', '200', 'How fast the extruder moves while not printing.')
		self.configList.append(c)
		validators.validFloat(c, 50, 500)
		
		c = configBase.SettingRow(left, "Bridge Feed (%)", 'bridge_feed_ratio', '90', 'Speed at which layers with bridges travel, compared to normal printing speed.')
		self.configList.append(c)
		validators.validFloat(c, 0.0)
		c = configBase.SettingRow(left, "Bridge Flow (%)", 'bridge_flow_ratio', '90', 'Speed at which layers with bridges are printed, compared to normal printing speed.')
		self.configList.append(c)
		validators.validFloat(c, 0.0)
		
		c = configBase.SettingRow(left, "Perimeter Speed (%)", 'perimeter_speed_ratio', '75', 'Speed at which the perimeter will be printed, compared to the infill.')
		self.configList.append(c)
		validators.validFloat(c, 0.0)
		
		configBase.TitleRow(left, "Cool")
		c = configBase.SettingRow(left, "Minimum feedrate (mm/s)", 'cool_min_feedrate', '5', 'The minimal layer time can cause the print to slow down so much it starts to ooze. The minimal feedrate protects against this. Even if a print gets slown down it will never be slower then this minimal feedrate.')
		self.configList.append(c)
		validators.validFloat(c, 0.0)
		c = configBase.SettingRow(left, "Fan on layer number (#)", 'fan_layer', '3', 'The layer at which the fan is turned on. The first layer is layer 0. The first layer can stick better if you turn on the fan on, on the 2nd layer.')
		self.configList.append(c)
		validators.validInt(c, 0)
		c = configBase.SettingRow(left, "Fan speed min (%)", 'fan_speed', '100', 'When the fan is turned on, it is enabled at this speed setting. If cool slows down the layer, the fan is adjusted between the min and max speed. Minimal fan speed is used if the layer is not slowed down due to cooling.')
		self.configList.append(c)
		validators.validInt(c, 0, 100)
		c = configBase.SettingRow(left, "Fan speed max (%)", 'fan_speed_max', '100', 'When the fan is turned on, it is enabled at this speed setting. If cool slows down the layer, the fan is adjusted between the min and max speed. Maximal fan speed is used if the layer is slowed down due to cooling by more then 200%.')
		self.configList.append(c)
		validators.validInt(c, 0, 100)

		configBase.TitleRow(left, "Skirt")
		c = configBase.SettingRow(left, "Skirt line count (#)", 'skirt_line_count', '3', 'The number of loops the print will draw outside the object on the first layer. This is to ensure the filament is flowing well before starting the print.')
		self.configList.append(c)
		validators.validFloat(c, 0)
		c = configBase.SettingRow(left, "Skirt gap width (mm)", 'skirt_gap', '3.0', 'How far the skirt will be placed from the actual object.')
		self.configList.append(c)
		validators.validInt(c, 0.0)
		
		configBase.TitleRow(left, "Size")
		c = configBase.SettingRow(left, "Custom Machine Depth (mm)", 'custom_machine_depth', '200', 'Custom Machine Depth')
		self.configList.append(c)
		validators.validFloat(c, 0)
		c = configBase.SettingRow(left, "Custom Machine Width (mm)", 'custom_machine_width', '200', 'Custom Machine Width')
		self.configList.append(c)
		validators.validFloat(c, 0)
		c = configBase.SettingRow(left, "Custom Machine Height (mm)", 'custom_machine_height', '200', 'Custom Machine Height')
		self.configList.append(c)
		validators.validFloat(c, 0)

		configBase.TitleRow(left, "Material")
		c = configBase.SettingRow(left, "Filament Density (ratio)", 'filament_density', '1', 'Density of the material. 1.0 for PLA. 0.9 for x')
		self.configList.append(c)
		validators.validFloat(c, 0)
		c = configBase.SettingRow(left, "Infill Width (mm)", 'infill_width', '0.4', 'The width of the infill.')
		self.configList.append(c)
		validators.validFloat(c, 0)
		c = configBase.SettingRow(left, "Perimeter flow ", 'perimeter_flow_ratio', '75', 'The flow rate of the perimeter')
		self.configList.append(c)
		validators.validFloat(c, 0)

		#c = configBase.SettingRow(left, "Enable Brim", 'fan_speed', '100', 'When the fan is turned on, it is enabled at this speed setting. If cool slows down the layer, the fan is adjusted between the min and max speed. Minimal fan speed is used if the layer is not slowed down due to cooling.')
		#validators.validInt(c, 0, 100)
		
		#configBase.TitleRow(left, "Raft (if enabled)")
		#c = configBase.SettingRow(left, "Extra margin (mm)", 'raft_margin', '3.0', 'If the raft is enabled, this is the extra raft area around the object which is also rafted. Increasing this margin will create a stronger raft.')
		#validators.validFloat(c, 0.0)
		#c = configBase.SettingRow(left, "Base material amount (%)", 'raft_base_material_amount', '100', 'The base layer is the first layer put down as a raft. This layer has thick strong lines and is put firmly on the bed to prevent warping. This setting adjust the amount of material used for the base layer.')
		#validators.validFloat(c, 0.0)
		#c = configBase.SettingRow(left, "Interface material amount (%)", 'raft_interface_material_amount', '100', 'The interface layer is a weak thin layer between the base layer and the printed object. It is designed to has little material to make it easy to break the base off the printed object. This setting adjusts the amount of material used for the interface layer.')
		#validators.validFloat(c, 0.0)

		#configBase.TitleRow(left, "Support")
		#c = configBase.SettingRow(left, "Material amount (%)", 'support_rate', '100', 'Amount of material used for support, less material gives a weaker support structure which is easier to remove.')
		#validators.validFloat(c, 0.0)
		#c = configBase.SettingRow(left, "Distance from object (mm)", 'support_distance', '0.5', 'Distance between the support structure and the object. Empty gap in which no support structure is printed.')
		#validators.validFloat(c, 0.0)

		
		configBase.TitleRow(right, "Infill")
		c = configBase.SettingRow(right, "Infill pattern", 'infill_type', ['Line', 'Grid Circular', 'Grid Hexagonal', 'Grid Rectangular'], 'Pattern of the none-solid infill. Line is default, but grids can provide a strong print.')
		self.configList.append(c)
		c = configBase.SettingRow(right, "Bottom surface layers (#) ", 'bottom_surface_thickness_layers', '2', 'Number of solid layers from the bottom of the print.')
		self.configList.append(c)
		validators.validFloat(c, 0)
		c = configBase.SettingRow(right, "Top surface layers (#) ", 'top_surface_thickness_layers', '3', 'Number of solid layers from the top of the print.')
		self.configList.append(c)
		validators.validFloat(c, 0)
		c = configBase.SettingRow(right, "Infill overlap (%)", 'fill_overlap', '12', 'Amount of overlap between the infill and the walls. There is a slight overlap with the walls and the infill so the walls connect firmly to the infill.')
		self.configList.append(c)
		validators.validFloat(c, 0.0)
		
		c = configBase.SettingRow(right, "Infill in direction of bridge", 'bridge_direction', True, 'If this is on, infill will fill in the direction of bridging. This improves bridging but may increase print time.')
		self.configList.append(c)

	
		configBase.TitleRow(right, "Retraction")
		c = configBase.SettingRow(right, "Retraction speed (mm/s) ", 'retraction_speed', '60.0', 'How quickly the extruder does a retract command.')
		self.configList.append(c)
		validators.validFloat(c, 0)
		c = configBase.SettingRow(right, "Retraction amount (mm) ", 'retraction_amount', '0.7', 'How much distance the extruder will retract.')
		self.configList.append(c)
		validators.validFloat(c, 0)
		c = configBase.SettingRow(right, "Retraction extra amount (mm) ", 'retraction_extra', '0.0', 'How much extra the extruder will retract with each retract command.')
		self.configList.append(c)
		validators.validFloat(c, 0)
		
		configBase.TitleRow(right, "First Layer")
		c = configBase.SettingRow(right, "First layer temperature (#) ", 'first_layer_print_temperature', '220', 'How hot the extruder will print at during the first layer.')
		self.configList.append(c)
		validators.validFloat(c, 0)
		#c = configBase.SettingRow(right, "First layer height (mm) ", 'bottom_thickness', '0.2', 'Create a solid top surface, if set to false the top is filled with the fill percentage. Useful for cups/vases.')
		#validators.validFloat(c, 0)
		c = configBase.SettingRow(right, "First layer speed (mm/s) ", 'bottom_layer_speed', '25', 'How fast the print will print at during the first layer.')
		self.configList.append(c)
		validators.validFloat(c, 0)
	
		configBase.TitleRow(right, "Clip")
		c = configBase.SettingRow(right, "Organic Clip", 'organic_clip', False, 'Attempts to hide the start and end points of each layer. Works well with organic shapes.')
		self.configList.append(c)
		#c = configBase.SettingRow(right, "Clip (mm)", 'clip', '0.0', 'How close the beginning and the end of a perimeter meet. A higher number increase the distance.')
		#self.configList.append(c)
		#validators.validFloat(c, 0.0)

		configBase.TitleRow(right, "Support")
		c = configBase.SettingRow(right, "Support Type", 'support', ['None', 'Exterior Only', 'Everywhere'], 'Where the supports will be generated.')
		self.configList.append(c)
		#validators.validFloat(c, 0)
		c = configBase.SettingRow(right, "Support Density", 'support_density', '0.3', 'How dense the support will be.')
		self.configList.append(c)
		validators.validFloat(c, 0)
		c = configBase.SettingRow(right, "Support Angle", 'support_angle', '65', 'The minimum angle required for support to be generated')
		self.configList.append(c)
		validators.validFloat(c, 0)
		
		#configBase.TitleRow(right, "Sequence")
		#c = configBase.SettingRow(right, "Print order sequence", 'sequence', ['Loops > Perimeter > Infill', 'Loops > Infill > Perimeter', 'Infill > Loops > Perimeter', 'Infill > Perimeter > Loops', 'Perimeter > Infill > Loops', 'Perimeter > Loops > Infill'], 'Sequence of printing. The perimeter is the outer print edge, the loops are the insides of the walls, and the infill is the insides.');
		#c = configBase.SettingRow(right, "Force first layer sequence", 'force_first_layer_sequence', True, 'This setting forces the order of the first layer to be \'Perimeter > Loops > Infill\'')

		#configBase.TitleRow(right, "Joris")
		#c = configBase.SettingRow(right, "Joris the outer edge", 'joris', False, '[Joris] is a code name for smoothing out the Z move of the outer edge. This will create a steady Z increase over the whole print. It is intended to be used with a single walled wall thickness to make cups/vases.')

		#configBase.TitleRow(right, "Retraction")
		#c = configBase.SettingRow(right, "Retract on jumps only", 'retract_on_jumps_only', True, 'Only retract when we are making a move that is over a hole in the model, else retract on every move. This effects print quality in different ways.')

		#configBase.TitleRow(right, "Hop")
		#c = configBase.SettingRow(right, "Enable hop on move", 'hop_on_move', False, 'When moving from print position to print position, raise the printer head 0.2mm so it does not knock off the print (experimental).')
		
		#def __init__(self, panel, name):
		"Add a title row to the configuration panel"
		sizer = right.GetSizer()
		x = sizer.GetRows()
		#self.title = wx.StaticText(right, -1, "ahh")
		#self.title.SetFont(wx.Font(wx.SystemSettings.GetFont(wx.SYS_ANSI_VAR_FONT).GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.FONTWEIGHT_BOLD))
		#sizer.Add(self.title, (x,0), (1,3), flag=wx.EXPAND|wx.TOP|wx.LEFT, border=10)
		self.ln = wx.StaticLine(right, -1)

		self.okButton = wx.Button(right, -1, 'Save')
		self.okButton2 = wx.Button(right, -1, 'Close')
		self.okButton3 = wx.Button(right, -1, 'Reset Settings')
		
		mySizer = wx.GridBagSizer(3, 2)
		mySizer.Add(self.okButton, (2,0), (1,1), flag=wx.EXPAND|wx.TOP|wx.RIGHT,border=5)
		mySizer.Add(self.okButton2, (2,1), (1,1), flag=wx.EXPAND|wx.TOP|wx.RIGHT,border=5)
		mySizer.Add(self.okButton3, (2,2), (1,1), flag=wx.EXPAND|wx.TOP|wx.RIGHT,border=5)
		sizer.Add(mySizer, (x,0), (1,3), flag=wx.EXPAND|wx.LEFT,border=10)
		
		sizer.SetRows(x )
		
		#self.ln = wx.StaticLine(panel, -1)

		#sizer.SetRows(x + 2)
		
		self.Bind(wx.EVT_BUTTON, lambda e: self.saveAll(), self.okButton) #TODO: have a "settings saved!" message/promt
		self.Bind(wx.EVT_BUTTON, lambda e: self.Close(), self.okButton2) #TODO: make a window promt asking to save changes if there are any
		self.Bind(wx.EVT_BUTTON, lambda e: self.resetSettings(), self.okButton3) #TODO: make a window promt asking to save changes if there are any

		#buttonPanel.SetSizer(sizer)

		#sizer.Add(leftConfigPanel, border=35, flag=wx.RIGHT)
		
		#self.okButton = wx.Button(self, -1, 'Ok')
		#sizer.Add(self.okButton, (0, 0))
		#sizer.Add(right, (1, 0))

		#self.okButton2 = wx.Button(left, -1, 'Ok')
		#left.GetSizer().Add(self.okButton2, (left.GetSizer().GetRows(), 1))
		#self.okButton3 = wx.Button(left, -1, 'Ok')
		#left.GetSizer().Add(self.okButton3, (left.GetSizer().GetRows(), 2))
		
		#self.Bind(wx.EVT_BUTTON, lambda e: self.Close(), self.okButton)
		
		main.Fit()
		self.Fit()

	def OnClose(self, e):
		self.Destroy()
		
	def saveAll(self):
		for item in self.configList:
			item.saveSetting()
		#self.Destroy()
		#self.parent.scene.updateProfileToControls()
		self.parent.updateProfileToControls()
	def resetSettings(self):
		for item in self.configList:
			#print item.defaultValue
			try:
				item.SetValue(item.defaultValue)
				item.saveSetting()
			except:
				pass
				#print item
		