package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log/slog"
	"os"
	"reflect"
	"strconv"
)

type Config struct {
	Pipelines    []Pipeline `json:"pipelines"`
	Worker       int        `json:"worker"`
	DataStore    string     `json:"data_store"`
	SlackChannel string     `json:"slack_channel"`
}

type Pipeline struct {
	URL       string `json:"url"`
	Frequency int    `json:"frequency"`
}

type CmdArgs struct {
	Config string `arg:"config" default:"" description:"The configuration file where pipelines are listed to collect data"`
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

func main() {
	logDebugMode := os.Getenv("DEBUG")
	if logDebugMode == "TRUE" || logDebugMode == "1" {
		slog.SetLogLoggerLevel(slog.LevelDebug)
	} else {
		slog.SetLogLoggerLevel(slog.LevelInfo)
	}
	slog.Debug("hello from debug")
	slog.Info("hello from info")
	args := createFlagArgs(CmdArgs{}).(CmdArgs)

	configPath := args.Config
	if configPath == "" {
		configPath = "config.json"
	}

	file, err := os.Open(configPath)
	if err != nil {
		slog.Error("Failed to open config file", slog.String("path", configPath), slog.Any("error", err))
		os.Exit(1)
	}
	defer file.Close()

	var config Config
	decoder := json.NewDecoder(file)
	if err := decoder.Decode(&config); err != nil {
		slog.Error("Failed to decode config file", slog.Any("error", err))
		os.Exit(1)
	}

	fmt.Printf("Loaded config: %+v\n", config)
}
