'''OpenGL extension NV.texture_rectangle

This module customises the behaviour of the 
OpenGL.raw.GL.NV.texture_rectangle to provide a more 
Python-friendly API

Overview (from the spec)
	
	OpenGL texturing is limited to images with power-of-two dimensions
	and an optional 1-texel border.  NV_texture_rectangle extension
	adds a new texture target that supports 2D textures without requiring
	power-of-two dimensions.
	
	Non-power-of-two dimensioned textures are useful for storing
	video images that do not have power-of-two dimensions.  Re-sampling
	artifacts are avoided and less texture memory may be required by using
	non-power-of-two dimensioned textures.  Non-power-of-two dimensioned
	textures are also useful for shadow maps and window-space texturing.
	
	However, non-power-of-two dimensioned (NPOTD) textures have
	limitations that do not apply to power-of-two dimensioned (POT)
	textures.  NPOTD textures may not use mipmap filtering; POTD
	textures support both mipmapped and non-mipmapped filtering.
	NPOTD textures support only the GL_CLAMP, GL_CLAMP_TO_EDGE,
	and GL_CLAMP_TO_BORDER_ARB wrap modes; POTD textures support
	GL_CLAMP_TO_EDGE, GL_REPEAT, GL_CLAMP, GL_MIRRORED_REPEAT_IBM,
	and GL_CLAMP_TO_BORDER.  NPOTD textures do not support an optional
	1-texel border; POTD textures do support an optional 1-texel border.
	
	NPOTD textures are accessed by non-normalized texture coordinates.
	So instead of thinking of the texture image lying in a [0..1]x[0..1]
	range, the NPOTD texture image lies in a [0..w]x[0..h] range.
	
	This extension adds a new texture target and related state (proxy,
	binding, max texture size).

The official definition of this extension is available here:
http://www.opengl.org/registry/specs/NV/texture_rectangle.txt
'''
from OpenGL import platform, constants, constant, arrays
from OpenGL import extensions, wrapper
from OpenGL.GL import glget
import ctypes
from OpenGL.raw.GL.NV.texture_rectangle import *
### END AUTOGENERATED SECTION