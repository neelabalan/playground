def run(n):
    student_marks = {}
    for _ in range(n):
        name, *line = input().split()
        scores = list(map(float, line))
        student_marks[name] = scores
    query_name = input()
    marks = student_marks.get(query_name)
    print(f'{sum(marks) / len(marks):.2f}')


if __name__ == '__main__':
    n = int(input())
