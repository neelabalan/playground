package main

import (
	"database/sql"
	"fmt"
	"log"
	"net/http"
	"notes/db"
	"strconv"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

func PostError(message string, err error, w http.ResponseWriter, r *http.Request, statusCode int) {
	var responseMessage = message
	// error can be nil
	if err != nil {
		responseMessage = fmt.Sprintf("%s - %s", message, err.Error())
	}
	log.Println(responseMessage)
	encode(w, r, statusCode, GenericResponse{Message: responseMessage})

}
func (app *App) CreateUserHandler(w http.ResponseWriter, r *http.Request) {

	dec, err := decode[CreateUserRequestModel](r)
	if err != nil {
		PostError("Error decoding request structure", err, w, r, http.StatusBadRequest)
		return
	}
	hashedPassword := HashPassword(dec.Password)

	user, err := app.queries.CreateUser(app.ctx, db.CreateUserParams{
		Username:     dec.Username,
		Password:     hashedPassword,
		Email:        dec.Email,
		RefreshToken: "",
	})
	log.Println(user)
	if err != nil {
		errMsg := "Error encountered while registering user"
		if strings.Contains(err.Error(), "UNIQUE constraint failed: users.username") {
			errMsg = "Username already taken"
		} else if strings.Contains(err.Error(), "UNIQUE constraint failed: users.email") {
			errMsg = "Email already registered"
		}
		PostError(errMsg, nil, w, r, http.StatusConflict)
		return
	}
	encode(w, r, http.StatusCreated, GenericResponse{Message: "User created successfully"})
}

func (app *App) RefreshTokenHandler(w http.ResponseWriter, r *http.Request) {
	// refreshToken, err := strconv.Atoi(r.PathValue("refreshToken"))
	refreshToken := r.Header.Get("Authorization")
	if refreshToken == "" {
		PostError("Refresh token missing", fmt.Errorf("refresh token not provided in the Authorization header"), w, r, http.StatusBadRequest)
		return
	}

	user, err := app.ValidateRefreshToken(refreshToken)
	if err != nil {
		PostError("Error encoutered while validating refresh token", err, w, r, http.StatusBadRequest)
		return
	}

	// Generate new access and refresh tokens
	newAccessToken, err := GenerateAccessToken(user.Email)
	if err != nil {
		PostError("Could not generate access token", err, w, r, http.StatusInternalServerError)
		return
	}

	newRefreshToken, err := GenerateRefreshToken()
	if err != nil {
		PostError("Could not generate refresh token", err, w, r, http.StatusInternalServerError)
		return
	}
	_, err = app.queries.UpdateRefreshToken(app.ctx, db.UpdateRefreshTokenParams{Email: user.Email, RefreshToken: newRefreshToken})
	if err != nil {
		PostError("Could not update refresh token", err, w, r, http.StatusInternalServerError)
		return
	}
	log.Println("Refresh token updated successfully for user ", user.Email)
	encode(w, r, http.StatusOK, TokenRefreshResponseModel{AccessToken: newAccessToken, RefreshToken: newRefreshToken})
}

func (app *App) SignInRequestHandler(w http.ResponseWriter, r *http.Request) {
	dec, err := decode[SignInRequestModel](r)
	if err != nil {
		PostError("Error decoding request structure", err, w, r, http.StatusBadRequest)
		return
	}
	user, err := app.queries.GetUserByEmail(app.ctx, dec.Email)
	if err != nil {
		PostError("Incorrect credentials", nil, w, r, http.StatusUnauthorized)
		return
	}
	if !CheckPassword(user.Password, dec.Password) {
		PostError("Incorrect credentials", nil, w, r, http.StatusUnauthorized)
		return
	}
	expirationTime := time.Now().Add(5 * time.Minute)

	refreshToken, err := GenerateRefreshToken()
	if err != nil {
		PostError("Could not generate refresh token", err, w, r, http.StatusInternalServerError)
		return
	}
	_, err = app.queries.UpdateRefreshToken(app.ctx, db.UpdateRefreshTokenParams{Email: user.Email, RefreshToken: refreshToken})
	if err != nil {
		PostError("Could not update refresh token", err, w, r, http.StatusInternalServerError)
		return
	}
	claims := &Claims{
		Email: dec.Email,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(expirationTime),
		},
	}
	tokenString, _ := jwt.NewWithClaims(jwt.SigningMethodHS256, claims).SignedString(jwtKey)
	http.SetCookie(w, &http.Cookie{
		Name:     "access_token",
		Value:    tokenString,
		Expires:  expirationTime,
		HttpOnly: true,
		Secure:   true, // Set to true if using HTTPS
		SameSite: http.SameSiteLaxMode,
		Path:     "/",
	})

	// Set the refresh token as an HTTP-only cookie
	http.SetCookie(w, &http.Cookie{
		Name:     "refresh_token",
		Value:    refreshToken,
		Expires:  time.Now().Add(7 * 24 * time.Hour), // Set an appropriate expiration time for refresh token
		HttpOnly: true,
		Secure:   true, // Set to true if using HTTPS
		SameSite: http.SameSiteLaxMode,
		Path:     "/",
	})
	encode(w, r, http.StatusOK, SignInResponseModel{RefreshToken: refreshToken, AccessToken: tokenString})

}

