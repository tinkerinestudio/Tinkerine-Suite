"""
Settings is a collection of utilities to display, read & write the settings and position widgets.

"""

from __future__ import absolute_import
from __future__ import division

import sys
import types
import math

from Cura.util import profile
from Cura.cura_sf.fabmetheus_utilities import archive

def DEFSET(setting):
	return setting.value

def storedSetting(name):
	return lambda setting: profile.getProfileSetting(name)
def storedSettingFloat(name):
	return lambda setting: profile.getProfileSettingFloat(name)
def storedSettingInt(name):
	return lambda setting: int(profile.getProfileSettingFloat(name))
def storedPreference(name):
	return lambda setting: profile.getPreference(name)
def storedPreferenceFloat(name):
	return lambda setting: profile.getPreferenceFloat(name)
def storedSettingInvertBoolean(name):
	return lambda setting: profile.getProfileSetting(name) == "False"

def ifSettingAboveZero(name):
	return lambda setting: profile.getProfileSettingFloat(name) > 0

def ifSettingIs(name, value):
	return lambda setting: profile.getProfileSetting(name) == value

def raftLayerCount(setting):
	if profile.getProfileSetting('enable_raft') == "True":
		return '1'
	return '0'

def storedPercentSetting(name):
	return lambda setting: profile.getProfileSettingFloat(name) / 100

def calculateEdgeWidth(setting):
	return profile.calculateEdgeWidth()

def calculateShells(setting):
	return profile.calculateLineCount() - 1

def calculateShellsBase(setting):
	edgeWidth = profile.calculateEdgeWidth()
	extraWall = profile.getProfileSettingFloat('extra_base_wall_thickness')
	
	return profile.calculateLineCount() - 1 + int(extraWall / edgeWidth + 0.0001)

def calculateSolidLayerCount(setting):
	return profile.calculateSolidLayerCount()

def firstLayerSpeedRatio(setting):
	bottomSpeed = profile.getProfileSettingFloat('bottom_layer_speed')
	speed = profile.getProfileSettingFloat('print_speed')
	return bottomSpeed/speed

def calculateBridgeFeedRatio(setting):
	print storedSettingFloat("bridge_feed_ratio")
	return storedSettingFloat("bridge_feed_ratio")/100
			#'Bridge_Feed_Rate_Multiplier_ratio': storedSettingFloat("bridge_feed_ratio"),
			#'Bridge_Flow_Rate_Multiplier_ratio': storedSettingFloat("bridge_flow_ratio"),
	
def calcSupportDistanceRatio(setting):
	edgeWidth = calculateEdgeWidth(setting)
	distance = profile.getProfileSettingFloat('support_distance')
	return distance / edgeWidth

def calculateMultiplyDistance(setting):
	edgeWidth = calculateEdgeWidth(setting)
	return 10.0 / edgeWidth

def calcBottomLayerFlowRateRatio(setting):
	bottomThickness = profile.getProfileSettingFloat('bottom_thickness')
	layerThickness = profile.getProfileSettingFloat('layer_height')
	if bottomThickness < layerThickness:
		return 1.0
	return bottomThickness / layerThickness

def calcExtraBottomThickness(setting):
	bottomThickness = profile.getProfileSettingFloat('bottom_thickness')
	layerThickness = profile.getProfileSettingFloat('layer_height')
	if bottomThickness < layerThickness:
		return 0.0
	return bottomThickness - layerThickness

def calcLayerSkip(setting):
	bottomThickness = profile.getProfileSettingFloat('bottom_thickness')
	layerThickness = profile.getProfileSettingFloat('layer_height')
	if bottomThickness < layerThickness:
		return 0
	return int(math.ceil((bottomThickness - layerThickness) / layerThickness + 0.0001) - 1)

