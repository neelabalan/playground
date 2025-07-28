#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <getopt.h>
#include <netinet/in.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>  // for memset
#include <strings.h>
#include <sys/epoll.h>
#include <sys/socket.h>
#include <unistd.h>


#define BUFFER_SIZE 1024
#define DEFAULT_PORT 8080
#define MAX_EVENTS 10

void print_usage(const char* prog_name) {
    printf("usage: %s [-t|-u] [-p port]\n", prog_name);
    printf("options:\n");
    printf("  --transport <UDP/TCP> use TCP/UDP protocol (default is TCP)\n");
    printf("  --epoll               enable epoll to run TCP server");
    printf("  --p <port>            specify port number (default: %d)\n", DEFAULT_PORT);
    printf("  --help                show this help message\n");
}

void error_message(const char* format, ...) {
    va_list args;
    va_start(args, format);
    vfprintf(stderr, format, args);
    va_end(args);
    // ensure output is written immediately
    fflush(stderr);
}

typedef struct {
    char* transport;
    unsigned int port;
    bool epoll_enabled;
} cmd_args;

cmd_args parse_args(int argc, char* argv[]) {
    int opt;
    int option_index = 0;
    static struct option long_options[] = {
        {"transport", required_argument, 0, 't'},
        {"port", required_argument, 0, 'p'},
        {"epoll", no_argument, 0, 'e'},
        {"help", no_argument, 0, 'h'},
        {0, 0, 0, 0}
    };
    unsigned int port = DEFAULT_PORT;
    char* transport = "tcp";
    bool epoll_enabled = false;

    while ((opt = getopt_long(argc, argv, "", long_options, &option_index)) != -1) {
        switch (opt) {
        case 'e':
            epoll_enabled = true;
            break;
        case 't':
            transport = optarg;
            if (strcasecmp(transport, "tcp") != 0 && strcasecmp(transport, "udp") != 0) {
                error_message("invalid trasport protocol. Use 'tcp' or 'udp'");
                print_usage(argv[0]);
                exit(EXIT_FAILURE);
            }
            break;
        case 'p':
            port = atoi(optarg);
            if (port < 1) {
                error_message("port value cannot be less than 0");
                exit(EXIT_FAILURE);
            }
            break;
        case 'h':
            print_usage(argv[0]);
            exit(EXIT_SUCCESS);
        default:
            print_usage(argv[0]);
            exit(EXIT_SUCCESS);
        }
    }
    cmd_args args = {transport, port, epoll_enabled};
    return args;
}

int start_tcp_server(int sockfd) {
    struct sockaddr_in client_addr;
    socklen_t client_len = sizeof(client_addr);
    char buffer[BUFFER_SIZE];

    if (listen(sockfd, 5) == -1) {
        return -1;
    }

    while (1) {
        // sockaddr_in is a specific implementation of the more general sockaddr structure
        int client_fd = accept(sockfd, (struct sockaddr*)&client_addr, &client_len);
        if (client_fd == -1) {
            perror("error accepting connection");
            continue;
        }

        printf(
            "connection from %s:%d\n",
            inet_ntoa(client_addr.sin_addr),
            ntohs(client_addr.sin_port)
        );

        while (1) {
            ssize_t bytes_read = recv(client_fd, buffer, BUFFER_SIZE - 1, 0);
            if (bytes_read <= 0) {
                break;
            }
            buffer[bytes_read] = '\0';
            printf("received: %s", buffer);
            if (send(client_fd, buffer, bytes_read, 0) == -1) {
                perror("error sending data");
                break;
            }
        }
        close(client_fd);
    }
}

