package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"
)

func run_async() {
	// A slice of sample websites
	dat, _ := os.ReadFile("../links.copy.txt")
	urls := strings.Split(strings.TrimSpace(string(dat)), "\n")

	// Split the URLs into batches of size 100
	batchSize := 25
	batches := make([][]string, 0, len(urls)/batchSize+1)
	for i := 0; i < len(urls); i += batchSize {
		end := i + batchSize
		if end > len(urls) {
			end = len(urls)
		}
		batches = append(batches, urls[i:end])
	}
	println("total batches: ", len(batches))

	c := make(chan urlStatus)
	var wg sync.WaitGroup

	for _, batch := range batches {
		wg.Add(1)
		go checkUrls(batch, c, &wg)
	}

	go func() {
		wg.Wait()
		close(c)
	}()

	var result []urlStatus
	for status := range c {
		result = append(result, status)
		fmt.Println(status)
	}

	jsonResult, _ := json.MarshalIndent(result, "", "    ")
	_ = os.WriteFile("result_go_async.json", jsonResult, 0644)
	fmt.Println("json result written")
}

// checks and prints a message if a website is up or down
func checkUrls(urls []string, c chan urlStatus, wg *sync.WaitGroup) {
	defer wg.Done()

	client := &http.Client{Timeout: 10 * time.Second}

	for _, url := range urls {
		req, _ := http.NewRequest("GET", url, nil)
		response, err := client.Do(req)
		if err != nil {
			c <- urlStatus{url, err.Error()}
			continue
		}
		defer response.Body.Close()
		c <- urlStatus{url, strconv.Itoa(response.StatusCode)}
	}
	println("completed processing batch requests")
}