func (app *App) CreateNoteHandler(w http.ResponseWriter, r *http.Request) {
	userEmail := r.Context().Value(EMAIL).(string)
	dec, err := decode[CreateNoteRequestModel](r)
	if err != nil {
		PostError("Error encoutered while parsing request body", err, w, r, http.StatusBadRequest)
		return
	}
	extractedTags := ExtractTags(dec.Note)
	tags := sql.NullString{}
	if extractedTags != "" {
		tags = sql.NullString{String: extractedTags, Valid: true}

	}
	noteCreateTime := time.Now()
	note, err := app.queries.CreateNote(app.ctx, db.CreateNoteParams{
		Email:     userEmail,
		Note:      dec.Note,
		Tags:      tags,
		CreatedAt: noteCreateTime,
		UpdatedAt: noteCreateTime,
	})
	if err != nil {
		PostError("Unable to create the note due to ", err, w, r, http.StatusInternalServerError)
		return
	}
	encode(w, r, http.StatusCreated, CreateNoteResponseModel{
		Message:   "Note created successfully",
		Tags:      note.Tags.String,
		CreatedAt: noteCreateTime.String(),
		UpdatedAt: noteCreateTime.String(),
	})
}
func (app *App) GetNoteHandler(w http.ResponseWriter, r *http.Request) {
	userEmail := r.Context().Value(EMAIL).(string)
	idStr := r.PathValue("id")
	id, err := strconv.ParseInt(idStr, 10, 64)
	if err != nil {
		PostError("Not valid ID, has to be of type integer", err, w, r, http.StatusBadRequest)
		return
	}
	note, err := app.queries.GetNote(app.ctx, db.GetNoteParams{Email: userEmail, ID: id})
	if err != nil {
		PostError("Could not find note with ID", nil, w, r, http.StatusBadRequest)
		return
	}

	encode(w, r, http.StatusOK, GetNoteResponseModel{
		NoteResponseModel{
			ID:        id,
			Note:      note.Note,
			Tags:      note.Tags.String,
			CreatedAt: note.CreatedAt.String(),
			UpdatedAt: note.UpdatedAt.String(),
		},
	})

}

func (app *App) ListNotesHandler(w http.ResponseWriter, r *http.Request) {
	userEmail := r.Context().Value(EMAIL).(string)

	pageStr := r.URL.Query().Get("page")
	pageSizeStr := r.URL.Query().Get("page_size")

	// pagination parameters to integers
	var page int64
	var pageSize int64

	if pageStr != "" {
		page, _ = strconv.ParseInt(pageStr, 10, 64)
	} else {
		page = 1
	}

	if pageSizeStr != "" {
		pageSize, _ = strconv.ParseInt(pageSizeStr, 10, 64)
	} else {
		pageSize = 50
	}

	// calculate offset
	offset := (page - 1) * pageSize

	// fetch notes with pagination
	notes, err := app.queries.ListNotes(app.ctx, db.ListNotesParams{
		Email:  userEmail,
		Limit:  pageSize,
		Offset: offset,
	})
	if err != nil {
		PostError("Error fetching notes", err, w, r, http.StatusInternalServerError)
		return
	}
	var noteResponses []NoteResponseModel
	for _, note := range notes {
		noteResponses = append(noteResponses, NoteResponseModel{
			ID:        note.ID,
			Note:      note.Note,
			Tags:      note.Tags.String,
			CreatedAt: note.CreatedAt.String(),
			UpdatedAt: note.UpdatedAt.String(),
		})
	}

	encode(w, r, http.StatusOK, ListNotesResponseModel{Notes: noteResponses, Page: page, PageSize: pageSize})
}

func (app *App) UpdateNoteHandler(w http.ResponseWriter, r *http.Request) {
	userEmail := r.Context().Value(EMAIL).(string)
	idStr := r.PathValue("id")
	id, err := strconv.ParseInt(idStr, 10, 64)
	if err != nil {
		PostError("Not valid ID, has to be of type integer", err, w, r, http.StatusBadRequest)
		return
	}

	dec, err := decode[UpdateNoteRequestModel](r)
	if err != nil {
		PostError("Error encountered while parsing request body", err, w, r, http.StatusBadRequest)
		return
	}

	// Get the user to find user_id
	user, err := app.queries.GetUserByEmail(app.ctx, userEmail)
	if err != nil {
		PostError("Could not find user", err, w, r, http.StatusInternalServerError)
		return
	}

	extractedTags := ExtractTags(dec.Note)
	tags := sql.NullString{}
	if extractedTags != "" {
		tags = sql.NullString{String: extractedTags, Valid: true}
	}

	noteUpdateTime := time.Now()
	err = app.queries.UpdateNote(app.ctx, db.UpdateNoteParams{
		Note:      dec.Note,
		Tags:      tags,
		UpdatedAt: noteUpdateTime,
		ID:        id,
		UserID:    user.ID,
	})
	if err != nil {
		PostError("Unable to update the note", err, w, r, http.StatusInternalServerError)
		return
	}
	encode(w, r, http.StatusOK, GenericResponse{Message: "Note updated successfully"})
}

func (app *App) DeleteNoteHandler(w http.ResponseWriter, r *http.Request) {
	userEmail := r.Context().Value(EMAIL).(string)
	idStr := r.PathValue("id")
	id, err := strconv.ParseInt(idStr, 10, 64)
	if err != nil {
		PostError("Not valid ID, has to be of type integer", err, w, r, http.StatusBadRequest)
		return
	}

	user, err := app.queries.GetUserByEmail(app.ctx, userEmail)
	if err != nil {
		PostError("Could not find user", err, w, r, http.StatusInternalServerError)
		return
	}

	err = app.queries.DeleteNote(app.ctx, db.DeleteNoteParams{
		ID:     id,
		UserID: user.ID,
	})
	if err != nil {
		PostError("Unable to delete the note", err, w, r, http.StatusInternalServerError)
		return
	}
	encode(w, r, http.StatusOK, GenericResponse{Message: "Note deleted successfully"})
}

func (app *App) HealthCheckHandler(w http.ResponseWriter, r *http.Request) {
	encode(w, r, http.StatusOK, GenericResponse{Message: "OK"})
}
