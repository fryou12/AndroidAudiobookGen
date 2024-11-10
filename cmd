docker build -t android-dev . 
docker run -it --name android-dev-container -v $(pwd):/home/developer/app android-dev
docker exec -it android-dev-container /bin/bash


brew install autoconf automake libtool pkg-config
brew link libtool
brew install openssl
brew install sdl2 sdl2_image sdl2_ttf sdl2_mixer
brew install pkg-config sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer

pip install --user buildozer
pip install --user appdirs colorama jinja2 sh build toml packaging setuptools
rm -rf .buildozer
/Users/thomasfry/.pyenv/versions/3.8.18/bin/python3.8 -m venv TTSenv
source TTSenv/bin/activate
pip install -U pip
pip install -U buildozer
pip install -U Cython==0.29.33
time ( yes | buildozer android clean ) > logC.txt
time ( yes | buildozer -v android debug ) >> logC.txt    # rappel : > pour écraser le fichier et >> pour ajouter au fichier  

source ~/.zshrc
rm -rf TTSenv
rm -rf .buildozer
rm -rf bin
python -m venv TTSenv
source TTSenv
python -m pip install --upgrade pip
python -m pip install --upgrade setuptools wheel
python -m pip install Cython==0.29.33
python -m pip install buildozer
mkdir -p .buildozer/android/platform
cd .buildozer/android/platform
git clone -b develop https://github.com/kivy/python-for-android.git
cd ../../..
time ( yes | buildozer android clean ) > logC.txt
time ( yes | buildozer -v android debug ) >> logC.txt
yes | (buildozer android clean 2>&1) | tee logC.txt
yes | (buildozer -v android debug 2>&1) | tee -a logC.txt

rm -rf .buildozer
rm -rf bin
rm -rf TTSenv
mkdir -p .buildozer/android/platform
cd .buildozer/android/platform
git clone -b develop https://github.com/kivy/python-for-android.git
cd python-for-android
python setup.py install
cd ../../../..
pyenv global 3.8.18
python3.8 -m venv TTSenv
source TTSenv/bin/activate
python -m pip install --upgrade pip
python -m pip install --upgrade setuptools wheel
python -m pip install Cython==0.29.33
python -m pip install buildozer
python --version
cython --version  
buildozer --version
time ( yes | buildozer android clean ) &> logC.txt
time ( yes | buildozer -v android debug ) &>> logC.txt
    
    
    
    #Important pour developper sur un terminal particulier
adb shell getprop ro.product.cpu.abi
adb shell getprop ro.product.cpu.abilist
adb shell getprop | grep -E "ro.hardware.egl|ro.hardware.vulkan|ro.opengles"
adb shell getprop | grep -E "ro.product|ro.build|ro.hardware"
adb shell getprop | grep -i mt6789
adb shell getprop | grep -i mali
adb shell getprop | grep -i mediatek
adb shell dumpsys audio
adb shell dumpsys SurfaceFlinger | grep GLES
adb shell dumpsys media.audio_flinger
    adb shell dumpsys media.audio_policy
adb shell dumpsys SurfaceFlinger | grep -i mali
adb shell ls -l /vendor/lib64/hw/
adb shell ls -l /system/lib64/
adb shell ls -l /system/lib64/libOpenSLES.so
adb shell ls -l /vendor/lib64/hw/mt6789/
adb shell ls -l /vendor/lib64/egl/
        adb shell ls -l /vendor/lib64/hw/gralloc.*
adb shell cat /proc/cpuinfo
adb shell cat /proc/meminfo
adb shell cat /sys/devices/soc0/soc_id
adb shell cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_available_frequencies
adb shell cat /sys/class/misc/mali*/device/gpuinfo

#IA a voulu savoir
cat .buildozer/android/platform/build-arm64-v8a/build/bootstrap_builds/sdl2/jni/SDL2-*/include/SDL_android.h
ls -R .buildozer/android/platform/build-arm64-v8a/build/bootstrap_builds/sdl2/jni/SDL2-*/src/core/android/
ls -l .buildozer/android/platform/build-arm64-v8a/build/bootstrap_builds/sdl2/jni/SDL2-*/include/SDL_config*.h
cat .buildozer/android/platform/build-arm64-v8a/build/bootstrap_builds/sdl2/jni/SDL2-*/include/SDL_internal.h

