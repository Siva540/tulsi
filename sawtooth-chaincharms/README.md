# sawtooth-willsandtrust
A simple sawtooth "willsandtrust" transaction family example (processor + client)

# Introduction

This is a minimal example of a sawtooth 1.0 application. This example demonstrates, a common usecase, where a Will-writer upload/read/update Will from his/her Will-wallet account. The willsandtrust application is based on hyperledger Sawtooth simplewallet application(https://github.com/askmish/sawtooth-simplewallet).

A Will-writer can:
1. upload Will-form into his/her Will-wallet account
2. read Will-form from his/her Will-wallet account
3. Update Will-form of a particular user(will-writer) account is again an upload will-form operation which will update the data at state address in the blockchain.

The customer is identified by a customer name and a corresponding public key. The Will-form, is stored at state address, derived from SHA 512 hash of customer's public key and the willsandtrust transaction family namespace.

# Components
The application is built in two parts:
1. The client application written in Python, written in two parts: _client.py file representing the backend stuff and the _cli.py representing the frontend stuff. The example is built by using the setup.py file located in one directory level up.

2. The Transaction Processor is written in python using python-sawtooth-sdk.

# Pre-requisites

This example uses docker-compose and Docker containers. If you do not have these installed please follow the instructions here: https://docs.docker.com/install/

**NOTE**

The preferred OS environment is Ubuntu 16.04.3 LTS x64. Although, other linux distributions which support Docker should work.
If you have Windows please install [Docker Toolbox for Windows](https://docs.docker.com/toolbox/toolbox_install_windows/) or [Docker for Windows](https://docs.docker.com/docker-for-windows/), based on your OS version.

### Working with proxies

**For linux:**

Follow the instructions in [sawtooth-core/BUILD.md](https://github.com/hyperledger/sawtooth-core/blob/master/BUILD.md#step-two-configure-proxy-optional)

**For pre-Windows 10 versions** (using Docker Toolbox for Windows):

Start the virtualbox host with:
```
   docker-machine rm default
   docker-machine create -d virtualbox --engine-env HTTP_PROXY=<your_http_proxy> --engine-env HTTPS_PROXY=<your_https_proxy> --engine-env NO_PROXY=<your_no_proxy> default
```
When you start Kitematic it will initially show an error, but just click "Use Virtualbox".

**For Windows 10** (using Docker for Windows):

Right click on the Docker icon in the notification area, select Settings. Then click Proxies. Select "Manual proxy configuration" and enter the following then click Apply.
```
    Web Server (HTTP):         <your_http_proxy>
    Secure Web Server (HTTPS): <your_https_proxy>
    Bypass for these hosts:    <your_no_proxy>,localhost,127.0.0.1
```

# Usage

Start the pre-built Docker containers in docker-compose.yaml file, located in sawtooth-willsandtrust directory:
```bash
cd sawtooth-willsandtrust
docker-compose -f willsandtrust-build-tp-py.yaml up
```
At this point all the containers should be running.

To launch the client, you could do this:
```bash
docker exec -it willsandtrust-client bash
```

You can locate the right Docker client container name using `docker ps`.

Sample command usage:

```bash
#Create a Will-wallet
sawtooth keygen user1 #This creates the public/private keys for user1, a pre-requisite for the following commands

willsandtrust upload <absolute path for Will-form> user1 #This uploads Will-form to user1's account

willsandtrust read user1 #Displays uploaded will-form from user1's account
```
Sample API Usage:

```bash
http://<machine-IP>:8008/batches (or) http://<machine-IP>:8008/blocks
http://<machine-IP>:8008/batch_statuses?id=<batch_id>
http://<machine-IP>:8008/state 
http://<machine-IP>:8008/state/<state-address> 
```
Where, <machine-IP> replaced with the IP of the machine where <rest-api> service is running.
