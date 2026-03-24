package main

import (
	"net/http"

	"github.com/Matvke/skuf/internal/client"
	"github.com/Matvke/skuf/internal/handler"
)

func main() {
	client := client.NewEngineClient("http://localhost:8081")
	handler := handler.NewHandler(client)

	server := http.NewServeMux()
	server.HandleFunc("/", handler.EngineHandler)

	http.ListenAndServe(":8080", server)
}
