if __name__ == '__main__':
    n, m = input().strip().split()
    athelete_list = list()
    for _ in range(int(n)):
        athelete_list.append(
            list(
                map(int, input().strip().split())
            )
        )
    index = int(input())
        
    athelete_list.sort(key=lambda x: x[index])
    for ath in athelete_list:
        print(
            ' '.join(
                list(map(str, ath))
            )
        )
