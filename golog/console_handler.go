package main

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"log/slog"
	"os"
	"path/filepath"
	"runtime"
	"sync"
	"time"
)

// Text formatting constants
const (
	Bold      = "\033[1m"
	Underline = "\033[4m"
	Italic    = "\033[3m"
	Reset     = "\033[0m"
)

// Foreground colors
const (
	FgRed    = "\033[31m"
	FgGreen  = "\033[32m"
	FgYellow = "\033[33m"
	FgBlue   = "\033[34m"
	FgPurple = "\033[35m"
	FgCyan   = "\033[36m"
	FgGray   = "\033[37m"
	FgWhite  = "\033[97m"
)

// Background colors
const (
	BgRed     = "\033[41m"
	BgGreen   = "\033[42m"
	BgYellow  = "\033[43m"
	BgBlue    = "\033[44m"
	BgPurple  = "\033[45m"
	BgCyan    = "\033[46m"
	BgGray    = "\033[47m"
	BgDefault = "\033[49m"
)

// PrintConfig holds the configuration for text printing
type PrintConfig struct {
	FgColor   string
	BgColor   string
	Bold      bool
	Underline bool
	Italic    bool
}

func (cfg PrintConfig) Print(text string) {
	if cfg.Bold {
		fmt.Print(Bold)
	}
	if cfg.Underline {
		fmt.Print(Underline)
	}
	if cfg.Italic {
		fmt.Print(Italic)
	}
	fmt.Print(cfg.FgColor)
	fmt.Print(cfg.BgColor)
	fmt.Print(text)
	fmt.Print(Reset)

}

func (cfg PrintConfig) Println(text string) {
	cfg.Print(text)
	fmt.Println()
}

func (cfg PrintConfig) ColorFmt(format string, a ...interface{}) string {
	text := fmt.Sprintf(format, a...)
	var result string
	if cfg.Bold {
		result += Bold
	}
	if cfg.Underline {
		result += Underline
	}
	if cfg.Italic {
		result += Italic
	}
	result += cfg.FgColor
	result += cfg.BgColor
	result += text
	result += Reset
	return result
}

var (
	GreenOnWhite  = PrintConfig{FgColor: FgGreen, BgColor: BgDefault}
	RedOnWhite    = PrintConfig{FgColor: FgRed, BgColor: BgDefault}
	BlueOnWhite   = PrintConfig{FgColor: FgBlue, BgColor: BgDefault}
	YellowOnWhite = PrintConfig{FgColor: FgYellow, BgColor: BgDefault}
)

var (
	levelToColor = map[string]PrintConfig{
		slog.LevelDebug.String(): BlueOnWhite,
		slog.LevelInfo.String():  GreenOnWhite,
		slog.LevelWarn.String():  YellowOnWhite,
		slog.LevelError.String(): RedOnWhite,
	}
	unknownLevelColor = RedOnWhite
)

type ConsoleHandlerOptions struct {
	SlogOpts slog.HandlerOptions
	UseColor bool
}

type ConsoleHandler struct {
	opts ConsoleHandlerOptions
	goas []groupOrAttrs

	mu *sync.Mutex
	w  io.Writer
}

func New(out io.Writer, opts *ConsoleHandlerOptions) *ConsoleHandler {
	return &ConsoleHandler{w: out, mu: &sync.Mutex{}}
}

func (h *ConsoleHandler) Enabled(ctx context.Context, level slog.Level) bool {
	return level >= h.opts.SlogOpts.Level.Level()
}

func (h *ConsoleHandler) Handle(ctx context.Context, r slog.Record) error {
	var buf bytes.Buffer

	buf.WriteString(r.Time.Format(time.RFC3339))
	buf.WriteString(" ")

	if r.PC != 0 {
		fs := runtime.CallersFrames([]uintptr{r.PC})
		f, _ := fs.Next()
		// buf.WriteString(slog.SourceKey)
		cwd, err := os.Getwd()
		if err != nil {
			return err
		}

		relativePath, err := filepath.Rel(cwd, f.File)
		if err != nil {
			return err
		}

		buf.WriteString(fmt.Sprintf("%s:%d", relativePath, f.Line))
	}

	buf.WriteString("\t")

	level := r.Level.String()
	if h.opts.UseColor {
		level = levelToColor[level].ColorFmt(level)
	}
	buf.WriteString(level)
	buf.WriteString("\t")

	buf.WriteString(r.Message)
	buf.WriteString("\n")

	h.mu.Lock()
	defer h.mu.Unlock()
	_, err := h.w.Write(buf.Bytes())
	if err != nil {
		return err
	}

	return err
}

type groupOrAttrs struct {
	group string      // group name if non-empty
	attrs []slog.Attr // attrs if non-empty
}

func (h *ConsoleHandler) withGroupOrAttrs(goa groupOrAttrs) *ConsoleHandler {
	h2 := *h
	h2.goas = make([]groupOrAttrs, len(h.goas)+1)
	copy(h2.goas, h.goas)
	h2.goas[len(h2.goas)-1] = goa
	return &h2
}
func (h *ConsoleHandler) WithGroup(name string) slog.Handler {
	if name == "" {
		return h
	}
	return h.withGroupOrAttrs(groupOrAttrs{group: name})
}
func (h *ConsoleHandler) WithAttrs(attrs []slog.Attr) slog.Handler {
	if len(attrs) == 0 {
		return h
	}
	return h.withGroupOrAttrs(groupOrAttrs{attrs: attrs})
}
