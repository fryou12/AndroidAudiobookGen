[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 0

# (str) Path to build artifact storage, absolute or relative to spec file
build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .aab, .ipa) storage
bin_dir = ./bin

[app]
# (str) Title of your application
title = ePub to Audio

# (str) Package name
package.name = epubtoaudio

# (str) Package domain (needed for android/ios packaging)
package.domain = org.epubtoaudio

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,html,css,js

# (str) Application version
version = 0.1.10

# (list) Application requirements
requirements = python3,\
    kivy==2.2.1,\
    pyjnius,\
    pillow==10.0.0,\
    beautifulsoup4==4.12.2,\
    PyPDF2==3.0.1,\
    pdfminer.six==20221105,\
    requests==2.31.0

# Python specific
python.version = 3.8

# Android specific
android.permissions = INTERNET
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a

# Build paths
android.sdk_path = /home/developer/.buildozer/android/platform/android-sdk
android.ndk_path = /home/developer/.buildozer/android/platform/android-ndk-r25b
android.ant_path = /home/developer/.buildozer/android/platform/apache-ant-1.9.4

# Python-for-android paths
p4a.source_dir = /home/developer/.buildozer/android/platform/python-for-android
p4a.local_recipes = %(source.dir)s/recipes
p4a.hook = %(source.dir)s/p4a_hooks.py
p4a.bootstrap = sdl2

# Debug
android.logcat_filters = *:S python:D
p4a.verbose = 2

# Build options
android.copy_libs = 1
android.gradle_dependencies = org.tensorflow:tensorflow-lite:+
android.add_gradle_repositories = mavenCentral()

# Orientation
orientation = portrait
fullscreen = 0
