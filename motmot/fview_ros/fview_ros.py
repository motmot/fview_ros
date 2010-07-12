from __future__ import with_statement, division

import pkg_resources
import warnings, threading
import enthought.traits.api as traits

import motmot.fview.traited_plugin as traited_plugin
import motmot.fview_ext_trig.ttrigger as ttrigger
import numpy as np

from enthought.traits.ui.api import View, Item, Group

try:
    import roslib
    have_ROS = True
except ImportError, err:
    have_ROS = False

if have_ROS:
    roslib.load_manifest('sensor_msgs')
    from sensor_msgs.msg import Image
    import rospy
    import rospy.core

class FviewROS(traited_plugin.HasTraits_FViewPlugin):
    plugin_name = 'FView ROS'
    publisher = traits.Any(transient=True)
    encoding = traits.String(transient=True)
    topic_prefix = traits.String

    traits_view = View(Group(Item('topic_prefix'),
                             Item('encoding',style='readonly')))

    def __init__(self,*args,**kwargs):
        super( FviewROS, self).__init__(*args,**kwargs)
        if have_ROS:
            rospy.init_node('fview_ros',
                            anonymous=True, # allow multiple instances to run
                            disable_signals=True, # let WX intercept them
                            )
        self.publisher_lock = threading.Lock()
        self.publisher = None
        self._topic_prefix_changed()

    def _topic_prefix_changed(self):
        with self.publisher_lock:
            # unregister old publisher
            if self.publisher is not None:
                self.publisher.unregister()

            # register a new publisher
            if have_ROS:
                 self.publisher = rospy.Publisher('%s/image_raw'%self.topic_prefix,
                                                  Image,
                                                  tcp_nodelay=True,
                                                  )

    def camera_starting_notification(self,cam_id,
                                     pixel_format=None,
                                     max_width=None,
                                     max_height=None):
        if pixel_format == 'MONO8':
            self.encoding = 'mono8'
        elif pixel_format in ('RAW8:RGGB','MONO8:RGGB'):
            self.encoding = 'bayer_rggb8'
        elif pixel_format in ('RAW8:BGGR','MONO8:BGGR'):
            self.encoding = 'bayer_bggr8'
        elif pixel_format in ('RAW8:GBRG','MONO8:GBRG'):
            self.encoding = 'bayer_gbrg8'
        elif pixel_format in ('RAW8:GRBG','MONO8:GRBG'):
            self.encoding = 'bayer_grbg8'
        else:
            raise ValueError('unknown pixel format "%s"'%pixel_format)

    def process_frame(self,cam_id,buf,buf_offset,timestamp,framenumber):
        if have_ROS:
            msg = Image()
            msg.header.seq=framenumber
            msg.header.stamp=rospy.Time.from_sec(timestamp)
            msg.header.frame_id = "0"

            npbuf = np.array(buf)
            (height,width) = npbuf.shape

            msg.height = height
            msg.width = width
            msg.encoding = self.encoding
            msg.step = width
            msg.data = npbuf.tostring() # let numpy convert to string

            with self.publisher_lock:
                self.publisher.publish(msg)
        return [],[]
