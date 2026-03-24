package handler

import (
	"io"
	"net/http"

	"github.com/Matvke/skuf/internal/client"
)

type Handler struct {
	engineClient *client.EngineClient
}

func NewHandler(client *client.EngineClient) *Handler {
	return &Handler{
		engineClient: client,
	}
}

func (h *Handler) EngineHandler(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "failed to read body", http.StatusBadRequest)
		return
	}

	engineBody, statusCode, err := h.engineClient.Forward(body)
	if err != nil {
		http.Error(w, "engine is unavailable", http.StatusBadGateway)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	w.Write(engineBody)

}
