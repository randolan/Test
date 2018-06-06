# -*- coding: utf-8 -*-
import os
import re
import sys
import json
import time
import fnmatch
import pathlib
import shutil
import subprocess
import getpass
import tempfile
import argparse

tempdir=tempfile.gettempdir()
arduino_path ='/usr/local/share/arduino'
arduino_packages = '/home/travis/.arduino15/packages'
build_output_dir= tempdir+'/temp_arduinoBuilderOutput'
output_dir=' /home/travis/Arduino/Tempor/arduinoBuilderOutput'

#Common path
arduino_builder = os.path.join(arduino_path, 'arduino-builder')
hardware_path = os.path.join(arduino_path, "hardware")
libsketches_path_default = os.path.join(arduino_path, "libraries")
tools_path = os.path.join(arduino_path,"tools-builder")

#Ouput directory path
bin_dir = os.path.join(output_dir,"binaries")
std_dir = os.path.join(output_dir,"std_folder")

#Counter
nb_build_total = 0
nb_build_passed = 0
nb_build_failed = 0

def createFolder(folder):
    try :
        if not os.path.exists(folder):
            os.makedirs(folder)
    except OSError:
        print ('Error: Creating directory. ' +  folder)

#Set up specific options to customise arduino builder command
def set_varOpt(board):
    var_type_default=board[0]
    var_num_default=board[1]
    upload_method_default="STLink"
    serial_mode_default="generic"
    usb_mode_default="none"
    option_default="osstd"
    variantOption = "STM32:stm32:{var_type}:pnum={var_num},upload_method={upload_method},xserial={serial_mode},usb={usb_mode},opt={option}".format(var_type=var_type_default,var_num=var_num_default,upload_method=upload_method_default,serial_mode=serial_mode_default,usb_mode=usb_mode_default,option=option_default)
    return variantOption

#Configure arduino builder command
def build(variant,sketch_path):
    cmd = []
    cmd.append(arduino_builder)
    cmd.append("-hardware")
    cmd.append(hardware_path)
    cmd.append("-hardware")
    cmd.append(arduino_packages)
    cmd.append("-tools")
    cmd.append(tools_path)
    cmd.append("-tools")
    cmd.append(arduino_packages)
    cmd.append("-libraries")
    cmd.append(libsketches_path_default)
    cmd.append("-fqbn")
    cmd.append(variant)
    cmd.append("-ide-version=10805")
    cmd.append("-build-path")
    cmd.append(build_output_dir)
    cmd.append("-verbose")
    cmd.append(sketch_path)
    return cmd

#Run arduino builder command
def run_command(cmd,board_name,sketch_name):
    boardstd = os.path.join(std_dir,board_name) #Board specific folder that contain stdout and stderr files
    createFolder(boardstd)
    timer=time.strftime("%Y-%m-%d-%Hh%M")
    stddout_name=timer+'_'+sketch_name+'_stdout.txt'
    stdderr_name=timer+'_'+sketch_name+'_stderr.txt'
    with open(os.path.join(boardstd,stddout_name),"w") as stdout, open(os.path.join(boardstd,stdderr_name),"w") as stderr:
        res = subprocess.Popen(cmd, stdout=stdout, stderr=stderr)
        print("Building in progress ...")
        res.wait()
        return res.returncode

#Find all .ino files
def find_inos(args):
    inoList = []
    if args.ino:
        assert os.path.exists(args.ino[0]), 'Ino path does not exist'
        inoList=args.ino
    else:
        for root, dirs, files in os.walk(arduino_path):
            for file in files:
                if file.endswith(".ino"):
                    if args.sketches:
                        sketch2find = args.sketches[len(args.sketches)-1]
                        regex=".*("+sketch2find+").*"
                        x=re.match(regex,os.path.join(root, file),re.IGNORECASE)
                        if x:
                            inoList.append(os.path.join(root,x.group(0)))
                    else:
                        inoList.append(os.path.join(root, file))
    return sorted(inoList)

