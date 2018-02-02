#coding: utf8
import sys
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex
import ConfigParser

config = ConfigParser.ConfigParser()
cfgfile = open('/var/www/site/mycitsm/mycitsm/login.cnf', 'r')
config.readfp(cfgfile)
key = config.get('key', 'encrypt_iv')


class prpcrypt():
    def __init__(self, key):
        self.key = key
        self.mode = AES.MODE_CBC
     
    def encrypt_c(self, text):
        cryptor = AES.new(self.key, self.mode, self.key)
        length = 32
        count = len(text)
        add = length - (count % length)
        text = text + ('\0' * add)
        self.ciphertext = cryptor.encrypt(text)
        return b2a_hex(self.ciphertext)

    def decrypt_c(self, text):
        cryptor = AES.new(self.key, self.mode, self.key)
        plain_text = cryptor.decrypt(a2b_hex(text))
        return plain_text.rstrip('\0')


def encrypt(text):
    pc = prpcrypt(key)
    e = pc.encrypt_c(text)
    return e

def decrypt(text):
    pc = prpcrypt(key)
    d = pc.decrypt_c(text)
    return d


if __name__ == '__main__':
    e = encrypt("test123")
    d = decrypt('e835b3eb4e5a60f8c184b3d77bbc3d40356cbdc9fbdf0d0660bc0c76864e1de4')                     
    print e, d
    e = encrypt("000000000000000000000")
    d = decrypt(e)                  
    print e, d 
