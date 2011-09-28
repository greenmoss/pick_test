#
# Alpha Selection Example for pyglet 1.x
#
# 3D Selection of 2D images with alpha transparency.
#
# When mouse is pressed, draw the color coded masks in the back buffer,
# and read the color. If there is an image with the color id, get the
# point where the mouse line intersects the plane, and get the coords
# in the plane.
#
# (c)2008 Txema Vicente
#
#---------------------------------

import math
import pyglet
from pyglet.window import key
from pyglet.gl import *
import sys

#---------------------------------

class Images(object):
	'Keep track of all images'
	selected=None
	mask=False
	num=0
	sprite_batch = pyglet.graphics.Batch()
	sprite_group = pyglet.graphics.OrderedGroup(0)
	mask_batch = pyglet.graphics.Batch()
	mask_group = pyglet.graphics.OrderedGroup(1)

	def __init__(self):
		self.images=[]

	def create_image(self):
		self.num+=1
		image=Image(self.num,'graphic.png')
		image.sprite.batch = self.sprite_batch
		image.sprite.group = self.sprite_group
		image.mask_sprite.batch = self.mask_batch
		image.mask_sprite.group = self.mask_group
		self.images.append(image)
		return image

	def click(self,x,y):
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glLoadIdentity()
		for image in self.images:
			image.selected=False
		self.mask_batch.draw()

		# read the pixel color of the selection area
		c=(GLubyte * 3)()
		glReadBuffer(GL_BACK)
		glReadPixels(x,y,1,1,GL_RGB,GL_UNSIGNED_BYTE,c)
		color=(c[0],c[1],c[2])
		print "Color =",str(color)

		self.selected = None
		for image in self.images:
			if image.id_color==color:
				image.touch(x,y)
				self.selected = image

	def draw(self):
		if self.mask:
			self.mask_batch.draw()
		else:
			self.sprite_batch.draw()

#---------------------------------
class Image(object):
	selected=False
	x,y=0,0

	def __init__(self,id,image):
		self.id=id
		self.image=pyglet.image.load(image)
		self.id_color=self.derive_color()
		self.px=-self.image.width/2
		self.py=-self.image.height/2

		# image sprite
		self.sprite = pyglet.sprite.Sprite(
			pyglet.resource.image(image),
			self.px,
			self.py
		)
		self.sprite.scale = 0.1

		# image mask
		mask=pyglet.image.create(self.image.width,self.image.height)
		mask.image_data.format="A"
		mask.image_data.pitch=self.image.width
		mask.texture.blit_into(self.image,0,0,0)

		# image mask sprite
		self.mask_sprite = pyglet.sprite.Sprite(
			mask.texture,
			self.px,
			self.py
		)
		self.mask_sprite.color = self.id_color
		self.mask_sprite.scale = self.sprite.scale

	def touch(self,mouse_x,mouse_y):
		self.selected=True
		print "Space point=",str((mouse_x,mouse_y))
		print "Plane point=",str((mouse_x-self.x,mouse_y-self.y))

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
		c1=int(S*(0.5+I)*255)
		c2=int(S*math.cos(ang*-0.01745)*255)
		c3=int(S*(0.5-I)*255)
	
		if H>60:
			temp=c1
			c1=c2
			c2=temp
	
		color=(0,0,0)
		if Z==1: color=(c1,c2,c3)
		elif Z==2: color=(c3,c1,c2)
		elif Z==3: color=(c2,c3,c1)
		print "from id %d, derived color %s"%(self.id,str(color))
		return color
	
#---------------------------------
class Camera():

	def key(self, symbol, modifiers):
		if symbol==key.F1:
			print "Toggle Color Masks"
			scene.mask=not scene.mask
		elif symbol==key.RETURN:
			scene.create_image()
		elif symbol==key.ESCAPE:
			sys.exit()
		else: print "KEY "+key.symbol_string(symbol)

	def click(self, x, y, button, modifiers):
		print "Mouse click at",str((x,y))
		scene.click(x,y)

	def drag(self, x, y, dx, dy, button, modifiers):
		if scene.selected == None:
			return
		scene.selected.sprite.x+=dx
		scene.selected.sprite.y+=dy
		scene.selected.mask_sprite.x=scene.selected.sprite.x
		scene.selected.mask_sprite.y=scene.selected.sprite.y

#---------------------------------
print "Alpha Selection"
print "---------------------------------"
print "Camera			-> Drag LMB,CMB,RMB"
print ""
print "Select image	  -> Click LMB"
print "Move image XY	 -> Drag LMB"
print "Add graphic	   -> RETURN"
print ""

scene=Images()
cam=Camera()
win = pyglet.window.Window()
win.on_key_press=cam.key
win.on_mouse_drag=cam.drag
win.on_mouse_press=cam.click
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
glDepthFunc(GL_LEQUAL)

for n in range (0,3):
	image=scene.create_image()
	image.sprite.x=160+n*160
	image.sprite.y=240
	image.mask_sprite.x=image.sprite.x
	image.mask_sprite.y=image.sprite.y

while not win.has_exit:
	win.dispatch_events()
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	glLoadIdentity()
	scene.draw()
	win.flip() 
