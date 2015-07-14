from __future__ import absolute_import
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import os
import sys
import gettext

__all__ = ['getPathForResource', 'getPathForImage', 'getPathForMesh']


if sys.platform.startswith('darwin'):
	if hasattr(sys, 'frozen'):
		from Foundation import *
		resourceBasePath = NSBundle.mainBundle().resourcePath()
	else:
		resourceBasePath = os.path.join(os.path.dirname(__file__), "../resources")
else:
	if hasattr(sys, 'frozen'):
		resourceBasePath = os.path.join(os.path.dirname(__file__), "../../resources")
	else:
		resourceBasePath = os.path.join(os.path.dirname(__file__), "../resources")

def getPathForResource(dir, subdir, resource_name):
	assert os.path.isdir(dir), "{p} is not a directory".format(p=dir)
	path = os.path.normpath(os.path.join(dir, subdir, resource_name))
	assert os.path.isfile(path), "{p} is not a file.".format(p=path)
	return path

def getPathForImage(name):
	return getPathForResource(resourceBasePath, 'images', name)

def getPathForMesh(name):
	return getPathForResource(resourceBasePath, 'meshes', name)

def getPathForFirmware(name):
	return getPathForResource(resourceBasePath, 'firmware', name)

def setupLocalization(selectedBrand = None, selectedLanguage = None):
	#Default to english, tinkerine
	languages = ['en_CA']
	brand = 'tinkerine'

	if selectedBrand is not None:
		for item in getBrandOptions():
			if item == selectedBrand and item is not None:
				brand = item

	if selectedLanguage is not None:
		for item in getLanguageOptions():
			if item[1] == selectedLanguage and item[0] is not None:
				languages = [item[0]]

	locale_path = os.path.normpath(os.path.join(resourceBasePath, 'locale-'+brand))
	translation = gettext.translation('tinkerine', locale_path, languages, fallback=True)
	translation.install(unicode=True)

def getLanguageOptions():
	return [
		['en_CA', 'Canadian English'],
	]

def getBrandOptions():
	return [
		'tinkerine',
		'varitronics',
	]