package main

import (
	"context"
	"flag"
	"fmt"
	"log/slog"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

func getLatestTimestamp(oplog *mongo.Collection) primitive.Timestamp {
	findOptions := options.FindOne().SetSort(bson.D{{Key: "$natural", Value: -1}})

	var result bson.M
	err := oplog.FindOne(context.Background(), bson.D{}, findOptions).Decode(&result)
	if err != nil {
		return primitive.Timestamp{T: 0, I: 0}
	}

	tsValue := result["ts"]
	ts, _ := tsValue.(primitive.Timestamp)
	return ts
}

type OplogTailer struct {
	database   string
	client     *mongo.Client
	collection string
	timestamp  primitive.Timestamp
	namespace  string
	oplog      *mongo.Collection
}

func (oplogTailer *OplogTailer) Init(mongoUri string, database string, collection string) {
	oplogTailer.database = database
	oplogTailer.collection = collection
	clientOptions := options.Client().ApplyURI(mongoUri)
	client, err := mongo.Connect(context.TODO(), clientOptions)

	if err != nil {
		slog.Error(fmt.Sprintf("Failed to connect to MongoDB: %v", err))
		return
	}
	oplogTailer.client = client
	// defer client.Disconnect(ctx)
	// setting oplog collection
	oplogTailer.oplog = client.Database("local").Collection("oplog.rs")

	// setting namespace
	oplogTailer.namespace = fmt.Sprintf("%s.%s", oplogTailer.database, oplogTailer.collection)

	// setting timestamp
	oplogTailer.timestamp = getLatestTimestamp(oplogTailer.oplog)
	slog.Info("initialization complete")

}

func (oplogTailer *OplogTailer) getCollectionStats() (map[string]interface{}, error) {
	stats := bson.M{}
	command := bson.D{{Key: "collStats", Value: oplogTailer.collection}}

	err := oplogTailer.client.Database(oplogTailer.database).RunCommand(context.Background(), command).Decode(&stats)
	if err != nil {
		slog.Info("Error fetching collection stats: %v", err)
		return nil, err
	}

	result := map[string]interface{}{
		"size": stats["size"],
		// "storageSize": stats["storageSize"],
		"count": stats["count"],
	}

	return result, nil
}

func (oplogTailer OplogTailer) tailOplog() {
	slog.Info(fmt.Sprintf("Starting to tail the oplog for %s...", oplogTailer.namespace))
	ctx := context.Background()

	for {
		// define the filter for the query
		filter := bson.D{
			{Key: "ts", Value: bson.D{{Key: "$gt", Value: oplogTailer.timestamp}}},
			{Key: "ns", Value: oplogTailer.namespace},
		}

		// options for a tailable await cursor
		findOptions := options.Find().SetCursorType(options.TailableAwait)

		cursor, err := oplogTailer.oplog.Find(ctx, filter, findOptions)
		if err != nil {
			if mongo.IsNetworkError(err) {
				slog.Info("MongoDB connection lost, retrying in 5 seconds...")
				time.Sleep(5 * time.Second)
				continue
			} else {
				slog.Info(fmt.Sprintf("Error occurred: %v", err))
				break
			}
		}
		defer cursor.Close(ctx)

		for {
			if cursor.Next(ctx) {
				var doc bson.M
				if err := cursor.Decode(&doc); err != nil {
					slog.Info(fmt.Sprintf("Error decoding document: %v", err))
					continue
				}

				// Extract and update the timestamp
				tsValue, ok := doc["ts"]
				if !ok {
					slog.Info("'ts' field not found in the document")
					continue
				}

				ts, ok := tsValue.(primitive.Timestamp)
				if !ok {
					slog.Info("'ts' field is not of type primitive.Timestamp")
					continue
				}
				oplogTailer.timestamp = ts

				oplogTailer.logOperation(doc)
			} else {
				if err := cursor.Err(); err != nil {
					if mongo.IsNetworkError(err) {
						slog.Info("MongoDB connection lost, retrying in 5 seconds...")
						time.Sleep(5 * time.Second)
						break
					} else {
						slog.Info("Error occurred: %v", err)
						return
					}
				}

				slog.Info("Oplog is empty, waiting for new operations...")
				time.Sleep(1 * time.Second)
			}
		}
	}
}

func (oplogTailer OplogTailer) logOperation(doc bson.M) {
	operation := doc["op"].(string)
	// ns := doc["ns"]

	operationMap := map[string]string{
		"i": "INSERT",
		"u": "UPDATE",
		"d": "DELETE",
	}
	expandedOp, exists := operationMap[operation]
	if !exists {
		expandedOp = "UNKNOWN"
	}
	slog.Info(fmt.Sprintf("operation %s", expandedOp))
	stats, _ := oplogTailer.getCollectionStats()
	slog.Info(fmt.Sprintf("Collection Stats: %+v", stats))

}

func main() {
	mongoURI := flag.String("mongo-uri", "mongodb://localhost:27017/", "MongoDB URI")
	databaseName := flag.String("database", "test_db", "Database name")
	collectionName := flag.String("collection", "test_collection", "Collection name")
	flag.Parse()

	oplogTailer := OplogTailer{}
	oplogTailer.Init(*mongoURI, *databaseName, *collectionName)
	oplogTailer.tailOplog()

}
