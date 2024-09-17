package main

import (
	"context"
	"flag"
	"fmt"
	"log/slog"
	"math/rand"
	"os"
	"time"

	slogmulti "github.com/samber/slog-multi"

	"github.com/go-faker/faker/v4"
	"github.com/google/uuid"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

type Address struct {
	Street  string `bson:"street"`
	City    string `bson:"city"`
	State   string `bson:"state"`
	ZipCode string `bson:"zip_code"`
}

type Document struct {
	ID        string  `bson:"_id"`
	Name      string  `bson:"name"`
	Email     string  `bson:"email"`
	Age       int     `bson:"age"`
	Address   Address `bson:"address"`
	CreatedAt string  `bson:"created_at"`
	IsActive  bool    `bson:"is_active"`
}

type DataGenerator struct{}

func (dg *DataGenerator) generateDocument(id string) Document {
	address := faker.GetRealAddress()
	return Document{
		ID:    id,
		Name:  faker.Name(),
		Email: faker.Email(),
		Age:   rand.Intn(63) + 18, // Age between 18 and 80

		Address: Address{
			Street:  address.Address,
			City:    address.City,
			State:   address.State,
			ZipCode: address.PostalCode,
		},
		CreatedAt: time.Now().Format(time.RFC3339),
		IsActive:  rand.Intn(2) == 1,
	}
}

func (dg *DataGenerator) generateBulkDocuments(numDocs int) []interface{} {
	documents := make([]interface{}, numDocs)
	for i := 0; i < numDocs; i++ {
		documents[i] = dg.generateDocument(uuid.New().String())
	}
	return documents
}

type Operation interface {
	Execute()
}

type BaseOperation struct {
	collection    *mongo.Collection
	logger        *slog.Logger
	bulk          bool
	numDocs       int
	interval      float64
	continuous    bool
	dataGenerator *DataGenerator
}

type WriteOperation struct {
	*BaseOperation
}

func (op *WriteOperation) Execute() {
	if op.continuous {
		ticker := time.NewTicker(time.Duration(op.interval * float64(time.Second)))
		defer ticker.Stop()
		for {
			op.executeOnce()
			<-ticker.C
		}
	} else {
		op.executeOnce()
	}
}

func (op *WriteOperation) executeOnce() {
	ctx := context.Background()
	if op.bulk {
		documents := op.dataGenerator.generateBulkDocuments(op.numDocs)
		op.logger.Info("Starting bulk insert", "num_documents", len(documents))
		startTime := time.Now()
		_, err := op.collection.InsertMany(ctx, documents)
		if err != nil {
			op.logger.Error("Error during bulk insert", "error", err)
			return
		}
		duration := time.Since(startTime)
		op.logger.Info("Bulk insert completed", "duration_seconds", duration.Seconds())
	} else {
		doc := op.dataGenerator.generateDocument(uuid.New().String())
		op.logger.Info("Inserting single document")
		startTime := time.Now()
		_, err := op.collection.InsertOne(ctx, doc)
		if err != nil {
			op.logger.Error("Error during single insert", "error", err)
			return
		}
		duration := time.Since(startTime)
		op.logger.Info("Single insert completed", "duration_seconds", duration.Seconds())
	}
}

func main() {
	mongoURI := flag.String("mongo-uri", "mongodb://localhost:27017/", "MongoDB URI")
	databaseName := flag.String("database", "test_db", "Database name")
	collectionName := flag.String("collection", "test_collection", "Collection name")
	operationType := flag.String("operation", "", "Operation to perform: write, delete, update")
	bulk := flag.Bool("bulk", false, "Perform bulk operations")
	numDocs := flag.Int("num-docs", 1000, "Number of documents to process")
	interval := flag.Float64("interval", 0.0, "Interval between operations in seconds")
	continuous := flag.Bool("continuous", false, "Run operations continuously")
	flag.Parse()

	if *operationType == "" {
		fmt.Println("Operation type is required. Use --operation=write|delete|update")
		os.Exit(1)
	}

	logFile, err := os.OpenFile("logs/data_operations.log", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
	if err != nil {
		slog.Error("Failed to open log file: %v", err)
	}
	defer logFile.Close()
	// Logging setup
	logger := slog.New(
		slogmulti.Fanout(
			slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{}), // pass to first handler: logstash over tcp
			slog.NewTextHandler(logFile, &slog.HandlerOptions{}),   // then to second handler: stderr
		),
	)

	clientOptions := options.Client().ApplyURI(*mongoURI)
	client, err := mongo.Connect(context.TODO(), clientOptions)
	if err != nil {
		logger.Error(fmt.Sprintf("Failed to connect to MongoDB: %v", err))
	}
	defer client.Disconnect(context.TODO())

	collection := client.Database(*databaseName).Collection(*collectionName)

	var dataGenerator *DataGenerator
	if *operationType == "write" {
		dataGenerator = &DataGenerator{}
	}

	baseOp := &BaseOperation{
		collection:    collection,
		logger:        logger,
		bulk:          *bulk,
		numDocs:       *numDocs,
		interval:      *interval,
		continuous:    *continuous,
		dataGenerator: dataGenerator,
	}

	var operation Operation
	switch *operationType {
	case "write":
		operation = &WriteOperation{BaseOperation: baseOp}
	// case "delete":
	// 	operation = &DeleteOperation{BaseOperation: baseOp}
	// case "update":
	// 	operation = &UpdateOperation{BaseOperation: baseOp}
	default:
		logger.Error(fmt.Sprintf("Unknown operation type: %s", *operationType))
	}

	operation.Execute()
}
