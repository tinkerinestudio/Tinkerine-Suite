import PIL
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw
from Cura.gui.util import opengl
from OpenGL.GL import *
class tooltipText(object):
	def __init__(self, x, y, text, font, fontsize, colour):
		self._x = x
		self._y = y
		self._text = text
		self._font = font
		self._fontsize = fontsize
		self._colour = colour
		self._pBits = None
		self._oldtext = None
		self.mode = None
		
		#self.makeText()
		
		#self.displayText()
	
	def doText(self):
		self.makeText()
		self.displayText()
	
	def makeText(self):
		if self._oldtext != self._text:
			font = ImageFont.truetype(self._font,self._fontsize)
			img=Image.new("RGBA", (300,200),(self._colour[0],self._colour[1],self._colour[2],0))

			draw = ImageDraw.Draw(img)
			draw.text((0, 200-self._fontsize),self._text,self._colour,font=font)
			draw = ImageDraw.Draw(img)
			#draw = ImageDraw.Draw(img)
			img_flip = img.transpose(Image.FLIP_TOP_BOTTOM)
			#draw = ImageDraw.Draw(img)
			#draw = ImageDraw.Draw(img)

			pBits2 = img.tostring("raw", "RGBA")
			pBits = img_flip.tostring("raw", "RGBA")
			#print "i made a pbit"
			self._pBits = pBits2
			#self.displayText()
			self._oldtext = self._text
			print "making text"
			return self._pBits
		else:
			return self._pBits
	def displayText2(self):
		glEnable(GL_TEXTURE_2D)
		glPushMatrix()
		glColor4f(1,1,1,1)
		glTranslate(self._x+300, self._y,0)
		glScale( 300,200,0)
			
		glBegin(GL_QUADS)
		glTexCoord2f(1, 0)
		glVertex2f(0,-1)
		glTexCoord2f(0, 0)
		glVertex2f(-1,-1)
		glTexCoord2f(0, 1)
		glVertex2f(-1, 0)
		glTexCoord2f(1, 1)
		glVertex2f(0, 0)
		glEnd()
		glDisable(GL_TEXTURE_2D)
		glPopMatrix()
		
	def displayText(self):
		#print "why"
		#print len(self._pBits)
		vPort = glGetIntegerv(GL_VIEWPORT)
		#glMatrixMode(GL_PROJECTION)
		#glEnable(GL_TEXTURE_2D)
		glPushMatrix()
		glLoadIdentity()
		glTranslate(self._x, self._y,0)
		glRasterPos(0,0,0)
		glOrtho(0, vPort[2], 0, vPort[3], -1, 1)
		glMatrixMode(GL_MODELVIEW)
		glDrawPixels(300, 200, GL_RGBA, GL_UNSIGNED_BYTE, self._pBits)
		glEnd()
		glDisable(GL_TEXTURE_2D)
		glPopMatrix()