#important pour savoir ce que l'on a a disposition en local comme sdk
sdkmanager --list | grep "build-tools"
git clone https://github.com/libsdl-org/SDL.git
cd SDL/src/core/android/SDL_android.c



brew uninstall python@3.10
brew unlink python@3.10
rm -rf /opt/homebrew/opt/python@3.10
rm -rf /opt/homebrew/Cellar/python@3.10
which python3.10

deactivate
rm -rf TTSenv
rm -rf .buildozer
rm -rf bin
pyenv global 3.8.18
/Users/thomasfry/.pyenv/versions/3.8.18/bin/python3.8 -m venv TTSenv
source TTSenv/bin/activate
/Users/thomasfry/.pyenv/versions/3.8.18/bin/python3.8 -m pip install --upgrade pip
/Users/thomasfry/.pyenv/versions/3.8.18/bin/python3.8 -m pip install --upgrade setuptools wheel
/Users/thomasfry/.pyenv/versions/3.8.18/bin/python3.8 -m pip install Cython==0.29.33
/Users/thomasfry/.pyenv/versions/3.8.18/bin/python3.8 -m pip install buildozer
python -m pip install --upgrade pip
python -m pip install --upgrade setuptools wheel
python -m pip install Cython==0.29.33
python -m pip install buildozer
buildozer --version
which python
python --version

time ( yes | /Users/thomasfry/.pyenv/versions/3.8.18/bin/python3.8 -m buildozer android clean ) > logC.txt
time ( yes | /Users/thomasfry/.pyenv/versions/3.8.18/bin/python3.8 -m buildozer -v android debug ) >> logC.txt

time ( yes | buildozer android clean ) > logC.txt
time ( yes | buildozer -v android debug ) >> logC.txt

# Désactiver l'environnement virtuel
deactivate
rm -rf TTSenv
rm -rf .buildozer
rm -rf bin
pyenv global 3.8.18
python3.8 -m venv TTSenv
source TTSenv/bin/activate
python -m pip install --ignore-installed --no-cache-dir Cython==0.29.33
python -c "import Cython; print(Cython.__version__)"
mkdir -p .buildozer/android/platform/build-arm64-v8a/build/python-installs/epubtoaudio/arm64-v8a/
python -m pip install Cython==0.29.33 --target=.buildozer/android/platform/build-arm64-v8a/build/python-installs/epubtoaudio/arm64-v8a/
python -m pip install --upgrade pip
python -m pip install --upgrade setuptools wheel
mkdir -p .buildozer/android/platform
cd .buildozer/android/platform
git clone -b develop https://github.com/kivy/python-for-android.git
cd python-for-android
python setup.py install
cd ../../../..
python -m pip install buildozer
python -c "import Cython; print(Cython.__version__)"
$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager "build-tools;31.0.0"
yes | (buildozer android clean 2>&1) | tee logC.txt
yes | (buildozer -v android debug 2>&1) | tee -a logC.txt



deactivate
rm -rf TTSenv
rm -rf .buildozer
rm -rf bin
pyenv global 3.8.18
python3.8 -m venv TTSenv
source TTSenv/bin/activate
python -m pip install --upgrade pip
python -m pip install --upgrade setuptools wheel
python -m pip install Cython==0.29.33
mkdir -p .buildozer/android/platform/build-arm64-v8a/build/python-installs/epubtoaudio/arm64-v8a/
python -m pip install Cython==0.29.33 --target=.buildozer/android/platform/build-arm64-v8a/build/python-installs/epubtoaudio/arm64-v8a/
python -m pip install buildozer
python -c "import Cython; print(Cython.__version__)"
time ( yes | buildozer android clean ) &> logC.txt
time ( yes | buildozer -v android debug ) &>> logC.txt