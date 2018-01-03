#!/usr/bin/env python
import os
import sys
import time
import zlib

import numpy as np
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg

from argparse import ArgumentParser

def read_hr2(filepath):

    hr2_dict={}

    with open(filepath,'rb') as f:

        # Ensure we have an HR2 file
        magic_number=f.read(3)
        if magic_number!=b"HR2":
            #print("File is not an hr2 file. Exiting")
            sys.exit(1)

        # Read the file into memory
        while True:
            # Get tag
            chunk_tag_size=int.from_bytes(f.read(1),byteorder='little')            
            chunk_tag=f.read(chunk_tag_size)
            #print(str(chunk_tag,'utf-8'))

            # Get value
            # Handle all tags *except* image data (size=uint16)
            if chunk_tag!=b'ImageData':
                chunk_val_size=int.from_bytes(f.read(2),byteorder='little')
                chunk_val=f.read(chunk_val_size)
                hr2_dict[str(chunk_tag,'utf-8')]=str(chunk_val,'utf-8')
            # Handle image data tag (size=uint32)
            else:
                chunk_val_size=int.from_bytes(f.read(4),byteorder='little')
                header_end_byte=f.tell()
                chunk_val=f.read(chunk_val_size)
                hr2_dict[str(chunk_tag,'utf-8')]=chunk_val
                break

        # Decompress the image data using zlib
        if hr2_dict['Compression']=="ZLib":
            hr2_dict['ImageData']=zlib.decompress(hr2_dict['ImageData'])

        # Parse image data byte string into numpy array
        hr2_dict['Size']=[int(x) for x in hr2_dict['Size'].split(' ')]
        hr2_dict['ImageData']=np.fromstring(hr2_dict['ImageData'],dtype='int16')
        hr2_dict['ImageData']=hr2_dict['ImageData'].reshape(hr2_dict['Size'][2],hr2_dict['Size'][1],hr2_dict['Size'][0])

        # Read the raw header data into our dictionary (will be used to save a copy for easy-rewrapping)
        with open(filepath,'rb') as f:
            hr2_dict['HeaderData']=f.read(header_end_byte)

        #print(hr2_dict['HeaderData'])
            
        return hr2_dict
    pass

class image_stack:
    stack=None
    curr_image=0
    n_images=None
    width=512
    height=512
    datatype='float'

    def __init__(self,filepath,width,height,offset,datatype):
        print('offset: ' + str(offset));
        print('width: ' +  str(width ));
        print('height: ' + str(height));

        self.width=width;
        self.height=height;
        self.datatype=datatype

        # Parse the file extension to see what we have
        # Load the image stack based on what we find
        # Offers support for IMG and HR2 *only*
        fname,fext = os.path.splitext(filepath)

        if fext.lower()=='.img':            
            with open(filepath,'r') as f:
                f.seek(offset,os.SEEK_SET);
                if self.datatype=='float':
                    self.stack=np.fromfile(f,'float32')
                else:
                    self.stack=np.fromfile(f,'float64')
                
            print(self.stack.size)
            self.stack=self.stack.reshape(self.stack.size/(self.width*self.height),self.width,self.height);
            self.stack=1000*(self.stack-0.01923)/(0.01923)
            stack_size=self.stack.shape
            self.n_images=stack_size[0];
        elif fext.lower()=='.hr2':
            hr2_dict=read_hr2(filepath)
            self.stack=hr2_dict['ImageData']
            stack_size=self.stack.shape
            self.n_images=stack_size[0];
        else:
            sys.exit('Unrecognized filetype: {}'.format(fext))
        
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
    
    def __init__(self,app,stack):
        super(viewer,self).__init__()
        self.app=app
        self.stack=stack;
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
    parser.add_argument('datatype', nargs='?', default='float',  help='Height of the image stack being read'); #required=False,
    parser.add_argument('offset', nargs='?', default=0,  help='Height of the image stack being read'); #required=False,
    args=parser.parse_args()

    filepath=args.filepath;
    width= int(args.width);
    height=int(args.height);
    datatype=args.datatype;
    offset=int(args.offset);
    
    v=viewer(app,image_stack(filepath,width,height,offset,datatype))

    #if len(sys.argv)==2:
    #    v=viewer(app,filepath,width,height)
    #else:
    #    v=viewer(app,sys.argv[1],sys.argv[2],sys.argv[3]);
    sys.exit(app.exec_())

if __name__=="__main__":
    main();
