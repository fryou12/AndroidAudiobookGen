[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

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
    pyjnius

# Environment variables
os.environ['JAVA_HOME'] = '/Users/thomasfry/Library/Java/JavaVirtualMachines/jbr-17.0.12/Contents/Home'

# Python specific
python.version = 3.8

# Android specific
android.permissions = INTERNET
android.minapi = 21
android.ndk = 25b
android.sdk = 31
android.archs = arm64-v8a
android.skip_update = False
android.enable_androidx = True
android.entrypoint = org.kivy.android.PythonActivity
android.apptheme = @android:style/Theme.NoTitleBar
android.copy_libs = 1
android.gradle_dependencies = org.tensorflow:tensorflow-lite:+,androidx.webkit:webkit:1.4.0
android.add_gradle_repositories = mavenCentral()

# Python-for-Android options
p4a.branch = develop
p4a.bootstrap = sdl2
p4a.local_recipes = ./recipes
p4a.no_patches = True

# Build options
android.logcat_filters = *:S python:D
android.meta_data = android.app.lib_name=epubtoaudio
android.wakelock = True

# Orientation
orientation = portrait
fullscreen = 0