#Return a list of all board types and names using the board.txt file
def find_board(args):
    boardlist=[]
    for path in [arduino_packages, hardware_path]:
        for root, dirs, files in os.walk(path, followlinks=True):
            for file in files:
                if fnmatch.fnmatch(file, 'boards.txt'):
                    if os.path.getsize(os.path.join(root,file)) != 0 :
                        with open(os.path.join(root,file),'r') as f:
                            regex="(.+)\.menu\.pnum\.([^\.]+)="
                            for line in f.readlines():
                                x=re.match(regex,line)
                                if x:
                                    if args.board:
                                        boardpattern = args.board[len(args.board)-1]
                                        reg=".*("+boardpattern+").*"
                                        y=re.match(reg,x.group(0),re.IGNORECASE)
                                        if y:
                                            board_type=x.group(1)
                                            board_name=x.group(2)
                                            board=(board_type,board_name)
                                            boardlist.append(board)
                                    else:
                                        board_type=x.group(1)
                                        board_name=x.group(2)
                                        board=(board_type,board_name)
                                        boardlist.append(board)
    return sorted(boardlist)

#Check the status
def check_status(status,board_name,sketch_name):
    global nb_build_passed
    global nb_build_failed
    global nb_build_total
    nb_build_total+=1
    if status==0:
        print('SUCESS')
        bin_copy(board_name,sketch_name)
        nb_build_passed += 1
    elif status==1:
        print('FAILED')
        nb_build_failed +=1
    else:
        print("Error ! Check the run_command exit status ! Return code = ",status)

#Create a "bin" directory for each board and copy all binary files from the builder output directory into it
def bin_copy(board_name,sketch_name):
    board_bin=os.path.join(bin_dir,board_name)
    createFolder(board_bin)
    binfile=os.path.join(build_output_dir,sketch_name+".bin")
    try :
        shutil.copy(binfile,os.path.abspath(board_bin))
    except OSError as e:
        print("Impossible to copy the binary from the arduino builder output: ",e.strerror)
        raise
        
#Automatic run
def run_auto(sketch_list,board_list):
    current_sketch=0
    for files in sketch_list:
        boardOk = []
        boardKo = []
        current_board=0
        current_sketch+=1
        sketch_name=os.path.basename(files)
        print("\nRUNNING : {} ({}/{}) ".format(sketch_name,current_sketch,len(sketch_list)))
        print("Sketch path : " +files)
        for board in board_list:
            board_name=board[1]
            current_board+=1
            print("\nBoard ({}/{}) : {}".format(current_board,len(board_list),board_name))
            variant = set_varOpt(board)
            command = build(variant,files)
            status = run_command(command,board_name,sketch_name)
            if status == 0:
                boardOk.append(board)
            if status == 1:
                boardKo.append(board)
            check_status(status,board_name,sketch_name)
    print("\n****************** PROCESSING COMPLETED ******************")
    print("PASSED = {}/{}".format(nb_build_passed,nb_build_total))
    print("FAILED = {}/{}".format(nb_build_failed,nb_build_total))
    print("Logs are available at", output_dir)

#Create output folders
createFolder(build_output_dir)
createFolder(output_dir)
createFolder(bin_dir)
createFolder(std_dir)

assert os.path.exists(arduino_path), 'Path does not exist: %s . Please set this path in the json config file' %arduino_path
assert os.path.exists(arduino_packages), 'Path does not exist: %s . Please set this path in the json config file' %arduino_packages
assert os.path.exists(build_output_dir), 'Path does not exist: %s . Please set this path in the json config file' %build_output_dir
assert os.path.exists(output_dir), 'Path does not exist: %s . Please set this path in the json config file' %output_dir

#Parser
parser = argparse.ArgumentParser(description="Automatic build script")
parser.add_argument('-a', '--all', help='-a : automatic build - build all sketches for all board', action='store_true')
parser.add_argument("-b", "--board", help="-b <board pattern>: pattern to find one or more boards to build",action="append",default=[])
parser.add_argument("-i", "--ino", help="-i <ino filepath>: single ino file to build",action="append",default=[])
parser.add_argument("-s", "--sketches", help=" -s <sketch pattern>: pattern to find one or more sketch to build",action="append",default=[])
args = parser.parse_args()

#Run builder
sketch_default=arduino_path+r'/examples/01.Basics/Blink/Blink.ino'
sketches = find_inos(args)
variants = find_board(args)

if len(sys.argv)<2 : #Si aucun args
    sketches = [sketch_default]
    run_auto(sketches,variants)
else:
    run_auto(sketches,variants)
