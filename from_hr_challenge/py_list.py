from queue import Queue


def call_function(command, element, index, oplist):
    """map of which function to be called and call em"""
    no_arg_map = {"sort": oplist.sort, "pop": oplist.pop, "reverse": oplist.reverse}
    single_arg_map = {"remove": oplist.remove, "append": oplist.append}

    if command in no_arg_map.keys():
        no_arg_map.get(command)()
    elif command in single_arg_map.keys():
        single_arg_map.get(command)(int(element))
    elif command == "insert":
        oplist.insert(int(element), int(index))
    else:
        print(oplist)


def process(command_queue):
    """calling functions based on commands"""
    list_output = []
    for command in command_queue.queue:
        call_function(
            command=command[0],
            element=command[1] if len(command) >= 2 else None,
            index=command[2] if len(command) == 3 else None,
            oplist=list_output,
        )
    return list_output


if __name__ == "__main__":
    N = int(input())
    command_queue = Queue()
    for i in range(N):
        command_queue.put(input().strip().split())
    process(command_queue)
