package main

import (
	"fmt"
	"log/slog"
	"os"
	"sync"

	slogmulti "github.com/samber/slog-multi"
)

func main() {
	// whiteOnGreen := PrintConfig{FgColor: Reset, BgColor: BgGreen, Bold: true}
	// redOnBlue := PrintConfig{FgColor: FgRed, BgColor: BgBlue, Bold: false}
	// whiteOnGreen.Println("INFO")
	// println()

	// println(redOnBlue.ColorFmt("hi there", 123))
	// slog.Info(redOnBlue.ColorFmt("this is a logging stuff"))

	consoleLogHandler := &ConsoleHandler{
		opts: ConsoleHandlerOptions{
			SlogOpts: slog.HandlerOptions{
				AddSource: true,
				Level:     slog.LevelDebug,
			},
			UseColor: true,
		},
		mu: &sync.Mutex{},
		w:  os.Stderr,
	}
	file, err := os.OpenFile("logfile.log", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
	if err != nil {
		fmt.Printf("Failed to open log file: %v\n", err)
		return
	}
	defer file.Close()
	fileLogHandler := &ConsoleHandler{
		opts: ConsoleHandlerOptions{
			SlogOpts: slog.HandlerOptions{
				AddSource: true,
				Level:     slog.LevelDebug,
			},
			UseColor: false,
		},
		mu: &sync.Mutex{},
		w:  file,
	}
	multiHandler := slogmulti.Fanout(
		consoleLogHandler,
		fileLogHandler,
	)

	logger := slog.New(multiHandler)
	logger.Debug("This is debug")
	logger.Info("This is info")
	logger.Error("This is error")
	logger.Warn("This is warn")
}
