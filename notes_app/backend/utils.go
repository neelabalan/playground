package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"regexp"
	"strings"

	"golang.org/x/crypto/bcrypt"
)

// usage

// err := encode(w, r, http.StatusOK, obj)
// decoded, err := decode[CreateSomethingRequest](r)

func encode[T any](w http.ResponseWriter, r *http.Request, status int, v T) error {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		return fmt.Errorf("encode json: %w", err)
	}
	return nil
}

func decode[T any](r *http.Request) (T, error) {
	var v T
	if err := json.NewDecoder(r.Body).Decode(&v); err != nil {
		return v, fmt.Errorf("decode json: %w", err)
	}
	return v, nil
}

func CheckPassword(hashedPassword, plainPassword string) bool {
	err := bcrypt.CompareHashAndPassword([]byte(hashedPassword), []byte(plainPassword))
	return err == nil
}

func HashPassword(password string) string {
	hashedPassword, _ := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	return string(hashedPassword)
}

func ExtractTags(input string) string {
	re := regexp.MustCompile(`#\w+`)
	tags := re.FindAllString(input, -1)

	// map to store unique tags
	tagSet := make(map[string]struct{})

	for _, tag := range tags {
		tagSet[tag] = struct{}{}
	}
	// Convert the map keys to a slice
	uniqueTags := make([]string, 0, len(tagSet))
	for tag := range tagSet {
		uniqueTags = append(uniqueTags, tag)
	}

	return strings.Join(uniqueTags, " ")
}
