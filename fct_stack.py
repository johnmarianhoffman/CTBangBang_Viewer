import sys

import numpy as np

class image_stack:
    stack=None
    curr_image=0
    n_images=None
    width=512
    height=512

    def __init__(self,filepath):
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
        
