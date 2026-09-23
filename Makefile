# shieldHer Makefile

CC = gcc
CFLAGS = -Wall -Wextra -std=c99
TARGET = analyzer
SRCS = analyzer.c
OBJS = $(SRCS:.c=.o)

.PHONY: all build clean run

all: build

build: $(TARGET)

$(TARGET): $(SRCS)
	$(CC) $(CFLAGS) -o $@ $^

run: $(TARGET)
	./$(TARGET)

clean:
	rm -f $(TARGET) $(OBJS)
