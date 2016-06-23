#!/usr/bin/env python

import sys
import time

import numpy as np
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg

from argparse import ArgumentParser

class image_stack:
    stack=None
    curr_image=0
    n_images=None
    width=512
    height=512

    def __init__(self,filepath,width,height):

        self.stack=np.fromfile(filepath,'float32');
        self.stack=self.stack.reshape(self.stack.size/(self.width*self.height),self.width,self.height);
        self.stack=1000*(self.stack-0.01923)/(0.01923)
        stack_size=self.stack.shape
        self.n_images=stack_size[0];

    def __getitem__(self,key):
        if (key in range(0,self.n_images)):
            return self.stack[key,:,:]
        else:
            raise IndexError

    def next_image(self):
        self.curr_image=min(self.curr_image+1,self.n_images-1);

    def prev_image(self):
        self.curr_image=max(self.curr_image-1,0);

class viewer(pg.GraphicsLayoutWidget):
    #objects
    app=None;
    stack=None;
    plot_window=None;
    img_obj=None;
    hist_obj=None;

    window=1000;
    level=0;
    
    is_windowing=False;
    is_playing=False;
    
    def __init__(self,app,filepath,width,height):
        super(viewer,self).__init__()
        self.app=app
        self.stack=image_stack(filepath,width,height);
        self.initUI()

    def initUI(self):
        self.setWindowTitle('CTBB Image Viewer');
        self.plot_window = self.addPlot()
        
        self.plot_window.hideAxis('left');
        self.plot_window.hideAxis('bottom');
        self.plot_window.invertY();
        self.plot_window.invertX();

        self.img_obj = pg.ImageItem()
        self.img_obj.aspectLocked=True;
        self.plot_window.addItem(self.img_obj)

        self.img_obj.setImage(self.stack[0],levels=(self.level-self.window/2,self.level+self.window/2))
        
        self.resize(512, 512)
        self.show()

    def update_image(self):
	self.img_obj.setImage(self.stack[self.stack.curr_image],levels=(self.level-self.window/2,self.level+self.window/2))
	self.app.processEvents()

    def play(self):
        while self.is_playing and self.stack.curr_image<=self.stack.n_images-1:
            self.stack.next_image();
            time.sleep(0.041);
            self.update_image();

    def rewind(self):
        while self.is_playing and self.stack.curr_image>=0:
            self.stack.prev_image();
            time.sleep(0.041);
            self.update_image();

    def keyPressEvent(self,e):
        if e.matches(QtGui.QKeySequence.Close):
            sys.exit()
        elif (e.key()==QtCore.Qt.Key_Right) | (e.key()==QtCore.Qt.Key_F):
            self.stack.next_image()
        elif (e.key()==QtCore.Qt.Key_Left) | (e.key()==QtCore.Qt.Key_B):
            self.stack.prev_image()
        elif e.key()==QtCore.Qt.Key_Space and e.modifiers()==QtCore.Qt.NoModifier:
            self.is_playing=not self.is_playing
            self.play();
        elif e.key()==QtCore.Qt.Key_Space and e.modifiers()!=QtCore.Qt.NoModifier:
            self.is_playing=not self.is_playing
            self.rewind();            
        elif e.key()==QtCore.Qt.Key_W:
            self.set_wl()
        else:
            pass

        self.update_image();

    def set_wl(self):        
        self.is_windowing=not self.is_windowing;

        if self.is_windowing:
            self.hist_obj = pg.HistogramLUTItem()
            self.hist_obj.setImageItem(self.img_obj)
            self.addItem(self.hist_obj);
        else:
            self.window=self.img_obj.levels[1]-self.img_obj.levels[0]
            self.level=(self.img_obj.levels[1]+self.img_obj.levels[0])/2
            self.removeItem(self.hist_obj);

def main():
    app=QtGui.QApplication(sys.argv)

    parser = ArgumentParser(description="")
    parser.add_argument('filepath', help='Path to float binary to be read');
    parser.add_argument('width' , nargs='?', default=512,  help='Width of the image stack being read');  #required=False,
    parser.add_argument('height', nargs='?', default=512,  help='Height of the image stack being read'); #required=False,
    args=parser.parse_args()

    filepath=args.filepath;
    width=args.width;
    height=args.height;

    v=viewer(app,filepath,width,height)

    #if len(sys.argv)==2:
    #    v=viewer(app,filepath,width,height)
    #else:
    #    v=viewer(app,sys.argv[1],sys.argv[2],sys.argv[3]);
    sys.exit(app.exec_())

if __name__=="__main__":
    main();
        
