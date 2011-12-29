from __future__ import with_statement, division

import pkg_resources
import warnings, threading
try:
    import enthought.traits.api as traits
    from enthought.traits.ui.api import View, Item, Group
except ImportError:
    # traits 4
    import traits.api as traits
    from traitsui.api import View, Item, Group

import motmot.fview.traited_plugin as traited_plugin
import numpy as np

try:
    import roslib
    have_ROS = True
except ImportError, err:
    have_ROS = False

if have_ROS:
    roslib.load_manifest('sensor_msgs')
    from sensor_msgs.msg import Image, CameraInfo
    import rospy
    import rospy.core

class FviewROS(traited_plugin.HasTraits_FViewPlugin):
    plugin_name = 'FView ROS'
    publisher = traits.Any(transient=True)
    publisher_cam_info = traits.Any(transient=True)
    encoding = traits.String(transient=True)
    topic_prefix = traits.String

    traits_view = View(Group(Item('topic_prefix'),
                             Item('encoding',style='readonly')))

    def __init__(self,*args,**kwargs):
        super( FviewROS, self).__init__(*args,**kwargs)
        if have_ROS:
            rospy.init_node('fview', # common name across all plugins so multiple calls to init_node() don't fail
                            anonymous=True, # allow multiple instances to run
                            disable_signals=True, # let WX intercept them
                            )
        self.publisher_lock = threading.Lock()
        self.publisher = None
        self.publisher_cam_info = None
        self._topic_prefix_changed()

    def _topic_prefix_changed(self):
        with self.publisher_lock:
            # unregister old publisher
            if self.publisher is not None:
                self.publisher.unregister()
            if self.publisher_cam_info is not None:
                self.publisher_cam_info.unregister()

            # register a new publisher
            if have_ROS:
                 self.publisher = rospy.Publisher('%s/image_raw'%self.topic_prefix,
                                                  Image,
                                                  tcp_nodelay=True,
                                                  )
                 self.publisher_cam_info = rospy.Publisher('%s/camera_info'%self.topic_prefix,
                                                           CameraInfo,
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

            cam_info = CameraInfo()
            cam_info.header.stamp = msg.header.stamp
            cam_info.header.seq = msg.header.seq
            cam_info.header.frame_id = msg.header.frame_id
            cam_info.width = width
            cam_info.height = height

            with self.publisher_lock:
                self.publisher.publish(msg)
                self.publisher_cam_info.publish(cam_info)
        return [],[]
