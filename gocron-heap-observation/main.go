package main

import (
	"encoding/csv"
	"fmt"
	"os"
	"os/signal"
	"runtime"
	"strconv"
	"syscall"
	"time"

	"github.com/go-co-op/gocron/v2"
)

func main() {
	s, err := gocron.NewScheduler()
	if err != nil {
	}
	// duration := flag.Int("duration", 10, "duration between runs")
	// flag.Parse()

	for _, t := range []struct {
		Str string
		Dur int
	}{
		{"hello", 5},
		{"test", 10},
		{"world", 15},
		{"metrics", 8},
		{"backup", 30},
		{"cleanup", 20},
		{"health", 17},
		{"report", 13},
	} {
		j, err := s.NewJob(
			gocron.DurationJob(
				time.Duration(t.Dur)*time.Second,
			),
			gocron.NewTask(
				func(a string, b int) {
					fmt.Println(a, b)
				},
				t.Str,
				t.Dur,
			),
		)
		if err != nil {

		}
		fmt.Println(j.ID())
	}
	s.Start()

	go func() {
		var m runtime.MemStats
		ticker := time.NewTicker(5 * time.Second)
		gcTicker := time.NewTicker(120 * time.Second)

		file, err := os.OpenFile("memory_stats.csv", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
		if err != nil {
			fmt.Printf("error opening CSV file: %v\n", err)
			return
		}
		defer file.Close()

		writer := csv.NewWriter(file)
		defer writer.Flush()

		if stat, _ := file.Stat(); stat.Size() == 0 {
			writer.Write([]string{"timestamp", "heap_alloc_kb", "heap_objects", "gc_cycles", "sys_kb"})
			writer.Flush()
		}
		for {
			select {
			case <-ticker.C:
				runtime.ReadMemStats(&m)
				timestamp := time.Now().Format("2006-01-02 15:04:05")

				record := []string{
					timestamp,
					strconv.FormatUint(m.HeapAlloc/1024, 10),
					strconv.FormatUint(m.HeapObjects, 10),
					strconv.FormatUint(uint64(m.NumGC), 10),
					strconv.FormatUint(m.Sys/1024, 10),
				}
				writer.Write(record)
				writer.Flush()
				fmt.Printf("heap alloc: %d KB, heap objects: %d, gc cycles: %d, sys: %d KB\n", m.HeapAlloc/1024, m.HeapObjects, m.NumGC, m.Sys/1024)
			case <-gcTicker.C:
				fmt.Printf("forcing gc")
				runtime.GC()
			}
		}
	}()

	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	fmt.Println("scheduler running... press ctrl+c to stop")
	<-c // block until signal received
	fmt.Println("shutting down scheduler...")
	err = s.Shutdown()
	if err != nil {
	}
}
