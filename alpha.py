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

DOT="dot.png"
LAYER="layer.png"

laser=image.load(DOT)
DEG2RAD=-0.01745

def real_color(c):
    '''When the mask is painted with glColor,
       the color returned by glReadPixels is not exactly the same.
       This function paints and then returns the real color.
    '''
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    fc=(GLfloat * 4)()
    glGetFloatv(GL_COLOR_CLEAR_VALUE,fc)
    glClearColor(c[0],c[1],c[2],1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    punto=(GLfloat * 3)()
    glReadBuffer(GL_BACK)
    glReadPixels(0,0,1,1,GL_RGB,GL_FLOAT,punto)
    glClearColor(fc[0],fc[1],fc[2],fc[3])
    p=(float(punto[0]),float(punto[1]),float(punto[2]))
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    return p

def hsi_rgb(H,S,I):
    """ This is an arbitrary color conversion, not interesting.
        It can be simpler, but this one is pretty
    """
    H+=180
    H=H%360
    Z=1+int(H/120)
    if H>=120 and H<240: H-=120
    elif H>=240: H-=240

    ang=float((H*9./6.)-90.)
    c1=S*(0.5+I)
    c2=S*math.cos(ang*DEG2RAD)
    c3=S*(0.5-I)

    if H>60:
        temp=c1
        c1=c2
        c2=temp

    if Z==1: return c1,c2,c3
    elif Z==2: return c3,c1,c2
    elif Z==3: return c2,c3,c1
    return 0,0,0

def unique_color(n):
    '''Returns a color for n
    '''
    H=n*39
    S=1./(1+int((n+1)/40.))
    I=0.5
    return real_color(hsi_rgb(H,S,I))

#---------------------------------

class Layers(object):
    '''The Scene
    '''
    selected=None
    mask=False
    num=0
    def __init__(self):
        self.layers=[]

    def load(self,file):
        self.num+=1
        layer=Layer(self.num,file,unique_color(self.num))
        self.layers.append(layer)
        return layer

    def __border(self):
        glColor4f(1,1,1,1)
        glBegin(GL_LINE_LOOP)
        glVertex3f(1,1,0)
        glVertex3f(640,1,0)
        glVertex3f(640,480,0)
        glVertex3f(1,480,0)
        glEnd()

    def __order_z(self):
        z_pre=-32000
        d={}
        good=True
        n=0
        for layer in self.layers:
            z=layer.z
            d[n]=z
            if z<z_pre: good=False
            z_pre=z
            n+=1
        if good: return
        print "Reordering layers"
        temp=[]
        for n,z in sorted(d.items(), lambda x, y: cmp(x[1], y[1])):
            temp.append(self.layers[n])
        self.layers=temp

    def __read_color(self,x,y):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        cam.apply()
        for layer in self.layers:
            layer.selected=False
            layer.draw(True)
        c=(GLfloat * 3)()
        glReadBuffer(GL_BACK)
        glReadPixels(x,y,1,1,GL_RGB,GL_FLOAT,c)
        color=(float(c[0]),float(c[1]),float(c[2]))
        print "Color =",str(color)
        return color

    def __find_layer(self,x,y):
        color=self.__read_color(x,y)
        for layer in self.layers:
            if layer.id_color==color:
                layer.touch(x,y)
                return layer
        return None

    def click(self,x,y):
        self.selected = self.__find_layer(x,y)

    def draw(self):
        self.__border()
        self.__order_z()
        for layer in self.layers:
            layer.draw(self.mask)

#---------------------------------
class Layer(object):
    selected=False
    lx,ly=0,0
    x,y,z=0,0,0
    rx,ry,rz=0,0,0
    mat_mod = (GLdouble * 16)()

    def __init__(self,id,img,id_color):
        self.id=id
        self.img=image.load(img)
        self.id_color=id_color
        self.px=-self.img.width/2
        self.py=-self.img.height/2
        self.__create_mask()

    def __border(self):
        glColor4f(1,0,1,0.5)
        glBegin(GL_LINE_LOOP)
        glVertex3f(-self.px,-self.py,0)
        glVertex3f(self.px,-self.py,0)
        glVertex3f(self.px,self.py,0)
        glVertex3f(-self.px,self.py,0)
        glColor4f(1,1,1,1)
        glEnd()

    def move(self,dx,dy,dz):
        self.x+=dx
        self.y+=dy
        self.z+=dz

    def __create_mask(self):
        print "Creating mask"
        mask=image.create(self.img.width,self.img.height)
        mask.image_data.format="A"
        mask.image_data.pitch=self.img.width
        mask.texture.blit_into(self.img,0,0,0)
        self.mask=mask

    def normal(self):
        '''Devuelve el vector normal.
        '''
        Cx=math.cos(DEG2RAD*self.rx)
        Cy=math.cos(DEG2RAD*self.ry)
        Sx=math.sin(DEG2RAD*self.rx)
        Sy=math.sin(DEG2RAD*self.ry)
        nx=-Sy
        ny=Sx*Cy
        nz=Cy*Cx
        return nx,ny,nz

    def local_point(self,px,py,pz):
        Cx=math.cos(-DEG2RAD*self.rx)
        Cy=math.cos(DEG2RAD*self.ry)
        Cz=math.cos(-DEG2RAD*self.rz)
        Sx=math.sin(-DEG2RAD*self.rx)
        Sy=math.sin(DEG2RAD*self.ry)
        Sz=math.sin(-DEG2RAD*self.rz)
        x=px-self.x
        y=py-self.y
        z=pz-self.z
        lx=Cz*(Cy*x+Sy*(Cx*z-Sx*y))+Sz*(Cx*y+Sx*z)
        ly=Cz*(Cx*y+Sx*z)-Sz*(Cy*x+Sy*(Cx*z-Sx*y))
        self.lx,self.ly=lx,ly

    def touch(self,mouse_x,mouse_y):
        self.selected=True
        px,py,pz=cam.ray_3d(mouse_x,mouse_y,self.mat_mod,
(self.x,self.y,self.z),self.normal())
        print "Space point=",str((px,py,pz))
        self.local_point(px,py,pz)
        print "Plane point=",str((self.lx,self.ly))

    def draw(self,mask=False):
        glGetDoublev(GL_MODELVIEW_MATRIX, self.mat_mod)
        glPushMatrix()
        glTranslatef(self.x,self.y,self.z)
        glRotatef(self.rx, 1, 0, 0)
        glRotatef(self.ry, 0, 1, 0)
        glRotatef(self.rz, 0, 0, 1)
        if mask:
            glColor4f(self.id_color[0],self.id_color[1],self.id_color
[2],1)
            self.mask.blit(self.px,self.py,0)
            glColor4f(1,1,1,1)
        else:
            self.img.blit(self.px,self.py,0)
            if self.selected:
                self.__border()
                laser.blit(self.lx-laser.width/2,self.ly-laser.height/
2,1)
        glPopMatrix()

    def toca(self,px,py):
        px,py,pz=self.toca_3d(px,py)
        if px is None: return None,None
        return self.eje.toca_2d(px,py,pz)

#---------------------------------
class Camera():
    x,y,z=0,0,512
    rx,ry,rz=30,-45,0
    w,h=640,480
    far=8192

    mat_vis = (GLint * 4)()
    mat_pro = (GLdouble * 16)()

    def ray_3d(self,px=0,py=0,matriz=None,punto=(0,0,0),normal=
(0,0,1)):
        '''Get the point where the mouse line touches a plane
        '''
        x,y,z=punto
        nx,ny,nz=normal

        wx,wy,wz = GLdouble(),GLdouble(),GLdouble()
        gluUnProject(px, py, 0.0, matriz, self.mat_pro, self.mat_vis,
wx, wy, wz)
        x0,y0,z0=wx.value,wy.value,wz.value
        gluUnProject(px, py, 1.0, matriz, self.mat_pro, self.mat_vis,
wx, wy, wz)
        x1,y1,z1=wx.value,wy.value,wz.value

        lx, ly, lz = x1-x0, y1-y0, z1-z0
        m=math.sqrt(lx*lx+ly*ly+lz*lz)
        if m==0.: m=1
        ux, uy, uz = lx/m, ly/m, lz/m
        nu=nx*ux+ny*uy+nz*uz
        if nu==0: return 8192,8192,8192

        dx, dy, dz = x0-x, y0-y, z0-z
        nd=nx*dx+ny*dy+nz*dz
        sp=-nd/nu
        px, py, pz = x0+sp*ux, y0+sp*uy, z0+sp*uz
        return px,py,pz

    def view(self,width=None,height=None):
        if width is None: width,height=self.w,self.h
        else: self.w,self.h=width,height
        glViewport(0, 0, width, height)
        glGetIntegerv(GL_VIEWPORT, self.mat_vis)
        print "Viewport "+str(width)+"x"+str(height)
        glMatrixMode(GL_PROJECTION)
        glOrtho(0, self.w, 0, self.h, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glGetDoublev(GL_PROJECTION_MATRIX, self.mat_pro)

    def key(self, symbol, modifiers):
        if symbol==key.F1:
            self.view()
            print "Projection: Pyglet default"
        elif symbol==key.F4:
            print "Toggle Color Masks"
            scene.mask=not scene.mask

        elif symbol==key.RETURN:
            scene.load(LAYER)
        elif symbol==key.ESCAPE:
            sys.exit()

        else: print "KEY "+key.symbol_string(symbol)

    def click(self, x, y, button, modifiers):
        print "Mouse click at",str((x,y))
        scene.click(x,y)

    def drag(self, x, y, dx, dy, button, modifiers):
        if scene.selected is not None:
            if button==1: scene.selected.move(dx,dy,0)
            elif button==5: scene.selected.move(0,0,-dy)
            return
        if button==1:
            self.x-=dx*2
            self.y-=dy*2
        elif button==2:
            self.x-=dx*2
            self.z-=dy*2
        elif button==4:
            self.ry+=dx/4.
            self.rx-=dy/4.

    def apply(self):
        glLoadIdentity()

#---------------------------------
def opengl_init():
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDepthFunc(GL_LEQUAL)

print "Alpha Selection"
print "---------------------------------"
print "Camera            -> Drag LMB,CMB,RMB"
print ""
print "Select layer      -> Click LMB"
print "Move layer XY     -> Drag LMB"
print "Move layer Z      -> Drag LMB+RMB"
print "Add star          -> RETURN"
print ""

scene=Layers()
cam=Camera()
win = window.Window(resizable=True)
win.on_resize=cam.view
win.on_key_press=cam.key
win.on_mouse_drag=cam.drag
win.on_mouse_press=cam.click
opengl_init()

for n in range (0,3):
    layer=scene.load(LAYER)
    layer.x=160+n*160
    layer.y=240
    layer.z=n-1

while not win.has_exit:
    win.dispatch_events()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    cam.apply()
    scene.draw()
    win.flip() 
