package main

import (
	"context"
	"database/sql"
	_ "embed"
	"fmt"
	"log"
	"net/http"
	"notes/db"
	"os"

	"github.com/golang-jwt/jwt/v5"
	_ "github.com/mattn/go-sqlite3"
)

//go:embed sql/schema.sql
var ddl string

var jwtKey = []byte("h;j6_d7],u'wPJ|$?xq&~5U[FQV0hGtA")

type Claims struct {
	Email string `json:"email"`
	jwt.RegisteredClaims
}

type App struct {
	queries *db.Queries
	ctx     context.Context
}

func getCorsOrigin() string {
	origin := os.Getenv("CORS_ORIGIN")
	if origin == "" {
		origin = "http://localhost:5173"
	}
	return origin
}

func enableCors(w *http.ResponseWriter) {
	(*w).Header().Set("Access-Control-Allow-Origin", getCorsOrigin())
	(*w).Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
	(*w).Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
	(*w).Header().Set("Access-Control-Allow-Credentials", "true")
}

func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		enableCors(&w)

		// Handle preflight (OPTIONS) requests
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}

func run() error {
	ctx := context.Background()

	dbConnection, err := sql.Open("sqlite3", "./dbstore/notes.db")
	if err != nil {
		return err
	}

	// create tables
	if _, err := dbConnection.ExecContext(ctx, ddl); err != nil {
		return err
	}
	log.Println("created the database tables")
	queries := db.New(dbConnection)

	app := App{
		queries: queries,
		ctx:     ctx,
	}

	// register routes
	mux := http.NewServeMux()
	mux.HandleFunc("POST /signup", app.CreateUserHandler)
	mux.HandleFunc("POST /signin", app.SignInRequestHandler)
	mux.HandleFunc("GET /refresh_token", app.RefreshTokenHandler)
	mux.HandleFunc("GET /health", app.HealthCheckHandler)
	mux.HandleFunc("POST /create_note", AuthenticationMiddleware(app.CreateNoteHandler))
	mux.HandleFunc("GET /note/{id}", AuthenticationMiddleware(app.GetNoteHandler))
	mux.HandleFunc("PUT /note/{id}", AuthenticationMiddleware(app.UpdateNoteHandler))
	mux.HandleFunc("DELETE /note/{id}", AuthenticationMiddleware(app.DeleteNoteHandler))
	mux.HandleFunc("GET /list_notes", AuthenticationMiddleware(app.ListNotesHandler))

	handler := corsMiddleware(mux)

	server := http.Server{
		Addr: ":8080",
		// ReadTimeout:  5 * time.Second,
		// WriteTimeout: 5 * time.Second,
		// IdleTimeout:  200 * time.Second,
		Handler: handler,
	}

	fmt.Println("Starting server at", server.Addr)
	err = server.ListenAndServe()
	if err != nil {
		if err != http.ErrServerClosed {
			panic(err)
		}
	}
	return err

	// http.ListenAndServe("localhost:8090", mux)
}

func main() {
	if err := run(); err != nil {
		log.Fatal(err)
	}
}
