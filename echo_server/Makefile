CC = gcc
CFLAGS = -Wall -Wextra -Werror -std=c11

SRC_DIR = .
BIN_DIR = bin

TARGET = server

SRC = $(SRC_DIR)/server.c

all: $(BIN_DIR)/$(TARGET)

$(BIN_DIR)/$(TARGET): $(SRC) | $(BIN_DIR)
	@mkdir -p $(BIN_DIR)
	$(CC) $(CFLAGS) -o $@ $<

clean: rm -f $(BIN_DIR)/$(TARGET)

.PHONY: all clean
