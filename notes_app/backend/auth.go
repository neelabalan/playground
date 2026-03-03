package main

import (
	"context"
	"database/sql"
	"fmt"
	"net/http"
	"notes/db"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
)

type contextKey string

const EMAIL = contextKey("email")

func GenerateRefreshToken() (string, error) {
	return uuid.NewString(), nil
}

func GenerateAccessToken(email string) (string, error) {
	expirationTime := time.Now().Add(15 * time.Minute)
	claims := &Claims{
		Email: email,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(expirationTime),
		},
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(jwtKey)
}

func (app *App) ValidateRefreshToken(token string) (*db.User, error) {
	user, err := app.queries.GetUserWithRefreshToken(app.ctx, token)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("refresh token not found")
		}
		return nil, fmt.Errorf("could not validate refresh token: %v", err)
	}
	return &user, nil
}

func ValidateAccessToken(token string) (*Claims, error) {
	claims := Claims{}
	jwtToken, err := jwt.ParseWithClaims(token, &claims, func(tok *jwt.Token) (interface{}, error) {
		if _, ok := tok.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method")
		}
		return jwtKey, nil
	})
	if !jwtToken.Valid {
		return nil, fmt.Errorf("token is invalid")
	}
	expirationTime, _ := jwtToken.Claims.GetExpirationTime()

	if expirationTime.Unix() < time.Now().Unix() {
		return nil, fmt.Errorf("token has expired")
	}
	return &claims, err
}

func AuthenticationMiddleware(handler http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var token string

		authHeader := r.Header.Get("Authorization")
		if strings.HasPrefix(authHeader, "Bearer ") {
			token = strings.TrimPrefix(authHeader, "Bearer ")
		}

		if token == "" {
			cookie, err := r.Cookie("access_token")
			if err == nil {
				token = cookie.Value
			}
		}

		if token == "" {
			http.Error(w, "Forbidden", http.StatusForbidden)
			return
		}

		claims, err := ValidateAccessToken(token)
		if err != nil {
			PostError("Error - ", err, w, r, http.StatusForbidden)
			return
		}

		ctx := context.WithValue(r.Context(), EMAIL, claims.Email)
		handler.ServeHTTP(w, r.WithContext(ctx))
	}
}
