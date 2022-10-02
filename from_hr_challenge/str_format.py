def print_formatted(number):
    w = len(str(bin(number))) - 2
    for i in range(1, number+1):
        num = str(i).rjust(w, ' ')
        octal = str(oct(i)[2:]).rjust(w, ' ')
        hexa = str(hex(i)[2:]).upper().rjust(w, ' ')
        binary = str(bin(i)[2:]).rjust(w, ' ')
        print(num, octal, hexa, binary)