def getProfileInformation():
#NOTE TO MYSELF#
#Skeinforge uses these variables, but has them converted first
#In skeinforge, in carve.py, there is- 'Edge Width (mm):' which corresponds to the- 'Edge_Width_mm' below.
#So it takes the 'Edge Width (mm):' and removed all spaces and brackets and puts a '_' between each word. 

	return {
		'carve': {
			'Add_Layer_Template_to_SVG': "true",
			'Edge_Width_mm': storedSettingFloat("edge_width_mm"),
			#'Edge_Width_mm': 2.2*0.2, 
			#'Edge_Width_mm': "0.36", #100 micron
			'Extra_Decimal_Places_float': "2.0",
			'Import_Coarseness_ratio': "1.0",
			'Layer_Height_mm': storedSettingFloat("layer_height"),
			'Layers_From_index': "0",
			'Layers_To_index': "912345678",
			'Correct_Mesh': "True",
			'Unproven_Mesh': "False",
			'SVG_Viewer': "webbrowser",
			'FlipX': storedSetting("flip_x"),
			'FlipY': storedSetting("flip_y"),
			'FlipZ': storedSetting("flip_z"),
			'SwapXZ': storedSetting("swap_xz"),
			'SwapYZ': storedSetting("swap_yz"),
			'Scale': storedSettingFloat("model_scale"),
			'Rotate': storedSettingFloat("model_rotate_base"),
			'CenterX': lambda setting: profile.getProfileSettingFloat('object_center_x') if profile.getProfileSettingFloat('object_center_x') > 0 else profile.getPreferenceFloat("machine_width") / 2,
			'CenterY': lambda setting: profile.getProfileSettingFloat('object_center_y') if profile.getProfileSettingFloat('object_center_y') > 0 else profile.getPreferenceFloat("machine_depth") / 2,
			'AlternativeCenterFile': storedSetting("alternative_center"),
		},'scale': {
			'Activate_Scale': "False",
			'XY_Plane_Scale_ratio': "1.01",
			'Z_Axis_Scale_ratio': "1",
			'SVG_Viewer': "webbrowser",
		},'bottom': {
			'Activate_Bottom': "True",
			'Additional_Height_over_Layer_Thickness_ratio': "0.5",
			'Altitude_mm': "0.0",
			'SVG_Viewer': "webbrowser",
		},'preface': {
			'Meta': DEFSET,
			'Set_Positioning_to_Absolute': "True",
			'Set_Units_to_Millimeters': "True",
			'Start_at_Home': "False",
			'Turn_Extruder_Off_at_Shut_Down': "True",
			'Turn_Extruder_Off_at_Start_Up': "True",
		},'widen': {
			'Activate_Widen': "False",
			'Widen_Width_over_Edge_Width_ratio': "2",
		},'inset': {
			'Add_Custom_Code_for_Temperature_Reading': "False",
			'Infill_in_Direction_of_Bridge': profile.getProfileSetting('bridge_direction'),
			#'Infill_Width': "0.3", #100 micron
			'Infill_Width': storedSettingFloat("infill_width"), 
			'Loop_Order_Choice': DEFSET,
			'Overlap_Removal_Width_over_Perimeter_Width_ratio': "0.6",
			'Turn_Extruder_Heater_Off_at_Shut_Down': "True",
			'Volume_Fraction_ratio': "0.82",
		},'fill': {
			'Activate_Fill': "True",
			'Solid_Surface_Top': "False",
			'Override_First_Layer_Sequence': storedSetting("force_first_layer_sequence"),
			'Diaphragm_Period_layers': "160000",
			'Diaphragm_Thickness_layers': "0",
			'Extra_Shells_on_Alternating_Solid_Layer_layers': calculateShells,
			'Extra_Shells_on_Base_layers': calculateShellsBase,
			'Extra_Shells_on_Sparse_Layer_layers': calculateShells,
			'Grid_Circle_Separation_over_Perimeter_Width_ratio': "0.2",
			'Grid_Extra_Overlap_ratio': "0.1",
			'Grid_Junction_Separation_Band_Height_layers': "10",
			'Grid_Junction_Separation_over_Octogon_Radius_At_End_ratio': "0.0",
			'Grid_Junction_Separation_over_Octogon_Radius_At_Middle_ratio': "0.0",
			'Infill_Begin_Rotation_degrees': "0",
			'Infill_Begin_Rotation_Repeat_layers': "1",
			'Infill_Odd_Layer_Extra_Rotation_degrees': "90.0",
			'Grid_Circular': ifSettingIs('infill_type', 'Grid Circular'),
			'Grid_Hexagonal': ifSettingIs('infill_type', 'Grid Hexagonal'),
			'Grid_Rectangular': ifSettingIs('infill_type', 'Grid Rectangular'),
			'Line': ifSettingIs('infill_type', 'Line'),
			'Infill_Perimeter_Overlap_ratio': storedPercentSetting('fill_overlap'),
			'Infill_Solidity_ratio': storedPercentSetting('fill_density'),
			'Infill_Width': "0.4",
			'Sharpest_Angle_degrees': "60",
			'Solid_Surface_Thickness_layers': calculateSolidLayerCount,
			'Bottom_Surface_Thickness_layers': profile.getProfileSetting('bottom_surface_thickness_layers'),
			'Top_Surface_Thickness_layers': profile.getProfileSetting('top_surface_thickness_layers'),
			'Start_From_Choice': DEFSET,
			'Surrounding_Angle_degrees': "60",
			'Thread_Sequence_Choice': storedSetting('sequence'),
		},'multiply': {
			'Activate_Multiply': "False",
			'Center_X_mm': lambda setting: profile.getProfileSettingFloat('object_center_x') if profile.getProfileSettingFloat('object_center_x') > 0 else profile.getPreferenceFloat("machine_width") / 2,
			'Center_Y_mm': lambda setting: profile.getProfileSettingFloat('object_center_y') if profile.getProfileSettingFloat('object_center_y') > 0 else profile.getPreferenceFloat("machine_depth") / 2,
			'Number_of_Columns_integer': storedSetting('model_multiply_x'),
			'Number_of_Rows_integer': storedSetting('model_multiply_y'),
			'Reverse_Sequence_every_Odd_Layer': False,
			'Separation_over_Perimeter_Width_ratio': calculateMultiplyDistance,
		},'speed': {
			'Activate_Speed': "True",
			'Add_Flow_Rate': "True",
			#'Bridge_Feed_Rate_Multiplier_ratio': "0.7", #100 micron
			#'Bridge_Flow_Rate_Multiplier_ratio': "2.0", #100 micron
			#'Bridge_Feed_Rate_Multiplier_ratio': storedPercentSetting('bridge_speed'),
			#'Bridge_Flow_Rate_Multiplier_ratio': storedPercentSetting('bridge_speed'),
			'Bridge_Feed_Rate_Multiplier_ratio': storedPercentSetting("bridge_feed_ratio"),
			'Bridge_Flow_Rate_Multiplier_ratio': storedPercentSetting("bridge_flow_ratio"),
			'Duty_Cyle_at_Beginning_portion': "1.0",
			'Duty_Cyle_at_Ending_portion': "0.0",
			'Feed_Rate_mm/s': storedSettingFloat("print_speed"),
			'Flow_Rate_Setting_float': storedSettingFloat("print_speed"),
			#'Flow_Rate_Setting_float': 200,
			'Object_First_Layer_Feed_Rate_Infill_Multiplier_ratio': firstLayerSpeedRatio,
			'Object_First_Layer_Feed_Rate_Perimeter_Multiplier_ratio': firstLayerSpeedRatio,
			'Object_First_Layer_Feed_Rate_Travel_Multiplier_ratio': firstLayerSpeedRatio,
			'Object_First_Layer_Flow_Rate_Infill_Multiplier_ratio': firstLayerSpeedRatio,
			'Object_First_Layer_Flow_Rate_Perimeter_Multiplier_ratio': firstLayerSpeedRatio,
			'Object_First_Layers_Amount_Of_Layers_For_Speed_Change': DEFSET,
			'Orbital_Feed_Rate_over_Operating_Feed_Rate_ratio': "0.5",
			'Maximum_Z_Feed_Rate_mm/s': "60.0",
			'Perimeter_Feed_Rate_Multiplier_ratio': storedPercentSetting("perimeter_speed_ratio"),
			'Perimeter_Flow_Rate_Multiplier_ratio': storedPercentSetting("perimeter_speed_ratio"),
			'Travel_Feed_Rate_mm/s': storedSettingFloat("travel_speed"),
			'Bottom_layer_flow_rate_ratio': calcBottomLayerFlowRateRatio,
			'Top_layer_flow_rate_ratio': storedSettingFloat("top_surface_flow"),
		},'temperature': {
			'Activate_Temperature': "True",#ifSettingAboveZero('print_temperature'),
			'Cooling_Rate_Celcius/second': "3.0",
			'Heating_Rate_Celcius/second': "10.0",
			'Base_Temperature_Celcius': storedSettingFloat("print_temperature"),
			'Interface_Temperature_Celcius': storedSettingFloat("print_temperature"),
			'Object_First_Layer_Infill_Temperature_Celcius': storedSettingFloat("first_layer_print_temperature"),
			'Object_First_Layer_Perimeter_Temperature_Celcius': storedSettingFloat("first_layer_print_temperature"),
			'Object_Next_Layers_Temperature_Celcius': storedSettingFloat("print_temperature"),
			'Support_Layers_Temperature_Celcius': storedSettingFloat("print_temperature"),
			'Supported_Layers_Temperature_Celcius': storedSettingFloat("print_temperature"),
		},'raft': {
			'Activate_Raft': "True",
			'Add_Raft,_Elevate_Nozzle,_Orbit': DEFSET,
			'Base_Feed_Rate_Multiplier_ratio': "1.0",
			'Base_Flow_Rate_Multiplier_ratio': "1.0",
			'Base_Infill_Density_ratio': "0.5",
			'Base_Layer_Thickness_over_Layer_Thickness': "2.0",
			'Base_Layers_integer': raftLayerCount,
			'Base_Nozzle_Lift_over_Base_Layer_Thickness_ratio': "0.4",
			'Initial_Circling': "False",
			'Infill_Overhang_over_Extrusion_Width_ratio': "0.0",
			'Interface_Feed_Rate_Multiplier_ratio': "1.0",
			'Interface_Flow_Rate_Multiplier_ratio': "1.0",
			'Interface_Infill_Density_ratio': storedSettingFloat("support_density"),
			'Interface_Layer_Thickness_over_Layer_Thickness': "1.0",
			'Interface_Layers_integer': raftLayerCount,
			'Interface_Nozzle_Lift_over_Interface_Layer_Thickness_ratio': "0.45",
			'Name_of_Support_End_File': DEFSET,
			'Name_of_Support_Start_File': DEFSET,
			'Operating_Nozzle_Lift_over_Layer_Thickness_ratio': "0.5",
			'Raft_Additional_Margin_over_Length_%': "1.0",
			'Raft_Margin_mm': "3.0",
			'Support_Cross_Hatch': lambda setting: 'True' if profile.getProfileSetting('support_dual_extrusion') == 'True' and int(profile.getPreference('extruder_amount')) > 1 else 'False',
			'Support_Flow_Rate_over_Operating_Flow_Rate_ratio': "1.0",
			'Support_Gap_over_Perimeter_Extrusion_Width_ratio': "1.2",
			'Support_Material_Choice_': storedSetting('support'),
			'Support_Minimum_Angle_degrees': storedSettingFloat("support_angle"),
			'Support_Margin_mm': '3.0',
			'Support_Offset_X_mm': lambda setting: -profile.getPreferenceFloat('extruder_offset_x1') if profile.getProfileSetting('support_dual_extrusion') == 'True' and int(profile.getPreference('extruder_amount')) > 1 else '0',
			'Support_Offset_Y_mm': lambda setting: -profile.getPreferenceFloat('extruder_offset_y1') if profile.getProfileSetting('support_dual_extrusion') == 'True' and int(profile.getPreference('extruder_amount')) > 1 else '0',
		},'skirt': {
			'Skirt_line_count': storedSetting("skirt_line_count"),
			'Convex': lambda setting: "True" if profile.getProfileSettingFloat('skirt_gap') > 0.0 else "False",
			'Gap_Width_mm': storedSetting("skirt_gap"),
			'Layers_To_index': "1",
		},'joris': {
			'Activate_Joris': storedSetting("joris"),
			'Layers_From_index': calculateSolidLayerCount,
		},'chamber': {
			'Activate_Chamber': "False",
			'Bed_Temperature_Celcius': DEFSET,
			'Bed_Temperature_Begin_Change_Height_mm': DEFSET,
			'Bed_Temperature_End_Change_Height_mm': DEFSET,
			'Bed_Temperature_End_Celcius': DEFSET,
			'Chamber_Temperature_Celcius': DEFSET,
			'Holding_Force_bar': DEFSET,
		},'tower': {
			'Activate_Tower': "False",
			'Extruder_Possible_Collision_Cone_Angle_degrees': "60",
			'Maximum_Tower_Height_layers': "5",
			'Tower_Start_Layer_integer': "1",
		},'jitter': {
			'Activate_Jitter': profile.getProfileSetting('organic_clip'),
			'Jitter_Over_Perimeter_Width_ratio': DEFSET,
		},'clip': {
			'Activate_Clip': "False",
			'Clip_Over_Perimeter_Width_ratio': storedSettingFloat("clip"),
			'Maximum_Connection_Distance_Over_Perimeter_Width_ratio': "10.0",
		},'smooth': {
			'Activate_Smooth': "True",
			'Layers_From_index': "1",
			'Maximum_Shortening_over_Width_float': "1.2",
		},'stretch': {
			'Activate_Stretch': "False",
			'Cross_Limit_Distance_Over_Perimeter_Width_ratio': DEFSET,
			'Loop_Stretch_Over_Perimeter_Width_ratio': DEFSET,
			'Path_Stretch_Over_Perimeter_Width_ratio': DEFSET,
			'Perimeter_Inside_Stretch_Over_Perimeter_Width_ratio': DEFSET,
			'Perimeter_Outside_Stretch_Over_Perimeter_Width_ratio': DEFSET,
			'Stretch_From_Distance_Over_Perimeter_Width_ratio': DEFSET,
		},'skin': {
			'Activate_Skin': storedSetting("enable_skin"),
			'Horizontal_Infill_Divisions_integer': "1",
			'Horizontal_Perimeter_Divisions_integer': "1",
			'Vertical_Divisions_integer': "2",
			'Hop_When_Extruding_Infill': "False",
			'Layers_From_index': "1",
		},'comb': {
			'Activate_Comb': "False",
			'Running_Jump_Space_mm': "2.0",
		},'cool': {
			'Activate_Cool': "True",
			'Bridge_Cool_Celcius': "1.0",
			'Cool_Type': DEFSET,
			'Maximum_Cool_Celcius': "2.0",
			'Minimum_Layer_Time_seconds': storedSettingFloat("cool_min_layer_time"),
			'Minimum_Orbital_Radius_millimeters': DEFSET,
			'Name_of_Cool_End_File': DEFSET,
			'Name_of_Cool_Start_File': DEFSET,
			'Orbital_Outset_millimeters': DEFSET,
			'Turn_Fan_On_at_Beginning': storedSetting("fan_enabled"),
			'Turn_Fan_Off_at_Ending': storedSetting("fan_enabled"),
			'Minimum_feed_rate_mm/s': storedSettingFloat("cool_min_feedrate"),
			'Fan_on_at_layer': storedSettingInt('fan_layer'),
			'Fan_speed_min_%': storedSettingInt('fan_speed'),
			'Fan_speed_max_%': storedSettingInt('fan_speed_max'),
		},'hop': {
			'Activate_Hop': storedSetting('hop_on_move'),
			'Hop_Over_Layer_Thickness_ratio': lambda setting: 0.2 / profile.getProfileSettingFloat('layer_height'),
			'Minimum_Hop_Angle_degrees': DEFSET,
		},'wipe': {
			'Activate_Wipe': "False",
			'Arrival_X_mm': DEFSET,
			'Arrival_Y_mm': DEFSET,
			'Arrival_Z_mm': DEFSET,
			'Departure_X_mm': DEFSET,
			'Departure_Y_mm': DEFSET,
			'Departure_Z_mm': DEFSET,
			'Wipe_X_mm': DEFSET,
			'Wipe_Y_mm': DEFSET,
			'Wipe_Z_mm': DEFSET,
			'Wipe_Period_layers': DEFSET,
		},'oozebane': {
			'Activate_Oozebane': "False",
			'After_Startup_Distance_millimeters': DEFSET,
			'Early_Shutdown_Distance_millimeters': DEFSET,
			'Early_Startup_Distance_Constant_millimeters': DEFSET,
			'Early_Startup_Maximum_Distance_millimeters': DEFSET,
			'First_Early_Startup_Distance_millimeters': DEFSET,
			'Minimum_Distance_for_Early_Startup_millimeters': DEFSET,
			'Minimum_Distance_for_Early_Shutdown_millimeters': DEFSET,
			'Slowdown_Startup_Steps_positive_integer': DEFSET,
		},'dwindle': {
			'Activate_Dwindle': "False",
			'End_Rate_Multiplier_ratio': '0.5',
			'Pent_Up_Volume_cubic_millimeters': "0.4",
			'Slowdown_Steps_positive_integer': '5',
			'Slowdown_Volume_cubic_millimeters': "5.0",
		},'splodge': {
			'Activate_Splodge': "False",
			'Initial_Lift_over_Extra_Thickness_ratio': DEFSET,
			'Initial_Splodge_Feed_Rate_mm/s': DEFSET,
			'Operating_Splodge_Feed_Rate_mm/s': DEFSET,
			'Operating_Splodge_Quantity_Length_millimeters': DEFSET,
			'Initial_Splodge_Quantity_Length_millimeters': DEFSET,
			'Operating_Lift_over_Extra_Thickness_ratio': DEFSET,
		},'home': {
			'Activate_Home': "False",
			'Name_of_Home_File': DEFSET,
		},'lash': {
			'Activate_Lash': "False",
			'X_Backlash_mm': DEFSET,
			'Y_Backlash_mm': DEFSET,
		},'fillet': {
			'Activate_Fillet': "False",
			'Arc_Point': DEFSET,
			'Arc_Radius': DEFSET,
			'Arc_Segment': DEFSET,
			'Bevel': DEFSET,
			'Corner_Feed_Rate_Multiplier_ratio': DEFSET,
			'Fillet_Radius_over_Perimeter_Width_ratio': DEFSET,
			'Reversal_Slowdown_Distance_over_Perimeter_Width_ratio': DEFSET,
			'Use_Intermediate_Feed_Rate_in_Corners': DEFSET,
		},'limit': {
			'Activate_Limit': "True",
			'Maximum_Initial_Feed_Rate_mm/s': "100.0",
		},'unpause': {
			'Activate_Unpause': "False",
			'Delay_milliseconds': DEFSET,
			'Maximum_Speed_ratio': DEFSET,
		},'dimension': {
			'Activate_Dimension': "True",
			'Absolute_Extrusion_Distance': "True",
			'Relative_Extrusion_Distance': "False",
			'Extruder_Retraction_Speed_mm/s': storedSettingFloat('retraction_speed'),
			'Filament_Diameter_mm': storedSettingFloat("filament_diameter"),
			'Filament_Packing_Density_ratio': "1",
			'Maximum_E_Value_before_Reset_float': "91234.0",
			'Minimum_Travel_for_Retraction_millimeters': "0.5",
			'Retract_Within_Island': storedSettingInvertBoolean("retract_on_jumps_only"),
			'Retraction_Distance_millimeters': "0.7",
			'Restart_Extra_Distance_millimeters': storedSettingFloat('retraction_extra'),
		},'alteration': {
			'Activate_Alteration': storedSetting('add_start_end_gcode'),
			'Name_of_End_File': "end.gcode",
			'Name_of_Start_File': "start.gcode",
			'Remove_Redundant_Mcode': "True",
			'Replace_Variable_with_Setting': DEFSET,
		},'export': {
			'Activate_Export': "True",
			'Add_Descriptive_Extension': DEFSET,
			'Add_Export_Suffix': "False",
			'Add_Profile_Extension': DEFSET,
			'Add_Timestamp_Extension': DEFSET,
			'Also_Send_Output_To': DEFSET,
			'Analyze_Gcode': DEFSET,
			'Comment_Choice': DEFSET,
			'Do_Not_Change_Output': DEFSET,
			'binary_16_byte': DEFSET,
			'gcode_step': DEFSET,
			'gcode_time_segment': DEFSET,
			'gcode_small': DEFSET,
			'File_Extension': storedSetting('gcode_extension'),
			'Name_of_Replace_File': DEFSET,
			'Save_Penultimate_Gcode': "False",
		}
	}

