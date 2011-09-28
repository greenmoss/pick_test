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
from pyglet.gl import *
import sys

#---------------------------------

class Images(object):
	'Keep track of all images'
	selected_image=None
	mask=False
	num=0
	sprite_batch = pyglet.graphics.Batch()
	sprite_group = pyglet.graphics.OrderedGroup(0)
	mask_batch = pyglet.graphics.Batch()
	mask_group = pyglet.graphics.OrderedGroup(1)

	def __init__(self):
		self.images=[]

	def create_image(self, offset=0):
		self.num+=1
		image=Image(self.num,'graphic.png',offset)

		image.sprite.batch = self.sprite_batch
		image.sprite.group = self.sprite_group

		image.sprite_mask.batch = self.mask_batch
		image.sprite_mask.group = self.mask_group

		self.images.append(image)
		return image

	def click(self,x,y):
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glLoadIdentity()
		self.mask_batch.draw()

		# read the pixel color of the selection area
		c=(GLubyte * 3)()
		glReadBuffer(GL_BACK)
		glReadPixels(x,y,1,1,GL_RGB,GL_UNSIGNED_BYTE,c)
		color=(c[0],c[1],c[2])
		print "Color =",str(color)

		self.selected_image = None
		for image in self.images:
			if image.id_color==color:
				image.touch(x,y)
				self.selected_image = image

	def draw(self):
		if self.mask:
			self.mask_batch.draw()
		else:
			self.sprite_batch.draw()

#---------------------------------
class Image(object):
	x,y=0,0

	def __init__(self,id,image,offset=0):
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
		self.sprite.x=160+offset*160
		self.sprite.y=240

		# image mask
		mask=pyglet.image.create(self.image.width,self.image.height)
		mask.image_data.format="A"
		mask.image_data.pitch=self.image.width
		mask.texture.blit_into(self.image,0,0,0)

		# image mask sprite
		self.sprite_mask = pyglet.sprite.Sprite(
			mask.texture,
			self.px,
			self.py
		)
		self.sprite_mask.color = self.id_color
		self.sprite_mask.scale = self.sprite.scale
		self.sprite_mask.x = self.sprite.x
		self.sprite_mask.y = self.sprite.y

	def touch(self,mouse_x,mouse_y):
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
class Window(pyglet.window.Window):

	def __init__(self):
		self.scene = Images()
		for n in range (0,3):
			self.scene.create_image(n)

		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glDepthFunc(GL_LEQUAL)
		super(Window, self).__init__(caption='Objects')

	def on_key_press(self, symbol, modifiers):
		if symbol==pyglet.window.key.F1:
			print "Toggle Color Masks"
			self.scene.mask=not self.scene.mask
		elif symbol==pyglet.window.key.RETURN:
			self.scene.create_image()
		elif symbol==pyglet.window.key.ESCAPE:
			sys.exit()
		else: print "KEY "+pyglet.window.key.symbol_string(symbol)

	def on_mouse_press(self, x, y, button, modifiers):
		print "Mouse click at",str((x,y))
		self.scene.click(x,y)

	def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
		if self.scene.selected_image == None:
			return
		self.scene.selected_image.sprite.x+=dx
		self.scene.selected_image.sprite.y+=dy
		self.scene.selected_image.sprite_mask.x=self.scene.selected_image.sprite.x
		self.scene.selected_image.sprite_mask.y=self.scene.selected_image.sprite.y
	
	def on_draw(self):
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glLoadIdentity()
		self.scene.draw()

#---------------------------------
print "Alpha Selection"
print "---------------------------------"
print "Camera			-> Drag LMB,CMB,RMB"
print ""
print "Select image	  -> Click LMB"
print "Move image XY	 -> Drag LMB"
print "Add graphic	   -> RETURN"
print ""

window = Window()
pyglet.app.run()
