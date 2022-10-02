def count_substring(string, sub_string):
    count = 0
    substrlen = len(sub_string)
    strlen = len(string)
    for _ in range(strlen):
        if string[-substrlen:] == sub_string:
            count = count+1
        string = string[:-1]
    return count
        