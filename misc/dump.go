package main

import (
	"compress/gzip"
	"context"
	"encoding/json"
	"fmt"
	"math"
	"os"
	"sync"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
	"go.mongodb.org/mongo-driver/mongo/readpref"
)

func processData(wg *sync.WaitGroup, idList []string, collection *mongo.Collection, uniqueFileId int) {
	defer wg.Done()

	// ctx := context.Background()

	file, _ := os.Create(fmt.Sprintf("%d-file.json.gz", uniqueFileId))
	defer file.Close()

	gzipWriter := gzip.NewWriter(file)
	defer gzipWriter.Close()

	for _, idStr := range idList {
		objectId, _ := primitive.ObjectIDFromHex(idStr)
		var document bson.M
		err := collection.FindOne(context.TODO(), bson.M{"_id": objectId}).Decode(&document)
		if err != nil {
			fmt.Println("Error finding document:", err)
			continue
		}

		jsonData, err := json.Marshal(document)
		if err != nil {
			fmt.Println("Error marshaling document:", err)
			continue
		}

		if _, err := gzipWriter.Write(append(jsonData, '\n')); err != nil {
			fmt.Println("Error writing to gzip file:", err)
			continue
		}
	}
	println("Completed writing to jsonfile")

}

func chunkList(lst []string, chunkSize int) [][]string {
	start := 0
	stop := len(lst)
	var chunks [][]string
	for i := start; i < stop; i += chunkSize {
		chunks = append(chunks, lst[i:i+chunkSize])

	}
	return chunks

}

func main() {
	fileBytes, _ := os.ReadFile("result.json")
	var data []string
	err := json.Unmarshal(fileBytes, &data)
	if err != nil {
		println("error reading json file")
	}

	clientCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	ctx := context.Background()
	defer cancel()

	client, err := mongo.Connect(clientCtx, options.Client().ApplyURI("mongodb://localhost:27017"))
	if err != nil {
		fmt.Println("Error connecting to MongoDB:", err)
		return
	}
	defer client.Disconnect(ctx)

	if err := client.Ping(ctx, readpref.Primary()); err != nil {
		fmt.Println("Error pinging MongoDB:", err)
		return
	}
	workers := 4.0
	chunkSize := int(math.Ceil(float64(len(data)) / workers))
	println("Chunk size - ", chunkSize)
	chunks := chunkList(data, chunkSize)

	collection := client.Database("analytics").Collection("gh_archive")
	// objectId, _ := primitive.ObjectIDFromHex("66c4cb33c5825beaf45abe61")
	// println(collection.FindOne(context.TODO(), bson.M{"_id": objectId}))
	var wg sync.WaitGroup
	for idx, chunk := range chunks {
		wg.Add(1)
		go processData(&wg, chunk, collection, idx)
	}
	wg.Wait() // Wait for all goroutines to complete

}
