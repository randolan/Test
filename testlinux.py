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
build_id = time.strftime("_%Y-%m-%d_%H-%M-%S")

arduino_path ='/usr/local/share/arduino'
arduino_packages = '/home/travis/.arduino15/packages'
build_output_dir= tempdir+'/temp_arduinoBuilderOutput'
root_output_dir=' /home/travis/Arduino/Tempor/arduinoBuilderOutput'
sketchbook_path = '/home/travis/Arduino'

assert os.path.exists(arduino_path), (
    "Path does not exist: %s . Please set this path in the json config file"
    % arduino_path
)
assert os.path.exists(arduino_packages), (
    "Path does not exist: %s . Please set this path in the json config file"
    % arduino_packages
)

assert os.path.exists(sketchbook_path), (
    "Path does not exist: %s . Please set this path in the json config file"
    % sketchbook_path
)

#Common path
arduino_builder = os.path.join(arduino_path, 'arduino-builder')
hardware_path = os.path.join(arduino_path, "hardware")
lib_path_default = os.path.join(arduino_path, "libraries")
additional_lib_path = os.path.join(sketchbook_path, "libraries")
tools_path = os.path.join(arduino_path,"tools-builder")
output_dir = os.path.join(root_output_dir, "build" + build_id)

#Ouput directory path
bin_dir = os.path.join(output_dir,"binaries")
std_dir = os.path.join(output_dir,"std_folder")

# Default
sketch_default = os.path.join(
    arduino_path, "examples", "01.Basics", "Blink", "Blink.ino"
)

# List
sketch_list = []
board_list = []

# Counter
nb_build_total = 0
nb_build_passed = 0
nb_build_failed = 0

# Create a folder if not exists
def createFolder(folder):
    try :
        if not os.path.exists(folder):
            os.makedirs(folder)
    except OSError:
        print ('Error: Creating directory. ' +  folder)

# Delete targeted folder recursively
def deleteFolder(folder):
    if os.path.isdir(folder):
        shutil.rmtree(folder, ignore_errors=True)

# Manage sketches list
def manage_inos():
    global sketch_list
    # Find all inos or all patterned inos
    if args.all or args.sketches:
        sketch_list = find_inos()
    # Only one ino
    elif args.ino:
        if os.path.exists(args.ino):
            sketch_list = [args.ino]
        else:
            assert os.path.exists(
                os.path.join(arduino_path, args.ino)
            ), "Ino path does not exist"
            sketch_list = [os.path.join(arduino_path, args.ino)]
    # Inos listed in a file
    elif args.file:
        assert os.path.exists(args.file), "Sketches list file does not exist"
        with open(args.file, "r") as f:
            for line in f.readlines():
               ino = line.rstrip()
               if os.path.exists(ino):
                   sketch_list.append(ino)
               elif os.path.exists(os.path.join(arduino_path, ino)):
                   sketch_list.append(os.path.join(arduino_path, ino))
               else:
                   print("Ignore %s as does not exist." % ino)
    # Defailt ino to build
    else:
        sketch_list = [sketch_default]
    assert len(sketch_list), "No sketch to build!"

    # Find all .ino files
def find_inos():
    inoList = []
    for root, dirs, files in os.walk(arduino_path, followlinks=True):
        for file in files:
            if file.endswith(".ino"):
                if args.sketches:
                    regex = ".*(" + args.sketches + ").*"
                    x = re.match(regex, os.path.join(root, file), re.IGNORECASE)
                    if x:
                        inoList.append(os.path.join(root, x.group(0)))
                else:
                    inoList.append(os.path.join(root, file))
    return sorted(inoList)

#Return a list of all board types and names using the board.txt file
def find_board():
    for path in [arduino_packages, hardware_path]:
        for root, dirs, files in os.walk(path, followlinks=True):
            for file in files:
                if fnmatch.fnmatch(file, "boards.txt"):
                    if os.path.getsize(os.path.join(root, file)) != 0:
                        with open(os.path.join(root, file), "r") as f:
                            regex = "(.+)\.menu\.pnum\.([^\.]+)="
                            for line in f.readlines():
                                x = re.match(regex, line)
                                if x:
                                    if args.board:
                                        reg = ".*(" + args.board + ").*"
                                        y = re.match(reg, x.group(0), re.IGNORECASE)
                                        if y:
                                            board_type = x.group(1)
                                            board_name = x.group(2)
                                            board = (board_type, board_name)
                                            board_list.append(board)
                                    else:
                                        board_type = x.group(1)
                                        board_name = x.group(2)
                                        board = (board_type, board_name)
                                        board_list.append(board)
    return sorted(board_list)

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

