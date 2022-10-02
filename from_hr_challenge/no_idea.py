# Enter your code here. Read input from STDIN. Print output to STDOUT
def common(l1, l2):
    return [element for element in l1 if element in l2]

n_no, m_no = input().split(' ')
ar = list(map(int, input().split(' ')))
a =  set(map(int, input().split(' ')))
b =  set(map(int, input().split(' ')))

happiness =  len(common(ar, a))
happiness = happiness - len(common(ar, b))

print(happiness)