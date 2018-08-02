# Copyright 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------

from __future__ import print_function
import argparse
import getpass
import logging
import os
import sys
import requests
import traceback
import pkg_resources

from colorlog import ColoredFormatter

from wills.willsandtrust_client import WillsAndTrustClient
from wills.willsandtrust_exceptions import WillsAndTrustException

DISTRIBUTION_NAME = 'willsandtrust'

try:
    res =  requests.head(os.getenv("test_rest_con"), timeout=5)
    if(res.ok):
        DEFAULT_URL = os.getenv("rest_url").split()[0]
except requests.exceptions.ConnectionError:
    DEFAULT_URL = os.getenv("rest_url").split()[1]

def create_console_handler(verbose_level):
    clog = logging.StreamHandler()
    formatter = ColoredFormatter(
        "%(log_color)s[%(asctime)s %(levelname)-8s%(module)s]%(reset)s "
        "%(white)s%(message)s",
        datefmt="%H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red',
        })

    clog.setFormatter(formatter)
    clog.setLevel(logging.DEBUG)
    return clog

def setup_loggers(verbose_level):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(create_console_handler(verbose_level))

def add_upload_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'upload',
        help='Upload a pdf file to an account',
        parents=[parent_parser])

    parser.add_argument(
        'file_name',
        type=str,
        help='the absolute path of the file to upload')

    parser.add_argument(
        'WillWriterName',
        type=str,
        help='the name of Willwriter to upload Will to')


def add_read_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'read',
        help='read an uploaded file',
        parents=[parent_parser])

    parser.add_argument(
        'WillWriterName',
        type=str,
        help='the name of Willwriter to read from')
        

def create_parent_parser(prog_name):
    parent_parser = argparse.ArgumentParser(prog=prog_name, add_help=False)

    try:
        version = pkg_resources.get_distribution(DISTRIBUTION_NAME).version
    except pkg_resources.DistributionNotFound:
        version = 'UNKNOWN'

    parent_parser.add_argument(
        '-V', '--version',
        action='version',
        version=(DISTRIBUTION_NAME + ' (Hyperledger Sawtooth) version {}')
        .format(version),
        help='display version information')

    return parent_parser


def create_parser(prog_name):
    parent_parser = create_parent_parser(prog_name)

    parser = argparse.ArgumentParser(
        description='Provides subcommands to manage your willsandtrust',
        parents=[parent_parser])

    subparsers = parser.add_subparsers(title='subcommands', dest='command')

    subparsers.required = True

    add_upload_parser(subparsers, parent_parser)
    add_read_parser(subparsers, parent_parser)

    return parser

def _get_keyfile(WillWriterName):
    home = os.path.expanduser("~")
    key_dir = os.path.join(home, ".sawtooth", "keys")

    return '{}/{}.priv'.format(key_dir, WillWriterName)
    
def _get_pubkeyfile(WillWriterName):
    home = os.path.expanduser("~")
    key_dir = os.path.join(home, ".sawtooth", "keys")

    return '{}/{}.pub'.format(key_dir, WillWriterName)

def do_upload(args):
    keyfile = _get_keyfile(args.WillWriterName)

    client = WillsAndTrustClient(baseUrl=DEFAULT_URL, keyFile=keyfile)
    response = None
    if (os.path.exists(args.file_name)):
        response = client.upload(args.file_name)
    else:
        raise WillsAndTrustException(args.file_name + " not found")
    print("Response: {}".format(response))

def do_read(args):
    keyfile = _get_keyfile(args.WillWriterName)

    client = WillsAndTrustClient(baseUrl=DEFAULT_URL, keyFile=keyfile)

    data = client.read()

    if data is not None:
        print("\n{} Uploaded file data written to a file read_will_form.pdf \n"
             .format(args.WillWriterName))
    else:
        raise WillsAndTrustException("Data not found: {}"
                                    .format(args.WillWriterName))


def main(prog_name=os.path.basename(sys.argv[0]), args=None):
    if args is None:
        args = sys.argv[1:]
    parser = create_parser(prog_name)
    args = parser.parse_args(args)

    verbose_level = 0

    setup_loggers(verbose_level=verbose_level)

    # Get the commands from cli args and call corresponding handlers
    if args.command == 'upload':
        do_upload(args)
    elif args.command == 'read':
        do_read(args)
    else:
        raise WillsAndTrustException("Invalid command: {}".format(args.command))


def main_wrapper():
    try:
        main()
    except WillsAndTrustException as err:
        print("Error: {}".format(err), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        pass
    except SystemExit as err:
        raise err
    except BaseException as err:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
