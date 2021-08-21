#!/bin/bash

sudo apt-get upgrade
sudo apt-get install libgles2-mesa libgles2-mesa-dev xorg-dev
sudo apt-get install python3 python3-pip chromium-chromedriver xvfb libopenjp2-7 openexr libavcodec-dev ffmpeg liblapack-dev libatlas-base-dev mpv -y

pip3 install pyvirtualdisplay selenium 2captcha-python pillow opencv-python filelock

echo "Please follow this guide to get hardware acceleration: https://lemariva.com/blog/2020/08/raspberry-pi-4-video-acceleration-decode-chromium"

mkdir saved_searches

git submodule init
git submodule update