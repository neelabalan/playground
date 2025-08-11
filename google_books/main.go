package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"net/url"
	"os"
	"reflect"
	"strconv"
)

type CmdArgs struct {
	Isbn   string `arg:"isbn" default:"" description:"International standard book number"`
	Search string `arg:"search" default:"" description:"Search term"`
}

func createFlagArgs(args any) any {
	t := reflect.TypeOf(args)
	commandLineArgs := reflect.New(t).Elem()

	for i := 0; i < t.NumField(); i++ {
		field := t.Field(i)
		cmdTag := field.Tag.Get("arg")
		defaultTag := field.Tag.Get("default")
		description := field.Tag.Get("description")

		switch field.Type.Name() {
		case "string":
			flag.StringVar(commandLineArgs.Field(i).Addr().Interface().(*string), cmdTag, defaultTag, description)
		case "int":
			val, err := strconv.Atoi(defaultTag)
			if err == nil {
				slog.Error("Check the default tag for ", slog.Any("type", field))
			}
			flag.IntVar(commandLineArgs.Field(i).Addr().Interface().(*int), cmdTag, val, description)
		default:
			slog.Warn("Cannot parse at ", slog.Any("type", field))
		}
	}
	flag.Parse()
	return commandLineArgs.Interface()

}

func logLevelMap(level string) slog.Level {
	switch level {
	case "DEBUG":
		return slog.LevelDebug
	case "INFO":
		return slog.LevelInfo
	case "WARN":
		return slog.LevelWarn
	case "ERROR":
		return slog.LevelError
	default:
		return slog.LevelInfo
	}
}

func main() {
	// isbn := flag.String("isbn", "", "International standard book number")
	// search := flag.String("search", "", "search term")
	// client := &http.Client{
	// 	Timeout: 30 * time.Second,
	// }

	slog.SetLogLoggerLevel(logLevelMap(os.Getenv("LOG_LEVEL")))

	args := createFlagArgs(CmdArgs{}).(CmdArgs)

	resp, err := http.Get(fmt.Sprintf("https://www.googleapis.com/books/v1/volumes?q=%s", url.QueryEscape(args.Search)))
	slog.Debug(resp.Request.URL.String())
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		panic(err)
	}
	var jsonBody map[string]any
	json.Unmarshal([]byte(body), &jsonBody)
	marshaled, _ := json.MarshalIndent(jsonBody, "", "    ")
	slog.Debug(string(marshaled))

	items := jsonBody["items"].([]any)
	for _, item := range items {
		volumeInfo := item.(map[string]any)["volumeInfo"].(map[string]any)
		fmt.Println("\n==========")
		fmt.Println("Title: ", volumeInfo["title"])
		fmt.Println("Publisher: ", volumeInfo["publisher"])
		fmt.Println("Published Date: ", volumeInfo["publishedDate"])
		fmt.Println("Page count: ", volumeInfo["pageCount"])
		fmt.Println("Language: ", volumeInfo["language"])
	}
}
