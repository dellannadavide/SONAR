# Steps to setup environment to use NOSAR with the Nao robot


## 1. Nao Softbank software, installation and setup
Software download page: https://www.aldebaran.com/fr/support/nao-6/downloads-softwares
- **Robot Settings**. Useful for checking and changing settings of Nao (e.g., wifi connection, or updates)
    > Verify installation by inserting Nao's IP address (press chest button on Nao to get it) and pressing Enter

- **Chorégraphe Suite**. Useful for creating and controlling behaviors for Nao; for installing behaviors on the robot; and for running the virtual robot.

  - Verify installation as follows:
    >1. Go to Connection -> Connect to...
    >2. Insert Nao's IP address (as per Robot Settings) in the field "Use fixed IP/hostname"
    >3. Nao should appear in the robot view
    >4. Try to execute a behavior: drag and drop from the Box libraries to the root field one animation (e.g.,the Animation->Moods->Positive->NAO->Happy animation), connect it to the onStart event, and press the green play button. Nao should execute the animation.
    
  - Setup the virtual robot as follows:
    >1. Go to Edit -> Preferences -> Virtual Robot
    >2. Select Robot model NAO H25 (V6)
    >3. Note on the bottom of the panel the **port on which NAOqi is running** (important for interfacing with Python) 
    >4. Press OK, then press Connection -> Connect to virtual robot
    >5. Press OK, then try to execute a behavior: drag and drop from the Box libraries to the root field one animation (e.g.,the Animation->Moods->Positive->NAO->Happy animation), connect it to the onStart event, and press the green play button. The virtual robot should execute the animation.

