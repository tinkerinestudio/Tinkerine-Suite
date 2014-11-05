import re

def getValue(line, key, default = None):
	if not key in line or (';' in line and line.find(key) > line.find(';')):
		return default
	subPart = line[line.find(key) + 1:]
	m = re.search('^[0-9]+\.?[0-9]*', subPart)
	if m is None:
		return default
	try:
		return float(m.group(0))
	except:
		return default
		


def delete(filename, x1, y1, x2, y2, parent):
	with open(filename, "r") as f:
		lines = f.readlines()
	z = 0.
	x = 0.
	y = 0.
	e = 0.
	s = 0.
	
	pauseState = 0
	currentSectionType = 'CUSTOM'
	deleteline = False
	endofdeleteline = False
	endpoint = False
	startpoint = False
	with open(filename, "w") as f:
		for line in lines:
			if line.startswith(';'):
				if line.startswith(';TYPE:'):
					currentSectionType = line[6:].strip()
				f.write(line)
				continue
			if currentSectionType == 'SUPPORT':
				
				if getValue(line, 'G', None) == 1 or getValue(line, 'G', None) == 0:
					newZ = getValue(line, 'Z', z)
					x = getValue(line, 'X', x)
					y = getValue(line, 'Y', y)
					
					if x1-0.1 < x < x1+0.1 and y1-0.1 < y < y1+0.1:
						startpoint = True
						#print line
					if x2-0.1 < x < x2+0.1 and y2-0.1 < y < y2+0.1:
						endpoint = True
						e = getValue(line, 'E', e) #extrusion
						z = getValue(line, 'Z', z) #z
						s = getValue(line, 'F', s) #speed
					#if x == x1 and y == y1:
					#	deleteline = True
					#	print line
					#if x == x2 and y == y2:
					#	endofdeleteline = True
					#	e = getValue(line, 'E', e)
			if endpoint:
				f.write("G1 X%f Y%f Z%f F%f\n" % (x,y,z,s))
				f.write("G92 E%f\n" % (e))
				endpoint = False
			else:
				f.write(line)

			#if deleteline == False:
			#	f.write(line)
			#elif deleteline == True and endofdeleteline == True:
			#	deleteline = False
			#	endofdeleteline = False
			#	f.write("G92 E%f\n" % (e))
	parent.OnSliceDone(filename)
