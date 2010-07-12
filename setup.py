from setuptools import setup, find_packages, Extension
import sys,os

setup(name='motmot.fview_ros',
      description='Robot Operating System (ROS) support for FView',
      version='0.0.1',
      packages = ['motmot.fview_ros',],
      author='Andrew Straw',
      author_email='strawman@astraw.com',
      url='http://code.astraw.com/projects/motmot',
      entry_points = {
    'motmot.fview.plugins':'fview_ros = motmot.fview_ros.fview_ros:FviewROS',
    },
      )
