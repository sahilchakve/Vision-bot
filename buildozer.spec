[app]
title = Vision Bot
package.name = visionbot
package.domain = org.sahil
source.dir = .
source.include_exts = py,json
version = 1.0
requirements = python3,kivy,requests,typing_extensions,instagrapi,pydantic,pillow,pycryptodomex
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 33
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True
log_level = 2

[buildozer]
log_level = 2
warn_on_root = 1