- **Python 2.7 NAOqi SDK**. Required to control Nao via Python.
  - Follow the installation instructions from Aldebaran [here](http://doc.aldebaran.com/2-8/dev/python/install_guide.html).

## 2. Basic services required to run NOSAR and the MQTT-Nao-Interface
### 2.1. XMPP communication server.
NOSAR makes use of the Python library [SPADE](https://spade-mas.readthedocs.io/en/latest/readme.html), which is a Multi-agent platform based on [XMPP](https://xmpp.org/) (the open universal messaging standard). SPADE requires access to an XMPP communication server. 
Below, it is reported a quick tutorial on how to install [Prosody](https://prosody.im/), the SPADE recommended XMPP server, on Windows 10. 
For more details see the [SPADE quick start](https://spade-mas.readthedocs.io/en/latest/usage.html) and the [Prosody guidelines](https://prosody.im/download/start#windows).
#### 2.1.1. Install Linux on Windows with WSL (see [Microsoft guidelines](https://learn.microsoft.com/en-us/windows/wsl/install))
>1. Open Windows PowerShell with admin rights
>2. Run ``` wsl --install ```
>3. Reboot the system 
>4. Open Microsoft Store and type and get Ubuntu
>5. Follow the instruction in the Ubuntu terminal to create a new UNIX user account.
>6. Run ``` sudo apt update && sudo apt upgrade```  to update packages.
#### 2.1.2. Install Prosody on Ubuntu
>1. In the Ubuntu terminal, as per step 6 of Sec 2.1.1., run ``` sudo apt install prosody ``` and type ```Y``` when requested.
>2. That's it. See Section 4.2.1. for details on how to create accounts for the SPADE agents.
#### 2.1.3. Start Prosody service
>In the Ubuntu terminal, run ``` sudo service prosody start ```

### 2.2. MQTT message broker
Communication between NOSAR and the (Python 2.7) MQTT-Nao-Interface happens via [MQTT](https://en.wikipedia.org/wiki/MQTT) (a lightweight method of carrying out messaging using a publish/subscribe model, and the standard messaging protocol for the Internet of Things). 

Services from both NOSAR and MQTT-Nao-Interface subscribe to or publish messages. This allows for decoupling between the specific interface with the robot or other devices (e.g., microphones, cameras. or IoT devices) and NOSAR. 

Specifically concerning the python MQTT-Nao-Interface, such an interface runs, due to compatibility constraints with the NAOqi Python SDK, on Python 2.7 (which is not well supported anymore as of 2022). 
Decoupling such an interface from the implementation of NOSAR, facilitates the implementation of several modern features that rely on libraries based on Python 3.x.

Below, it is reported a very quick tutorial on how to install [Eclipse Mosquitto](https://mosquitto.org/), an open source message broker that implements the MQTT protocol, on the Ubuntu distro installed as per Section 2.1.1.

#### 2.2.1. Install and start Mosquitto on Ubuntu
>1. In the Ubuntu terminal, as per step 6 of Sec 2.1.1., add the mosquitto-dev PPA by running first ```sudo apt-add-repository ppa:mosquitto-dev/mosquitto-ppa``` and then ```sudo apt-get update```.
>2. To install Mosquitto, run ``` sudo apt install mosquitto ``` and type ```Y``` when requested.
>3. To start Mosquitto, run ``` sudo service mosquitto start ```



## 3. Setup the MQTT-Nao-Interface
### 3.1. Required software and libraries
MQTT-Nao-Interface is a python resource that runs on Python 2.7. Therefore the basic requirement is [Python 2.7](https://www.python.org/downloads/).

Secondly, the MQTT-Nao-Interface needs the Python 2.7 NAOqi SDK. See section 1 for details on installation.

The MQTT-Nao-Interface also requires a number of Python packages to be installed. 
The list of requirements can be found in the ```requirements.txt``` file. 
A standard way to install all required libraries is to run command ```pip install -r /path/to/requirements.txt```. 
Based on your environment you may adopt the most handy procedure.

Finally, MQTT-Nao-Interface relies on an MQTT broker. Follow steps in Section 2 to install it.


### 3.2. Setup and Run
#### 3.2.1. Upload additional behaviors on Nao
NOSAR can instruct the MQTT-Nao-Interface to execute a number of non-default behaviors on Nao (e.g., some particular movements).
These behaviors can be found in folder ```MQTT-Nao-Interface/lib/Nao_Additional_Behaviors```, which contains a Choreographe project.
In order to upload them on Nao and/or on a virtual robot follow the next steps.
>1. Open Choreographe
>2. Open the project (File -> Open project) contained in the ```Nao_Additional_Behaviors``` folder.
>3. In the ```Robot applications``` panel in Choreographe press the button ```Package and install current project to the robot```. An entry named ```Nao_Additional_Behaviors``` should appear in the list of applications of the robot.
>4. Run, on Choreographe, one of the behaviors (e.g., open ```behaviors/anger/behavior.xar``` and press play after connecting to the (virtual) robot). By doing so all behaviors in the project will be also automatically loaded in the ```.lastUploadedChoreographeBehavior``` application, which is the only application available to the virtual robot.


#### 3.2.1 Run MQTT-Nao-Interface
>1. Start Mosquitto as per section 2.2.1
>2. Turn on Nao, or connect to a virtual robot.
>3. Determine the IP and port of the robot. For Nao, press the chest to obtain its IP address (the default port is ```9559```). For the virtual robot in Choreographe, the IP is ```localhost``` if Choreographe is running on the same machine as the MQTT-Nao-Interface, and the port can be found in the preferences as per Section 1.
>4. Assign the correct IP and port to variables ```ip``` and ```port``` in file ```MQTT-Nao-Interface/main.py```.
>5. Run MQTT-Nao-Interface via ```python MQTT-Nao-Interface/main.py```.




## 4. Setup NOSAR
### 4.1. Required software and libraries
NOSAR is a python resource that runs on Python 3.9. Therefore the basic requirement is [Python 3.9](https://www.python.org/downloads/).

NOSAR makes extensive use of a variety of state-of-the-art libraries for, among others: multi-agent communication; natural language processing, understanding and generation; Fuzzy Inference, Multi-Objective optimization, Belief-Desire-Intention-based inference. 
For this reason, after having set up the Python environment, a number of Python packages need to be installed. The list of requirements can be found in the ```requirements.txt``` file.
A standard way to install all required libraries is to run command ```pip install -r /path/to/requirements.txt```. Based on your environment you may adopt the most handy procedure.

Additionally, as per Section 2, NOSAR relies on XMPP and MQTT services. Follow steps in Section 2 to install them.

>**Notes** 
> 1. [SPADE](https://pypi.org/project/spade/) depends on some packages that require the [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) to be installed.
> 2. [SPADE](https://pypi.org/project/spade/) depends on some packages that require the ```lxml``` library to be installed. In case of troubles in installing this library on Windows: download the precompiled WHL from [http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml](http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml) for your Python and Windows version (e.g., if you are using Python 3.11 on Windows 64 bit, one adequate file is ```lxml‑4.9.0‑cp311‑cp311‑win_amd64.whl```) and install it by running ```pip install C:\path\to\downloaded\file\lxml‑4.5.2‑cp39‑cp39‑win32.whl```.
> 3. [Tokenizers](https://pypi.org/project/tokenizers/) might require to install a Rust compiler. On Windows, this can be easily installed from [https://rustup.rs/](https://rustup.rs/)
> 4. NOSAR makes extensive use of pretrained language models, which will be downloaded (if not available already) at the first execution. The whole set of models might require a couple of GB of space on the hard drive.
> 5. [Spacy](https://spacy.io/usage) requires the model ```en_core_web_sm```. This can be installed by running ```python -m spacy download en_core_web_sm```.

### 4.2. Setup and Run
#### 4.2.1 Register the agents in the XMPP server
The first step required in order to allow communication between agents in NOSAR is to register the agents in the XMPP server with a ```jid``` and a ```password```.

Following the [guidelines from the SPADE library](https://spade-mas.readthedocs.io/en/latest/usage.html), the jid (e.g., <agent_name>@<your_xmpp_server>) contains the agent’s name (before the @) and the DNS or IP of the XMPP server (after the @). 

> **Example.** Assuming that you installed the Prosody XMPP server locally by following the steps indicated in Section 2.1, the server IP will be by default ```localhost```.
An example of <agent_name> that operates in NOSAR is ```nosar_chatter```. In the default settings, therefore such an agent will have jid ```nosar_chatter@localhost```.

The list of required agents and XMPP-related information (e.g., name, server, jid, pwd) can be found at the bottom of file ```NOSAR/utils/constants.py```. 
All agents in the ```XMPP_AGENTS_DETAILS``` data structure should be registered in the XMPP server.

> **Tip.** You can extend or modify such a data structure if you run the agents on a different IP, if you want to give different names to the agents in the XMPP server, or if you want to add additional agents).

To register the required NOSAR agents on Prosody via terminal (see [Prosody guidelines](https://prosody.im/doc/creating_accounts) for more details):
>1. Start Prosody as per section 2.1.3
>2. Register an agent by running ```sudo prosodyctl adduser <agent_name>@<your_xmpp_server>```, and by providing the password for the agent as indicated in file ```nosar.utils.constants.py```.
>3. Repeat step 2 for all agents indicated in ```XMPP_AGENTS_DETAILS```.
>4. Verify that all agents have been created by listing the accounts registered in Prosody by running ```sudo ls /var/lib/prosody/localhost/accounts```. The output should contain the list of registered accounts on server ```localhost```.

#### 4.2.2 Run NOSAR
>1. Start Prosody as per section 2.1.3
>2. Start Mosquitto as per section 2.2.1
>3. Run NOSAR via ```python NOSAR/main.py```.

At this point NOSAR should be running, with the several agents communicating between each other, and waiting for messages to be received via the MQTT broker by the MQTT-Nao-Interface.