def safeConfigName(name):
	return name.replace("=", "").replace(":", "").replace(" ", "_").replace("(", "").replace(")", "")

def getReadRepository(repository):
	"Read the configuration for this 'repository'"
	
	info = getProfileInformation()
	if not info.has_key(repository.name):
		print("Warning: Plugin: " + repository.name + " missing from Cura info")
		return repository
	info = info[repository.name]
	
	#print('getReadRepository:', repository.name)
	for p in repository.preferences:
		name = safeConfigName(p.name)
		if not info.has_key(name):
			print("Setting: " + repository.name + ":" + name + " missing from Cura info")
			continue
		if isinstance(info[name], types.FunctionType):
			p.setValueToString(str(info[name](p)))
		else:
			p.setValueToString(str(info[name]))

	return repository

def printProgress(layerIndex, procedureName):
	print("Progress[" + procedureName + ":" + str(layerIndex+1) + "]")
	sys.stdout.flush()

def printProgressByNumber(layerIndex, numberOfLayers, procedureName):
	print("Progress[" + procedureName + ":" + str(layerIndex+1) + ":" + str(numberOfLayers) + "]")
	sys.stdout.flush()

def getAlterationFileLines(fileName):
	'Get the alteration file line and the text lines from the fileName in the alterations directories.'
	return getAlterationLines(fileName)

