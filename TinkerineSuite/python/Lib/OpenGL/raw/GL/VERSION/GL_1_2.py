'''OpenGL extension VERSION.GL_1_2

Automatically generated by the get_gl_extensions script, do not edit!
'''
from OpenGL import platform, constants, constant, arrays
from OpenGL import extensions
from OpenGL.GL import glget
import ctypes
EXTENSION_NAME = 'GL_VERSION_GL_1_2'
_DEPRECATED = False
GL_UNSIGNED_BYTE_3_3_2 = constant.Constant( 'GL_UNSIGNED_BYTE_3_3_2', 0x8032 )
GL_UNSIGNED_SHORT_4_4_4_4 = constant.Constant( 'GL_UNSIGNED_SHORT_4_4_4_4', 0x8033 )
GL_UNSIGNED_SHORT_5_5_5_1 = constant.Constant( 'GL_UNSIGNED_SHORT_5_5_5_1', 0x8034 )
GL_UNSIGNED_INT_8_8_8_8 = constant.Constant( 'GL_UNSIGNED_INT_8_8_8_8', 0x8035 )
GL_UNSIGNED_INT_10_10_10_2 = constant.Constant( 'GL_UNSIGNED_INT_10_10_10_2', 0x8036 )
GL_TEXTURE_BINDING_3D = constant.Constant( 'GL_TEXTURE_BINDING_3D', 0x806A )
GL_PACK_SKIP_IMAGES = constant.Constant( 'GL_PACK_SKIP_IMAGES', 0x806B )
GL_PACK_IMAGE_HEIGHT = constant.Constant( 'GL_PACK_IMAGE_HEIGHT', 0x806C )
GL_UNPACK_SKIP_IMAGES = constant.Constant( 'GL_UNPACK_SKIP_IMAGES', 0x806D )
GL_UNPACK_IMAGE_HEIGHT = constant.Constant( 'GL_UNPACK_IMAGE_HEIGHT', 0x806E )
GL_TEXTURE_3D = constant.Constant( 'GL_TEXTURE_3D', 0x806F )
GL_PROXY_TEXTURE_3D = constant.Constant( 'GL_PROXY_TEXTURE_3D', 0x8070 )
GL_TEXTURE_DEPTH = constant.Constant( 'GL_TEXTURE_DEPTH', 0x8071 )
GL_TEXTURE_WRAP_R = constant.Constant( 'GL_TEXTURE_WRAP_R', 0x8072 )
GL_MAX_3D_TEXTURE_SIZE = constant.Constant( 'GL_MAX_3D_TEXTURE_SIZE', 0x8073 )
GL_UNSIGNED_BYTE_2_3_3_REV = constant.Constant( 'GL_UNSIGNED_BYTE_2_3_3_REV', 0x8362 )
GL_UNSIGNED_SHORT_5_6_5 = constant.Constant( 'GL_UNSIGNED_SHORT_5_6_5', 0x8363 )
GL_UNSIGNED_SHORT_5_6_5_REV = constant.Constant( 'GL_UNSIGNED_SHORT_5_6_5_REV', 0x8364 )
GL_UNSIGNED_SHORT_4_4_4_4_REV = constant.Constant( 'GL_UNSIGNED_SHORT_4_4_4_4_REV', 0x8365 )
GL_UNSIGNED_SHORT_1_5_5_5_REV = constant.Constant( 'GL_UNSIGNED_SHORT_1_5_5_5_REV', 0x8366 )
GL_UNSIGNED_INT_8_8_8_8_REV = constant.Constant( 'GL_UNSIGNED_INT_8_8_8_8_REV', 0x8367 )
GL_UNSIGNED_INT_2_10_10_10_REV = constant.Constant( 'GL_UNSIGNED_INT_2_10_10_10_REV', 0x8368 )
GL_BGR = constant.Constant( 'GL_BGR', 0x80E0 )
GL_BGRA = constant.Constant( 'GL_BGRA', 0x80E1 )
GL_MAX_ELEMENTS_VERTICES = constant.Constant( 'GL_MAX_ELEMENTS_VERTICES', 0x80E8 )
GL_MAX_ELEMENTS_INDICES = constant.Constant( 'GL_MAX_ELEMENTS_INDICES', 0x80E9 )
GL_CLAMP_TO_EDGE = constant.Constant( 'GL_CLAMP_TO_EDGE', 0x812F )
GL_TEXTURE_MIN_LOD = constant.Constant( 'GL_TEXTURE_MIN_LOD', 0x813A )
GL_TEXTURE_MAX_LOD = constant.Constant( 'GL_TEXTURE_MAX_LOD', 0x813B )
GL_TEXTURE_BASE_LEVEL = constant.Constant( 'GL_TEXTURE_BASE_LEVEL', 0x813C )
GL_TEXTURE_MAX_LEVEL = constant.Constant( 'GL_TEXTURE_MAX_LEVEL', 0x813D )
GL_SMOOTH_POINT_SIZE_RANGE = constant.Constant( 'GL_SMOOTH_POINT_SIZE_RANGE', 0xB12 )
GL_SMOOTH_POINT_SIZE_GRANULARITY = constant.Constant( 'GL_SMOOTH_POINT_SIZE_GRANULARITY', 0xB13 )
GL_SMOOTH_LINE_WIDTH_RANGE = constant.Constant( 'GL_SMOOTH_LINE_WIDTH_RANGE', 0xB22 )
GL_SMOOTH_LINE_WIDTH_GRANULARITY = constant.Constant( 'GL_SMOOTH_LINE_WIDTH_GRANULARITY', 0xB23 )
GL_ALIASED_LINE_WIDTH_RANGE = constant.Constant( 'GL_ALIASED_LINE_WIDTH_RANGE', 0x846E )
glBlendColor = platform.createExtensionFunction( 
'glBlendColor',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLclampf,constants.GLclampf,constants.GLclampf,constants.GLclampf,),
doc='glBlendColor(GLclampf(red), GLclampf(green), GLclampf(blue), GLclampf(alpha)) -> None',
argNames=('red','green','blue','alpha',),
deprecated=_DEPRECATED,
)