# Create arduino builder command
def create_command(board, sketch_path):
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
    cmd.append(lib_path_default)
    cmd.append("-libraries")
    cmd.append(additional_lib_path)
    cmd.append("-fqbn")
    cmd.append(set_varOpt(board))
    cmd.append("-ide-version=10805")
    cmd.append("-build-path")
    cmd.append(build_output_dir)
    cmd.append("-warnings=all")
    if args.verbose:
        cmd.append("-verbose")
    cmd.append(sketch_path)
    return cmd

# Automatic run
def build_all():
    current_sketch = 0
    for files in sketch_list:
        boardOk = []
        boardKo = []
        current_board = 0
        current_sketch += 1
        sketch_name = os.path.basename(files)
        print(
            "\nRUNNING : {} ({}/{}) ".format(
                sketch_name, current_sketch, len(sketch_list)
            )
        )
        print("Sketch path : " + files)
        for board in board_list:
            board_name = board[1]
            current_board += 1
            sys.stdout.write(
                "Build {} ({}/{})... ".format(
                    board_name, current_board, len(board_list)
                )
            )
            sys.stdout.flush()

            command = create_command(board, files)
            status = build(command, board_name, sketch_name)
            if status == 0:
                boardOk.append(board_name)
            if status == 1:
                boardKo.append(board_name)
            check_status(status, board_name, sketch_name)
    print("\n****************** PROCESSING COMPLETED ******************")
    print(
        "PASSED = {}/{} ({}%) ".format(
            nb_build_passed,
            nb_build_total,
            round(nb_build_passed / nb_build_total * 100),
        )
    )
    print(
        "FAILED = {}/{} ({}%) ".format(
            nb_build_failed,
            nb_build_total,
            round(nb_build_failed / nb_build_total * 100),
        )
    )
    print("Logs are available here: " + output_dir)

    # Run arduino builder command
def build(cmd, board_name, sketch_name):
    boardstd = os.path.join(
        output_dir, board_name, std_dir
    )  # Board specific folder that contain stdout and stderr files
    createFolder(boardstd)
    stddout_name = sketch_name + "_stdout.txt"
    stdderr_name = sketch_name + "_stderr.txt"
    with open(os.path.join(boardstd, stddout_name), "w") as stdout, open(
        os.path.join(boardstd, stdderr_name), "w"
    ) as stderr:
        res = subprocess.Popen(cmd, stdout=stdout, stderr=stderr)
        res.wait()
        return res.returncode

# Parser
parser = argparse.ArgumentParser(description="Automatic build script")
parser.add_argument(
    "-a",
    "--all",
    help="-a : automatic build - build all sketches for all board",
    action="store_true",
)
parser.add_argument(
    "-b",
    "--board",
    help="-b <board pattern>: pattern to find one or more boards to build",
)
parser.add_argument(
    "-c",
    "--clean",
    help="-c: clean output directory by deleting %s folder" % root_output_dir,
    action="store_true",
)
group = parser.add_mutually_exclusive_group()
group.add_argument("-i", "--ino", help="-i <ino filepath>: single ino file to build")
group.add_argument(
    "-f",
    "--file",
    help=" -f <sketches list file>: file containing list of sketches to build",
)
group.add_argument(
    "-s",
    "--sketches",
    help=" -s <sketch pattern>: pattern to find one or more sketch to build",
)
parser.add_argument(
    "-e",
    "--exclude",
    help="-e <exclude list file>: file containing pattern of sketches to ignore | Default path : <working directory>\conf\exclude_list.txt ",
)
parser.add_argument(
    "-v",
    "--verbose",
    help="-v : enable arduino-builder verbose mode",
    action="store_true",
)

args = parser.parse_args()

# Clean previous build results
if args.clean:
    deleteFolder(root_output_dir)

# Create output folders
createFolder(build_output_dir)
createFolder(output_dir)

manage_inos()
find_board()

# Run builder
build_all()

# Remove build output
deleteFolder(build_output_dir)