def getAlterationLines(fileName):
	return archive.getTextLines(getAlterationFile(fileName))

def getAlterationFile(fileName):
	return profile.getAlterationFileContents(fileName)

####################################
## Configuration settings classes ##
####################################

class GeneralSetting(object):
	"Just a basic setting subclass"
	def getFromValue( self, name, repository, value ):
		#print('GeneralSetting:', name, repository, value )
		self.name = name
		self.value = value
		repository.preferences.append(self)
		return self

class StringSetting(GeneralSetting):
	"A class to display, read & write a string."
	def setValueToString(self, value):
		self.value = value

class BooleanSetting( GeneralSetting ):
	"A class to display, read & write a boolean."
	def setValueToString(self, value):
		self.value = str(value) == "True"

class LatentStringVar(object):
	"This is actually used as 'group' object for Radio buttons. (Did I mention the code is a mess?)"
	"This class doesn't have a name, and isn't really used for anything. It doesn't even know which repository it belongs to"

class Radio( BooleanSetting ):
	"A class to display, read & write a boolean with associated radio button."
	def getFromRadio( self, latentStringVar, name, repository, value ):
		"Initialize."
		#print('Radio->getFromRadio:', latentStringVar, name, repository, value )
		self.name = name
		self.value = value
		repository.preferences.append(self)
		return self

