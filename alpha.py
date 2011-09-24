#
# Alpha Selection Example for pyglet 1.x
#
# 3D Selection of 2D images with alpha transparency.
#
# When mouse is pressed, draw the color coded masks in the back buffer,
# and read the color. If there is a layer with the color id, get the
# point where the mouse line intersects the plane, and get the coords
# in the plane.
#
# (c)2008 Txema Vicente
#
#---------------------------------

import math
from pyglet import window,image
from pyglet.window import key
from pyglet.gl import *
import sys

#---------------------------------

class Layers(object):
	'''The Scene
	'''
	selected=None
	mask=False
	num=0
	def __init__(self):
		self.layers=[]

	def create_layer(self):
		self.num+=1
		layer=Layer(self.num,'graphic.png')
		self.layers.append(layer)
		return layer

	def click(self,x,y):
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glLoadIdentity()
		for layer in self.layers:
			layer.selected=False
			layer.draw(True)

		  # read the pixel color of the selection area
		c=(GLfloat * 3)()
		glReadBuffer(GL_BACK)
		glReadPixels(x,y,1,1,GL_RGB,GL_FLOAT,c)
		color=(float(c[0]),float(c[1]),float(c[2]))
		print "Color =",str(color)

		self.selected = None
		for layer in self.layers:
			if layer.id_color==color:
				layer.touch(x,y)
				self.selected = layer

	def draw(self):
		for layer in self.layers:
			layer.draw(self.mask)

#---------------------------------
class Layer(object):
	selected=False
	x,y,z=0,0,0

	def __init__(self,id,img):
		self.id=id
		self.img=image.load(img)
		self.id_color=self.derive_color()
		self.px=-self.img.width/2
		self.py=-self.img.height/2

		# image mask
		mask=image.create(self.img.width,self.img.height)
		mask.image_data.format="A"
		mask.image_data.pitch=self.img.width
		mask.texture.blit_into(self.img,0,0,0)
		self.mask=mask

	def touch(self,mouse_x,mouse_y):
		self.selected=True
		print "Space point=",str((mouse_x,mouse_y))
		print "Plane point=",str((mouse_x-self.x,mouse_y-self.y))

	def draw(self,mask=False):
		glPushMatrix()
		glTranslatef(self.x,self.y,self.z)
		if mask:
			glColor4f(self.id_color[0],self.id_color[1],self.id_color[2],1)
			self.mask.blit(self.px,self.py,0)
			glColor4f(1,1,1,1)
		else:
			self.img.blit(self.px,self.py,0)
		glPopMatrix()

	def derive_color(self):
		'''Returns a color derived from int self.id'''
		# not sure what H, S, and I are supposed to signify
		H=self.id*39
		S=1./(1+int((self.id+1)/40.))
		I=0.5
	
		H+=180
		H=H%360
		Z=1+int(H/120)
		if H>=120 and H<240: H-=120
		elif H>=240: H-=240
	
		ang=float((H*9./6.)-90.)
		c1=S*(0.5+I)
		c2=S*math.cos(ang*-0.01745)
		c3=S*(0.5-I)
	
		if H>60:
			temp=c1
			c1=c2
			c2=temp
	
		color=(0,0,0)
		if Z==1: color=(c1,c2,c3)
		elif Z==2: color=(c3,c1,c2)
		elif Z==3: color=(c2,c3,c1)
		print ("original color: ", color)
	
		# When the mask is painted with glColor,
		# the color returned by glReadPixels is not exactly the same.
		# This code paints and then returns the real color.
		glMatrixMode(GL_PROJECTION)
		glPushMatrix()
		glLoadIdentity()
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		fc=(GLfloat * 4)()
		glGetFloatv(GL_COLOR_CLEAR_VALUE,fc)
		glClearColor(color[0],color[1],color[2],1)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		read_colors=(GLfloat * 3)()
		glReadBuffer(GL_BACK)
		glReadPixels(0,0,1,1,GL_RGB,GL_FLOAT,read_colors)
		glClearColor(fc[0],fc[1],fc[2],fc[3])
		painted_color=(float(read_colors[0]),float(read_colors[1]),float(read_colors[2]))
		glMatrixMode(GL_PROJECTION)
		glPopMatrix()
		glMatrixMode(GL_MODELVIEW)
		glPopMatrix()
		print ("painted color: ", painted_color)
		return painted_color

#---------------------------------
class Camera():

	def key(self, symbol, modifiers):
		if symbol==key.F1:
			print "Toggle Color Masks"
			scene.mask=not scene.mask
		elif symbol==key.RETURN:
			scene.create_layer()
		elif symbol==key.ESCAPE:
			sys.exit()
		else: print "KEY "+key.symbol_string(symbol)

	def click(self, x, y, button, modifiers):
		print "Mouse click at",str((x,y))
		scene.click(x,y)

	def drag(self, x, y, dx, dy, button, modifiers):
		if scene.selected == None:
			return
		scene.selected.x+=dx
		scene.selected.y+=dy

#---------------------------------
print "Alpha Selection"
print "---------------------------------"
print "Camera			-> Drag LMB,CMB,RMB"
print ""
print "Select layer	  -> Click LMB"
print "Move layer XY	 -> Drag LMB"
print "Add graphic	   -> RETURN"
print ""

scene=Layers()
cam=Camera()
win = window.Window()
win.on_key_press=cam.key
win.on_mouse_drag=cam.drag
win.on_mouse_press=cam.click
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
glDepthFunc(GL_LEQUAL)

for n in range (0,3):
	layer=scene.create_layer()
	layer.x=160+n*160
	layer.y=240
	layer.z=n-1

while not win.has_exit:
	win.dispatch_events()
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	glLoadIdentity()
	scene.draw()
	win.flip() 
