package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"
)

func run_seq() {
	// A slice of sample websites
	dat, _ := os.ReadFile("../links.copy.txt")
	urls := strings.Split(strings.TrimSpace(string(dat)), "\n")

	result := make([]urlStatus, len(urls))
	for i, url := range urls {
		println("checking ", url)
		result[i] = checkUrl(url)
	}

	jsonResult, _ := json.MarshalIndent(result, "", "    ")
	_ = os.WriteFile("result_go_sync.json", jsonResult, 0644)
	fmt.Println("json result written")
}

// checks and prints a message if a website is up or down
func checkUrl(url string) urlStatus {
	// defer wg.Done()
	client := http.Client{Timeout: 10 * time.Second}
	response, err := client.Get(url)
	var status urlStatus
	if err != nil {
		fmt.Println(url, "is down")
		if response != nil {
			status = urlStatus{url, strconv.Itoa(response.StatusCode)}
		} else {
			status = urlStatus{url, "Errored out"}
		}
	} else {
		status = urlStatus{url, strconv.Itoa(response.StatusCode)}
	}
	return status
}