class RadioCapitalized( Radio ):
	"A class to display, read & write a boolean with associated radio button."

class RadioCapitalizedButton( Radio ):
	"A class to display, read & write a boolean with associated radio button. With an added configuration dialog button"
	"Only used for the extra export options, which we are not using, so ignore the path for now"
	def getFromPath( self, latentStringVar, name, path, repository, value ):
		"Initialize."
		#print('RadioCapitalizedButton->getFromPath:', latentStringVar, name, path, repository, value )
		self.name = name
		self.value = value
		repository.preferences.append(self)
		return self
		
class FileNameInput(StringSetting):
	"A class to display, read & write a fileName."
	def getFromFileName( self, fileTypes, name, repository, value ):
		#print('FileNameInput:getFromFileName:', self, fileTypes, name, repository, value )
		self.name = name
		self.value = value
		return self

class HelpPage(object):
	"A class to open a help page."
	def getOpenFromAbsolute( self, hypertextAddress ):
		return self

class MenuButtonDisplay(object):
	"A class to add a combo box selection."
	def getFromName( self, name, repository ):
		#print('MenuButtonDisplay->getFromName:', name, repository )
		self.name = name
		self.value = "ERROR"
		self.radioList = []
		repository.preferences.append(self)
		return self
	
	def addRadio(self, radio, default):
		if default:
			self.value = radio.name
		self.radioList.append(radio)
	
	def setValueToString(self, value):
		valueFound = False
		for radio in self.radioList:
			if radio.name == value:
				valueFound = True;
		if valueFound:
			self.value = value
			for radio in self.radioList:
				radio.value = (radio.name == value)

