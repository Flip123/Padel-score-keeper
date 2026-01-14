[app]
title = Padel Score Keeper
package.name = padelscorekeeper
package.domain = org.flip123
version = 0.1.0

source.dir = .
source.include_exts = py,kv,txt

entrypoint = main.py

requirements = python3,kivy

android.permissions = WAKE_LOCK

android.api = 33
android.minapi = 26
android.ndk_api = 26

orientation = landscape
fullscreen = 1

log_level = 2

[buildozer]
log_level = 2
warn_on_root = 1
