@echo off
call "D:\python projects 3.8\UAVpath\uav_find_path\o4w_env.bat"
call "D:\python projects 3.8\UAVpath\uav_find_path\qt5_env.bat"
call "D:\python projects 3.8\UAVpath\uav_find_path\py3_env.bat"

@echo on
pyrcc5 -o resources.py resources.qrc