class MenuRadio( BooleanSetting ):
	"A class to display, read & write a boolean with associated combo box selection."
	def getFromMenuButtonDisplay( self, menuButtonDisplay, name, repository, value ):
		"Initialize."
		#print('MenuRadio->getFromMenuButtonDisplay:', menuButtonDisplay, name, repository, value )
		self.name = name
		self.value = value
		menuButtonDisplay.addRadio(self, value)
		return self

class LabelDisplay(object):
	"A class to add a label."
	def getFromName( self, name, repository ):
		"Initialize."
		return self

class FloatSetting(GeneralSetting):
	"A class to display, read & write a float."
	def setValueToString(self, value):
		self.value = float(value)

class FloatSpin( FloatSetting ):
	"A class to display, read & write an float in a spin box."
	def getFromValue(self, from_, name, repository, to, value):
		"Initialize."
		self.name = name
		self.value = value
		if repository != None:
			repository.preferences.append(self)
		return self

class LabelSeparator(object):
	"A class to add a label and menu separator."
	def getFromRepository( self, repository ):
		"Initialize."
		return self

class IntSpin(FloatSpin):
	"A class to display, read & write an int in a spin box."
	def getSingleIncrementFromValue( self, from_, name, repository, to, value ):
		"Initialize."
		self.name = name
		self.value = value
		repository.preferences.append(self)
		return self

	def setValueToString(self, value):
		self.value = int(value)

##########################
# Helper classes
##########################

class LayerCount(object):
	'A class to handle the layerIndex.'
	def __init__(self):
		'Initialize.'
		self.layerIndex = -1

	def __repr__(self):
		'Get the string representation of this LayerCount.'
		return str(self.layerIndex)

	def printProgressIncrement(self, procedureName):
		'Print progress then increment layerIndex.'
		self.layerIndex += 1
		printProgress(self.layerIndex, procedureName)

