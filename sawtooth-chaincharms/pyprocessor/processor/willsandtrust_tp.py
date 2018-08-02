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

import hashlib
import logging
import os

from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError
from sawtooth_sdk.processor.core import TransactionProcessor

LOGGER = logging.getLogger(__name__)

FAMILY_NAME = "willsandtrust"

def _hash(data):
    return hashlib.sha512(data).hexdigest()

sw_namespace = _hash(FAMILY_NAME.encode('utf-8'))[0:6]

class WillsAndTrustTransactionHandler(TransactionHandler):
    def __init__(self, namespace_prefix):
        self._namespace_prefix = namespace_prefix

    @property
    def family_name(self):
        return FAMILY_NAME

    @property
    def family_versions(self):
        return ['1.0']

    @property
    def namespaces(self):
        return [self._namespace_prefix]

    def apply(self, transaction, context):
        header = transaction.header
        payload_list = transaction.payload.decode().split(",")
        operation = payload_list[0]
        encoded_file = payload_list[1]
        
        from_key = header.signer_public_key

        LOGGER.info("Operation = "+ operation)

        if operation == "upload":
            self._make_upload(context, encoded_file, from_key)
        else:
            LOGGER.info("Unhandled action. Operation should be upload")

    def _make_upload(self, context, encoded_file, from_key):
        locker_key = self._get_locker_key(from_key)
        LOGGER.info('Got the key {} and the locker key {} '.format(from_key, locker_key))
        state_data = str(encoded_file).encode('utf-8')
        addresses = context.set_state({locker_key: state_data})
        if len(addresses) < 1:
            raise InternalError("State Error")

    def _get_locker_key(self, from_key):
        return _hash(FAMILY_NAME.encode('utf-8'))[0:6] + _hash(from_key.encode('utf-8'))[0:64]

def setup_loggers():
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

def main():
    setup_loggers()
    try:
        processor = TransactionProcessor(os.getenv("url"))

        handler = WillsAndTrustTransactionHandler(sw_namespace)

        processor.add_handler(handler)

        processor.start()

    except KeyboardInterrupt:
        pass
    except SystemExit as err:
        raise err
    except BaseException as err:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
