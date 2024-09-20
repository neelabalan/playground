package main

import (
	"compress/gzip"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log/slog"
	"os"
	"sync"

	"github.com/google/uuid"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

type Task struct {
	ID        int
	Documents []bson.M
}

type WorkerPool struct {
	maxWorkers int
	tasks      chan Task
	wg         sync.WaitGroup
	ctx        context.Context
	cancel     context.CancelFunc
}

func NewWorkerPool(maxWorkers int) *WorkerPool {
	ctx, cancel := context.WithCancel(context.Background())
	return &WorkerPool{
		maxWorkers: maxWorkers,
		tasks:      make(chan Task),
		ctx:        ctx,
		cancel:     cancel,
	}
}

func (wp *WorkerPool) Run(taskFunc func(Task)) {
	wp.wg.Add(wp.maxWorkers)
	for i := 0; i < wp.maxWorkers; i++ {
		go wp.worker(i, taskFunc)
	}
}

func (wp *WorkerPool) worker(id int, taskFunc func(Task)) {
	defer wp.wg.Done()
	for {
		select {
		case <-wp.ctx.Done():
			fmt.Printf("Worker %d stopping.\n", id)
			return
		case task, ok := <-wp.tasks:
			if !ok {
				fmt.Printf("Worker %d stopping, task channel closed.\n", id)
				return
			}
			fmt.Printf("Worker %d picked up task %d\n", id, task.ID)
			taskFunc(task)
		}
	}
}

func (wp *WorkerPool) AddTask(task Task) {
	wp.tasks <- task
}

func (wp *WorkerPool) Stop() {
	wp.cancel()
	close(wp.tasks)
	wp.wg.Wait()
}

func dumpData(task Task) {
	file, _ := os.Create(fmt.Sprintf("%s.json.gz", uuid.New().String()))
	defer file.Close()

	gzipWriter := gzip.NewWriter(file)
	defer gzipWriter.Close()

	for _, doc := range task.Documents {
		// fmt.Printf("document - %v\n", doc)
		jsonData, err := json.Marshal(doc)
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
func main() {
	mongoURI := flag.String("mongo-uri", "mongodb://localhost:27017/", "MongoDB URI")
	databaseName := flag.String("database", "test_db", "Database name")
	collectionName := flag.String("collection", "test_collection", "Collection name")
	maxDocCount := flag.Int("doc-count", 1000, "Maximum number of documents that the worker can dump at a time")
	maxWorkers := flag.Int("workers", 10, "Maximum number of workers to do the job")
	flag.Parse()

	clientOptions := options.Client().ApplyURI(*mongoURI)
	client, err := mongo.Connect(context.TODO(), clientOptions)
	if err != nil {
		slog.Error("Error connecting to mongodb")
		return
	}
	collection := client.Database(*databaseName).Collection(*collectionName)
	stream, _ := collection.Watch(context.TODO(), mongo.Pipeline{})

	// more stuff for worker
	wp := NewWorkerPool(*maxWorkers)
	wp.Run(dumpData)

	// second part for change stream listening
	defer stream.Close(context.TODO())
	count := 0
	batch := 0
	var documents []bson.M

	go func() {
		for stream.Next(context.TODO()) {
			var data bson.M
			if err := stream.Decode(&data); err != nil {
				panic(err)
			}
			documents = append(documents, data)
			count += 1
			if count == *maxDocCount {
				task := Task{ID: batch, Documents: documents}
				fmt.Printf("Adding task %d\n", task.ID)
				wp.AddTask(task)
				count = 0
				batch += 1
				documents = nil
			}

		}
		wp.Stop()
	}()
	wp.wg.Wait()
	fmt.Println("ALl tasks processing complete")

}
