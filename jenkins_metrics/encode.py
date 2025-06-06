import bcrypt

# Force $2a$ format by manipulating the salt (Jenkins compatibility)
salt = bcrypt.gensalt(rounds=10, prefix=b'2a')
hashed = bcrypt.hashpw('admin'.encode('utf-8'), salt).decode('utf-8')
print(f'#jbcrypt:{hashed}')
