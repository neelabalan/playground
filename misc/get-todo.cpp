/*
[why I am writing this]
wanted to use <filesystem> on some code :)

[compilation]
g++ -std=c++17 get-todo.cpp -o get-todo

[usage]
./get-todo /home/user/todolist

*/
#include <iostream>
#include <filesystem>
#include <string>
#include <fstream>
#include <vector>

const std::string WHITESPACE = " \n\r\t\f\v";
// trim space
std::string ltrim(const std::string &s)
{
    size_t start = s.find_first_not_of(WHITESPACE);
    return (start == std::string::npos) ? "" : s.substr(start);
}

void printTodos(std::vector<std::string> paths)
{
    bool flag = true;
    for (const auto path : paths)
    {
        std::ifstream ifs{path};
        std::string str = "";
        flag = true;
        while (getline(ifs, str))
        {
            if ((ltrim(str).find("- [ ] ") == 0) || (ltrim(str).find("- [x] ") == 0))
            {
                if (flag)
                {
                    std::cout << "####" << path << std::endl;
                    flag = false;
                }
                std::cout << str << std::endl;
            }
        }
    }
}

auto dirTraversal(std::string dirPath)
{
    std::vector<std::string> paths{};
    using recursive_directory_iterator = std::filesystem::recursive_directory_iterator;
    for (const auto &entry : recursive_directory_iterator(dirPath))
    {
        if (std::filesystem::is_regular_file(entry))
        {
            paths.push_back(entry.path().string());
        }
    }
    return paths;
}

int main(int argc, char** argv)
{
    auto paths = dirTraversal(argv[1]);
    printTodos(paths);
}