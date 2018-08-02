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

import hashlib
import base64
from base64 import b64encode
import time
import requests
import yaml

from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory
from sawtooth_signing import ParseError
from sawtooth_signing.secp256k1 import Secp256k1PrivateKey

from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader
from sawtooth_sdk.protobuf.transaction_pb2 import Transaction
from sawtooth_sdk.protobuf.batch_pb2 import BatchList
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader
from sawtooth_sdk.protobuf.batch_pb2 import Batch


from wills.willsandtrust_exceptions import WillsAndTrustException

# The Transaction Family Name
FAMILY_NAME='willsandtrust'

def _hash(data):
    return hashlib.sha512(data).hexdigest()


class WillsAndTrustClient:
    def __init__(self, baseUrl, keyFile=None):

        self._baseUrl = baseUrl

        if keyFile is None:
            self._signer = None
            return

        try:
            with open(keyFile) as fd:
                privateKeyStr = fd.read().strip()
        except OSError as err:
            raise WillsAndTrustException(
                'Failed to read private key {}: {}'.format( \
                    keyFile, str(err)))

        try:
            privateKey = Secp256k1PrivateKey.from_hex(privateKeyStr)
        except ParseError as e:
            raise WillsAndTrustException( \
                'Failed to load private key: {}'.format(str(e)))

        self._signer = CryptoFactory(create_context('secp256k1')) \
            .new_signer(privateKey)

        self._publicKey = self._signer.get_public_key().as_hex();

        self._address = _hash(FAMILY_NAME.encode('utf-8'))[0:6] + \
            _hash(self._publicKey.encode('utf-8'))[0:64]

    # For each valid cli commands in _cli.py file
    # Add methods to:
    # 1. Do any additional handling, if required
    # 2. Create a transaction and a batch
    # 2. Send to rest-api
    def upload(self, file_name):
        return self._wrap_and_send(
            "upload",
            file_name)

    def read(self):
        result = self._send_to_restapi(
            "state/{}".format(self._address))
        try:
            decode1 = base64.b64decode(yaml.safe_load(result)["data"])
            decode2 = decode1.decode().split("'")[1]
            with open("read_will_form.pdf","wb") as f_write:
                f_write.write(base64.b64decode(decode2))
            return decode2    

        except BaseException:
            return None

    def _send_to_restapi(self,
                      suffix,
                      data=None,
                      contentType=None):
        if self._baseUrl.startswith("http://"):
            url = "{}/{}".format(self._baseUrl, suffix)
        else:
            url = "http://{}/{}".format(self._baseUrl, suffix)

        headers = {}

        if contentType is not None:
            headers['Content-Type'] = contentType

        try:
            if data is not None:
                result = requests.post(url, headers=headers, data=data)
            else:
                result = requests.get(url, headers=headers)

            if not result.ok:
                raise WillsAndTrustException("Error {}: {}".format(
                    result.status_code, result.reason))

        except requests.ConnectionError as err:
            raise WillsAndTrustException(
                'Failed to connect to {}: {}'.format(url, str(err)))

        except BaseException as err:
            raise WillsAndTrustException(err)

        return result.text

    def _wrap_and_send(self,
                     action,
                     *files):

        # Generate a csv utf-8 encoded string as payload
        rawPayload = action
        for f in files:
            with open(f, 'rb') as pdf_file:
                encoded_string = base64.b64encode(pdf_file.read())
            rawPayload = ",".join([rawPayload, str(encoded_string)]) 
        payload = rawPayload.encode()

        # Construct the address where we'll store our state
        address = self._address
        inputAddressList = [address]
        outputAddressList = [address]
        
        # Create a TransactionHeader
        header = TransactionHeader(
            signer_public_key=self._publicKey,
            family_name=FAMILY_NAME,
            family_version="1.0",
            inputs=inputAddressList,
            outputs=outputAddressList,
            dependencies=[],
            payload_sha512=_hash(payload),
            batcher_public_key=self._publicKey,
            nonce=time.time().hex().encode()
        ).SerializeToString()

        # Create a Transaction from the header and payload above
        transaction = Transaction(
            header=header,
            payload=payload,
            header_signature=self._signer.sign(header)
        )

        transactionList = [transaction]

        # Create a BatchHeader from TransactionList above
        header = BatchHeader(
            signer_public_key=self._publicKey,
            transaction_ids=[txn.header_signature for txn in transactionList]
        ).SerializeToString()

        #Create Batch using the BatchHeader and transactionList above
        batch = Batch(
            header=header,
            transactions=transactionList,
            header_signature=self._signer.sign(header))

        #Create a Batch List from Batch above
        batch_list = BatchList(batches=[batch])

        # Send batch_list to rest-api
        return self._send_to_restapi(
            "batches",
            batch_list.SerializeToString(),
            'application/octet-stream')