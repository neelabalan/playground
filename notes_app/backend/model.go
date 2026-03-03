package main

type CreateUserRequestModel struct {
	Username string `json:"username"`
	Email    string `json:"email"`
	Password string `json:"password"`
}

type SignInRequestModel struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type SignInResponseModel struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
}

type GenericResponse struct {
	Message string `json:"message"`
}

type TokenRefreshResponseModel struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
}

type CreateNoteRequestModel struct {
	Note string `json:"note"`
}

type UpdateNoteRequestModel struct {
	Note string `json:"note"`
}

type CreateNoteResponseModel struct {
	Message   string `json:"message"`
	Tags      string `json:"tags"`
	CreatedAt string `json:"created_at"`
	UpdatedAt string `json:"updated_at"`
}

type NoteResponseModel struct {
	ID        int64  `json:"id"`
	Note      string `json:"note"`
	Tags      string `json:"tags"`
	CreatedAt string `json:"created_at"`
	UpdatedAt string `json:"updated_at"`
}

type GetNoteResponseModel struct {
	NoteResponseModel
}

type ListNotesResponseModel struct {
	Notes    []NoteResponseModel `json:"notes"`
	Page     int64               `json:"page"`
	PageSize int64               `json:"page_size"`
}
