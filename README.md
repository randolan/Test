# stm32_tools
Useful tools for stm32

## arduino-builder.py 
Used to build sketch(es) thanks Arduino builder for all [Arduino_Core_STM32](https://github.com/stm32duino/Arduino_Core_STM32) variants.

**Configure:** 

Once you run arduino-builder.py script, a _config.json_ file containing default operating system-dependent paths, will be automatically created in the working directory. Set this file to configure your arduino builder environment. 
```
ARDUINO_PATH : <arduino IDE installation folder> Path to Arduino installation folder.

ARDUINO_PACKAGES : <arduino packages path> Path to folder containing Arduino packages.

BUILD_OUTPUT_DIR : <build output directory path> Path to temporary folder where compiled files are stored.

ROOT_OUTPUT_DIR : <root ouput directory path> Path to folder where log files are saved.

SKETCHBOOK_PATH : <sketchbook directory path> Path to folder where the Arduino IDE stores 

```
**Examples:** 
  * To build all ino file found in _examples_ and  _libraries_ directories:
  
_Note: exclude_list.txt is used to filter sketches found.See more informations about this file in -e section_
  
`./arduino-builder.py -a`
  * To build a specific ino _\<path to my ino file\>/mysketch.ino_:
  
`./arduino-builder.py -i /tmp/SerialLoop.ino`
  * To build a specific set of sketch using a pattern:
  
`./arduino-builder.py -s "08\.|09\."`

will build all sketch in _examples/09.USB_ and _examples/08.Strings_ directories
* To build a specific list of sketch:

_Note: sketches list file must contain path to the desired sketches.
  
`./arduino-builder.py -f : <sketches list file>`

will build all sketch listed in the sketches list file.
  * To build a specific set of boards using a pattern:
  
`./arduino-builder.py -b "F4"`

will build sketch for all variants name including **F4**.

 * To ignore a specific list of sketc using a pattern:
  
`./arduino-builder.py -a -e:<exclude list file>`

will build sketch for all sketch expecting the ones matching the pattern from exclude list.

_Note : 
Blink sketch is build by default for all variants. To build other sketch you can use previous options. Be aware that with -all and --file options, exclude list will be automatically used if present._

**Usage:**
```
usage: arduino-builder.py [-h] [-a] [-b BOARD] [-c]
                          [-i INO | -f FILE | -s SKETCHES] [-e EXCLUDE] [-v]

Automatic build script

optional arguments:
  -h, --help            show this help message and exit
  -a, --all             -a : automatic build - build all sketches for all
                        board
  -b BOARD, --board BOARD
                        -b <board pattern>: pattern to find one or more boards
                        to build
  -c, --clean           -c: clean output directory by deleting
                        C:\Users\randolpa\arduinoBuilderOutput folder
  -i INO, --ino INO     -i <ino filepath>: single ino file to build
  -f FILE, --file FILE  -f <sketches list file>: file containing list of
                        sketches to build
  -s SKETCHES, --sketches SKETCHES
                        -s <sketch pattern>: pattern to find one or more
                        sketch to build
  -e EXCLUDE, --exclude EXCLUDE
                        -e <exclude list file>: file containing pattern of
                        sketches to ignore | Default path : <working
                        directory>\conf\exclude_list.txt
  -v, --verbose         -v : enable arduino-builder verbose mode
  
```
## [deprecated] arduino-builder-cli.sh (linux)
Used to build sketch(es) thanks Arduino CLI for all [Arduino_Core_STM32](https://github.com/stm32duino/Arduino_Core_STM32) variants.

Launch this script at the top of Arduino IDE directory.

**Examples:**
  * To build all ino file found in _examples_ and  _libraries_ directories:
  
_Note: exclude_list.txt is used to filter sketches found._
  
`./arduino-builder-cli.sh -a`
  * To build a specific ino _\<path to my ino file\>/mysketch.ino_:
  
`./arduino-builder-cli.sh -i /tmp/SerialLoop.ino`
  * To build a specific set of sketch using a pattern:
  
`./arduino-builder-cli.sh -s "08\.|09\."`

will build all sketch in _examples/09.USB_ and _examples/08.Strings_ directories
  * To build a specific set of boards using a pattern:
  
`./arduino-builder-cli.sh -b "F4"`

will build sketch for all variants name including **F4**.

## genpinmap (Moved to [Arduino_Tools](https://github.com/stm32duino/Arduino_Tools))

## gen_cmsis_startup_file_list.sh
Used to generate the stm32_def_build.h file.

Launch it at the root of [Arduino_Core_STM32](https://github.com/stm32duino/Arduino_Core_STM32)

## gen_stm32yyxx_files.sh
Used to generate stm32yyxx files to wrap HAL/LL files

Launch it at the root of [Arduino_Core_STM32](https://github.com/stm32duino/Arduino_Core_STM32)

## gen_peripheralpins_files.sh
Used to generate all `PeripheralPins.c` files for all STM32 MCU xml file description provided with [STM32CubeMX](http://www.st.com/en/development-tools/stm32cubemx.html) using [genpinmap.py](https://github.com/stm32duino/Arduino_Tools/blob/master/src/genpinmap/genpinmap_arduino.py) script.

Launch it from the same folder than [genpinmap.py](https://github.com/stm32duino/Arduino_Tools/blob/master/src/genpinmap/genpinmap_arduino.py) script.
