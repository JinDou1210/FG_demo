# FG demo
## Environment

- windows 10
- FlightGear 2020.3.6
- python 3.8.3
- pandas 0.23.4
- numpy 1.14.2
- tensorflow 1.12.0
- [geographiclib](https://geographiclib.sourceforge.io/html/python/index.html) 1.49

## Install

1. Install Anaconda in your compute, you can get it [here](https://www.anaconda.com/download/). you need a python3 version.

2. add  `path\of\your\Anaconda\` and`path\of\you\Anaconda\Scripts` to your system environment

3. run the following command in your Windows PowerShell:

    ```shell
    conda install numpy
    conda install pandas
    conda install tensorflow
    pip install geographiclib
    ```

4. Install FlightGear on your computer, you can get it [here](http://home.flightgear.org/download/) 

5. copy `config/fgudp.xml`into folder `FG_ROOT/data/Protocol`. `FG_ROOT` is the folder where you install FG 

6. start flight gear and  add below command line option into the blank white box in the tail of flightgear setting page. after this , press the `fly` button to begin your fly. 

    ```
    --allow-nasal-from-sockets
    --telnet=5555
    --httpd=5500
    --generic=socket,in,10,127.0.0.1,5701,udp,fgudp
    --generic=socket,out,10,127.0.0.1,5700,udp,fgudp
    ```

7. To begin communicate with flightgear using python. just run the `python example.py`

8. **[tips] next time you only need to start flightgear and do step 7. you don't need to do step 1-6 again**

## Code & Features

- `train.py`
- `data_analysis.py`  data analysis
- `DRL`  RL model
    - `DQN` 
    - `ActorCritic`
    - `DDPG`
- `fgmodule` Communication and Control Module
    - `fgudp.py`  main module of flightgear communication
    - `fgcmd.py`  remote control, reset and other functions
    - `fgenv.py` 
- `scaffold` 
- `data` we will save all the fly log in folder `data/flylog`. their named by the time when the log created.

## terms

- `takeoff ` 
- `cruise ` 

## Relative Doc


- [Introduction to command line arguments at startup](http://flightgear.sourceforge.net/getstart-en/getstart-enpa2.html)

- [telnet help](http://wiki.flightgear.org/Telnet_usage#nasal?tdsourcetag=s_pctim_aiomsg) **this is very important for using telnet, please read carefully**

- quick replay
    Load Flight Recorder Tape (Shift-F1) load a pre-recorded flight to play back.
    Save Flight Recorder Tape (Shift-F2) saves the current flight to play back later.
    we can also use (Ctrl-R) to make a quick replay

- some important props 
    ```
    /sim/model/autostart  #autostart
    /controls/gear/brake-parking
    /sim/crashed #whether crashed
    ```

