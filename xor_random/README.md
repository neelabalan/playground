## encryption
```bash
echo "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum" > sample.txt
```
```
>> py xor_random_secret.py --filein sample.txt --output cipher.txt
key stored as:  key.txt

>> cat key.txt
�CEvN0A�]0; /home/blue/github/python-playground/misc/xoring

>> cat sample.txt
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum

>> cat cipher.txt
c5#T.ʹ֠�w(bS.Ϩ�de'�2²�*bi�+�%�,re#�3�c+V;-�76!!�a̺�/4`e5�'6('�7ĵ�c,V �5Ӯֶ1u,:�/,6)!�2�76$?�1ֶ y(*�"ε78e'� ԯֺ�se"�aȵׄ�~ +�5֥6f1+F$Ͳֶ�6&"�aŴ&ce)�53w7:�o�c7�'�aθ76&'�5ט3d*+�m�-6&>�0Բי�$�+�3Ե־/1� �aȿד/w';�

```

## decryption
```
>> py xor_random_secret.py --key key.txt --filein cipher.txt --output decrypt.txt

>> cat decrypt.txt
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum
```