glBlendEquation = platform.createExtensionFunction( 
'glBlendEquation',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLenum,),
doc='glBlendEquation(GLenum(mode)) -> None',
argNames=('mode',),
deprecated=_DEPRECATED,
)

glDrawRangeElements = platform.createExtensionFunction( 
'glDrawRangeElements',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLenum,constants.GLuint,constants.GLuint,constants.GLsizei,constants.GLenum,ctypes.c_void_p,),
doc='glDrawRangeElements(GLenum(mode), GLuint(start), GLuint(end), GLsizei(count), GLenum(type), c_void_p(indices)) -> None',
argNames=('mode','start','end','count','type','indices',),
deprecated=_DEPRECATED,
)

glTexImage3D = platform.createExtensionFunction( 
'glTexImage3D',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLenum,constants.GLint,constants.GLint,constants.GLsizei,constants.GLsizei,constants.GLsizei,constants.GLint,constants.GLenum,constants.GLenum,ctypes.c_void_p,),
doc='glTexImage3D(GLenum(target), GLint(level), GLint(internalformat), GLsizei(width), GLsizei(height), GLsizei(depth), GLint(border), GLenum(format), GLenum(type), c_void_p(pixels)) -> None',
argNames=('target','level','internalformat','width','height','depth','border','format','type','pixels',),
deprecated=_DEPRECATED,
)

glTexSubImage3D = platform.createExtensionFunction( 
'glTexSubImage3D',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLenum,constants.GLint,constants.GLint,constants.GLint,constants.GLint,constants.GLsizei,constants.GLsizei,constants.GLsizei,constants.GLenum,constants.GLenum,ctypes.c_void_p,),
doc='glTexSubImage3D(GLenum(target), GLint(level), GLint(xoffset), GLint(yoffset), GLint(zoffset), GLsizei(width), GLsizei(height), GLsizei(depth), GLenum(format), GLenum(type), c_void_p(pixels)) -> None',
argNames=('target','level','xoffset','yoffset','zoffset','width','height','depth','format','type','pixels',),
deprecated=_DEPRECATED,
)

glCopyTexSubImage3D = platform.createExtensionFunction( 
'glCopyTexSubImage3D',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLenum,constants.GLint,constants.GLint,constants.GLint,constants.GLint,constants.GLint,constants.GLint,constants.GLsizei,constants.GLsizei,),
doc='glCopyTexSubImage3D(GLenum(target), GLint(level), GLint(xoffset), GLint(yoffset), GLint(zoffset), GLint(x), GLint(y), GLsizei(width), GLsizei(height)) -> None',
argNames=('target','level','xoffset','yoffset','zoffset','x','y','width','height',),
deprecated=_DEPRECATED,
)
# import legacy entry points to allow checking for bool(entryPoint)
from OpenGL.raw.GL.VERSION.GL_1_2_DEPRECATED import *
