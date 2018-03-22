#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib

from address import *
from crypto import (dsha256, EllipticCurveKey)

SIGHASH_ALL = 0x01
SIGHASH_FORKID = 0x40
FORKID = 0x00
BCH_SIGHASH_TYPE = 0x41

TRANSACTION_VERSION_1 = 1 # version 2 transactions exist
SEQUENCE_NUMBER = 0xffffffff - 1

# OP codes (make a dictionnary ?)
OP_DUP = 0x76
OP_HASH160= 0xa9
OP_EQUALVERIFY = 0x88
OP_CHECKSIG = 0xac

def construct_transaction( wifkey, receive_address, amount, locktime, prevtx_id, prevtx_index, prevamount ):
    ''' Construct a Bitcoin Cash transaction with one input and one output.
    wifkey (str) : private key (Wallet Import Format)
    receive_address (str) : recipient address (legacy or cash format)
    amount (int) : amount in satoshis 
    prevtx_id (str) : previous output transaction id
    prevtx_index (int) : index of the output in the previous transaction
    prevamount (int) : previous output amount in staoshis'''
    
    # Creation of elliptic curve keys (private key + public key)
    eckey = EllipticCurveKey.from_wifkey( wifkey )
    
    # Public key and address (Public Key Hash)
    publicKey = eckey.serialized_pubkey()
    lengthPublicKey = bytes([len(publicKey)])
    print("Public key", publicKey.hex())
    sendaddr = Address.from_pubkey( publicKey )
    print("Sending address", sendaddr.to_cash())
    recaddr = Address.from_string( receive_address )
    print("Receiving address", recaddr.to_cash())
    print()
    
    # Version (little-endian)
    version = TRANSACTION_VERSION_1
    nVersion = version.to_bytes(4,'little')
    
    # Signature hash type (little-endian)
    hashtype = BCH_SIGHASH_TYPE
    nHashtype = hashtype.to_bytes(4,'little')
    
    # Sequence number (little-endian)
    sequence = SEQUENCE_NUMBER
    nSequence = sequence.to_bytes(4,'little')
    
    # Amount in satoshis (little-endian)
    nAmount = amount.to_bytes(8,'little')
    
    # Locktime (little-endian)
    nLocktime = locktime.to_bytes(4,'little')
    
    # Previous output hash (previous transaction id)
    prevHash = bytes.fromhex( prevtx_id )[::-1]
    
    # Previous output index in this transaction
    prevIndex = prevtx_index.to_bytes(4,'little')
    
    # Previous output value
    prevValue = prevamount.to_bytes(8,'little')
    
    # Number of tx inputs
    input_count = 1
    nInputs = bytes([input_count])
    
    # Number of tx outputs
    output_count = 1
    nOutputs = bytes([output_count])
    
    # Input Public Key Hash
    pubkeyHash_in = sendaddr.hash_addr
    
    # Previous locking script
    prevLockingScript = bytes([OP_DUP]) + bytes([OP_HASH160]) + bytes([0x14]) + pubkeyHash_in + bytes([OP_EQUALVERIFY]) + bytes([OP_CHECKSIG])
    
    # Length of previous locking script
    lengthPrevLockingScript = bytes([len(prevLockingScript)])
    
    # Output Public Key Hash
    pubkeyHash_out = recaddr.hash_addr
    
    # Locking script
    lockingScript = bytes([OP_DUP]) + bytes([OP_HASH160]) + bytes([0x14]) + pubkeyHash_out + bytes([OP_EQUALVERIFY]) + bytes([OP_CHECKSIG])
    
    # Length of previous locking script
    lengthLockingScript = bytes([len(lockingScript)])
    
    outpoint = prevHash + prevIndex
    hashPrevouts = dsha256( outpoint )
    hashSequence = dsha256( nSequence )
    hashOutputs = dsha256( nAmount + lengthLockingScript + lockingScript )
    
    # --- Construct preimage ---
    # BIP-143
    preimage = b""
    
    preimage += nVersion # version
    preimage += hashPrevouts
    preimage += hashSequence
    preimage += outpoint
    preimage += lengthPrevLockingScript # length of the previous output locking script
    preimage += prevLockingScript # previous output locking script (scriptPubKey)
    preimage += prevValue # value of the previous output
    preimage += nSequence # sequence number
    preimage += hashOutputs
    preimage += nLocktime # locktime
    preimage += nHashtype # signature 4-bytes hash type
    
    print("PREIMAGE",preimage.hex())
    print()
    
    # We sign the double SHA256 hash of the preimage with our private key
    prehash = dsha256( preimage )
    signature = eckey.sign( prehash )
    lengthSigandHash = bytes([len(signature)+1])
    
    # --- Construct unlocking script ---
    unlockingScript = b""
    
    unlockingScript += lengthSigandHash # length of the signature
    unlockingScript += signature # DER-encoded signature of the double sha256 of the preimage
    unlockingScript += bytes([hashtype]) # signature 1-byte hash type
    unlockingScript += lengthPublicKey # length of serialized public key
    unlockingScript += publicKey # serialized public key
    
    lengthUnlockingScript = bytes([len(unlockingScript)])
    
    # --- Construct transaction ---
    rawtx = b""
    
    rawtx += nVersion # version
    rawtx += nInputs # input count
    
    rawtx += prevHash # previous output hash
    rawtx += prevIndex # previous output index
    rawtx += lengthUnlockingScript # length of the unlocking script
    rawtx += unlockingScript # unlocking script (scriptSig)
    rawtx += nSequence # sequence number
    
    rawtx += nOutputs # output count
    
    rawtx += nAmount # value of the output
    rawtx += lengthLockingScript # length of the output locking script
    rawtx += lockingScript # output locking script
    
    rawtx += nLocktime # locktime
    
    txid = dsha256( rawtx )[::-1]
    
    return rawtx.hex(), txid.hex()
    
    
if __name__ == '__main__':
    print()
    print("BROADCAST TRANSACTION")
    print("---------------------")
    print()
    
    wifkey = "5KMYonsNGYJj8UXf2L4M7gmKi87yXThjgDuVpWoekjYjCR4S5nr"
    recipient_address = "bitcoincash:qq7ur36zd8uq2wqv0mle2khzwt79ue9ty57mvd95r0"
    amount = 29066
    locktime = 522542 # in electron : height of the last block
    prevtx_id = "31ba61e23bc532e3210c6521757f6f9cf46540fc9a57dd2c1493551b14f7f4d4"
    prevtx_index = 0
    prevamount = 29316 # previous output amount
    
    tx, txid = construct_transaction( wifkey, recipient_address, amount, locktime, prevtx_id, prevtx_index, prevamount )
    print("RAW TRANSACTION")
    print(tx)
    print()
    print("TRANSACTION ID")
    print(txid)
    print()
    print("Transaction fees (sat)", prevamount-amount)
    print()
    