int start_tcp_server_with_epoll(int sockfd) {
    struct sockaddr_in client_addr;
    socklen_t client_len = sizeof(client_addr);
    char buffer[BUFFER_SIZE];

    if (listen(sockfd, 5) == -1) {
        return -1;
    }

    // get flag and set to non-blocking mode
    int flags = fcntl(sockfd, F_GETFL, 0);
    fcntl(sockfd, F_SETFL, flags | O_NONBLOCK);

    int epfd = epoll_create1(0);
    if (epfd == -1) {
        return -1;
    }

    struct epoll_event ev, events[MAX_EVENTS];
    ev.events = EPOLLIN;
    ev.data.fd = sockfd;

    // not sure why this requires the sockfd to be passed again when ev has it
    if (epoll_ctl(epfd, EPOLL_CTL_ADD, sockfd, &ev) == -1) {
        perror("error adding listening socket to epoll");
        close(epfd);
        return -1;
    }
    while (1) {
        // https://man7.org/linux/man-pages/man2/epoll_wait.2.html
        // returns the number of file descriptors
        // ready for the requested I/O operation
        int nfds = epoll_wait(epfd, events, MAX_EVENTS, -1);
        if (nfds == -1) {
            perror("error in epoll_wait");
            continue;
        }

        for (int i = 0; i < nfds; i++) {
            if (events[i].data.fd == sockfd) {
                // new connection
                int client_fd = accept(sockfd, (struct sockaddr*)&client_addr, &client_len);
                if (client_fd == -1) {
                    // handle with errno
                }
                printf(
                    "connection from %s:%d\n",
                    inet_ntoa(client_addr.sin_addr),
                    ntohs(client_addr.sin_port)
                );

                // get and set client fd to non blocking
                flags = fcntl(client_fd, F_GETFL, 0);
                fcntl(client_fd, F_SETFL, flags | O_NONBLOCK);

                // EPOLLET for edge-triggered mode
                ev.events = EPOLLIN | EPOLLET;
                ev.data.fd = client_fd;
                if (epoll_ctl(epfd, EPOLL_CTL_ADD, client_fd, &ev) == -1) {
                    perror("error adding client socket to epoll");
                    close(client_fd);
                    continue;
                }
            } else {
                int client_fd = events[i].data.fd;
                int bytes_read = recv(client_fd, buffer, BUFFER_SIZE - 1, 0);
                if (bytes_read == 0) {
                    printf("client disconnected\n");
                    close(client_fd);
                } else if (bytes_read < 0) {
                    if (errno != EAGAIN && errno != EWOULDBLOCK) {
                        perror("error receiving data");
                        close(client_fd);
                    }
                } else {
                    buffer[bytes_read] = '\0';
                    printf("received: %s", buffer);

                    if (send(client_fd, buffer, bytes_read, 0) == -1) {
                        perror("error sending data");
                        close(client_fd);
                    }
                }
            }
        }
    }
}

int start_udp_server(int sockfd) {
    char buffer[BUFFER_SIZE];
    struct sockaddr_in client_addr;
    socklen_t client_len = sizeof(client_addr);

    while (1) {
        ssize_t bytes_read = recvfrom(
            sockfd,
            buffer,
            BUFFER_SIZE - 1,
            0,
            (struct sockaddr*)&client_addr,
            &client_len
        );
        if (bytes_read < 0) {
            perror("error receiving data");
            continue;
        }
        buffer[bytes_read] = '\0';
        printf(
            "received from %s:%d: %s\n",
            inet_ntoa(client_addr.sin_addr),
            ntohs(client_addr.sin_port),
            buffer
        );
        if (sendto(sockfd, buffer, bytes_read, 0, (struct sockaddr*)&client_addr, client_len) < 0) {
            perror("error sending data");
        }
    }
}

int main(int argc, char* argv[]) {
    int sockfd;
    struct sockaddr_in server_addr;

    cmd_args args = parse_args(argc, argv);
    if (strcasecmp(args.transport, "tcp") == 0) {
        sockfd = socket(AF_INET, SOCK_STREAM, 0);
    } else {
        sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    }

    if (sockfd < 0) {
        perror("error creating socket");
        exit(1);
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(args.port);

    if (bind(sockfd, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        perror("error binding socket");
        close(sockfd);
        exit(1);
    }

    printf("echo server started on port %d using %s\n", args.port, args.transport);

    if (strcasecmp(args.transport, "tcp") == 0) {
        if (args.epoll_enabled) {
            if (start_tcp_server_with_epoll(sockfd) == -1) {
                perror("");
                return -1;
            };
        } else {
            if (start_tcp_server(sockfd) == -1) {
                perror("");
                return -1;
            };
        }

    } else {
        if (start_udp_server(sockfd) == -1) {
            perror("");
            return -1;
        };
    }
    close(sockfd);
    return 0;
}
