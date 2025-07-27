#include <arpa/inet.h>
#include <getopt.h>
#include <netinet/in.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>  // for memset
#include <strings.h>
#include <sys/socket.h>
#include <unistd.h>

#define BUFFER_SIZE 1024
#define DEFAULT_PORT 8080

void print_usage(const char* prog_name) {
    printf("Usage: %s [-t|-u] [-p port]\n", prog_name);
    printf("Options:\n");
    printf("  -t              Use TCP protocol (default)\n");
    printf("  -u              Use UDP protocol\n");
    printf("  -p port         Specify port number (default: %d)\n", DEFAULT_PORT);
    printf("  -h              Show this help message\n");
}

int start_tcp_server(int sockfd) {
    struct sockaddr_in client_addr;
    socklen_t client_len = sizeof(client_addr);
    char buffer[BUFFER_SIZE];

    if (listen(sockfd, 5) == -1) {
        return -1;
    }

    while (1) {
        int client_fd = accept(sockfd, (struct sockaddr*)&client_addr, &client_len);
        if (client_fd == -1) {
            perror("Error accepting connection");
            continue;
        }

        printf(
            "Connection from %s:%d\n",
            inet_ntoa(client_addr.sin_addr),
            ntohs(client_addr.sin_port)
        );

        while (1) {
            ssize_t bytes_read = recv(client_fd, buffer, BUFFER_SIZE - 1, 0);
            if (bytes_read <= 0) {
                break;
            }
            buffer[bytes_read] = '\0';
            printf("Received: %s", buffer);
            if (send(client_fd, buffer, bytes_read, 0) == -1) {
                perror("Error sending data");
                break;
            }
        }
        close(client_fd);
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
            perror("Error receiving data");
            continue;
        }
        buffer[bytes_read] = '\0';
        printf(
            "Received from %s:%d: %s\n",
            inet_ntoa(client_addr.sin_addr),
            ntohs(client_addr.sin_port),
            buffer
        );
        if (sendto(sockfd, buffer, bytes_read, 0, (struct sockaddr*)&client_addr, client_len) < 0) {
            perror("Error sending data");
        }
    }
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
} cmd_args;

cmd_args parse_args(int argc, char* argv[]) {
    int opt;
    int option_index = 0;
    static struct option long_options[] = {
        {"transport", required_argument, 0, 't'},
        {"port", required_argument, 0, 'p'},
        {"help", no_argument, 0, 'h'},
        {0, 0, 0, 0}
    };
    unsigned int port = 8080;
    char* transport = "tcp";

    while ((opt = getopt_long(argc, argv, "", long_options, &option_index)) != -1) {
        switch (opt) {
        case 't':
            transport = optarg;
            if (strcasecmp(transport, "tcp") != 0 && strcasecmp(transport, "udp") != 0) {
                error_message("Invalid trasport protocol. Use 'tcp' or 'udp'");
                print_usage(argv[0]);
                exit(EXIT_FAILURE);
            }
            break;
        case 'p':
            port = atoi(optarg);
            if (port < 1) {
                error_message("Port value cannot be less than 0");
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
    cmd_args args = {transport, port};
    return args;
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
        perror("Error creating socket");
        exit(1);
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(args.port);

    if (bind(sockfd, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        perror("Error binding socket");
        close(sockfd);
        exit(1);
    }

    printf("Echo server started on port %d using %s\n", args.port, args.transport);

    if (strcasecmp(args.transport, "tcp") == 0) {
        if (start_tcp_server(sockfd) == -1) {
            perror("");
            return -1;
        };
    } else {
        if (start_udp_server(sockfd) == -1) {
            perror("");
            return -1;
        };
    }
    close(sockfd);
    return 0;
}
