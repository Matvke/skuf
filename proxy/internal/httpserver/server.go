package httpserver

import (
	"context"
	"encoding/json"
	"log/slog"
	"net/http"

	"github.com/Matvke/skuf/internal/config"
	"github.com/Matvke/skuf/internal/routing"
)

type Server struct {
	cfgStore *config.Store
}

func New(cfgStore *config.Store) *Server {
	return &Server{
		cfgStore: cfgStore,
	}
}

func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("/healthz", s.handleHealth)
	mux.HandleFunc("/debug/config", s.handleConfig)
	mux.HandleFunc("/", s.handleCatchAll)

	return mux
}

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("ok"))
}

func (s *Server) handleConfig(w http.ResponseWriter, r *http.Request) {
	cfg := s.cfgStore.Get()

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(cfg)
}

func (s *Server) handleCatchAll(w http.ResponseWriter, r *http.Request) {
	cfg := s.cfgStore.Get()

	target := routing.Match(cfg, r)

	if target == nil {
		slog.LogAttrs(
			context.Background(),
			slog.LevelInfo,
			"unmatched target",
			slog.Bool("matched", false),
		)

		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]any{
			"matched": false,
		})
	} else {
		slog.LogAttrs(
			context.Background(),
			slog.LevelInfo,
			"matched target",
			slog.String("target", target.Name),
			slog.Bool("matched", true),
			slog.String("upstream_url", target.UpstreamURL),
		)

		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]any{
			"matched":      true,
			"target":       target.Name,
			"upstream_url": target.UpstreamURL,
			"method":       r.Method,
			"host":         r.Host,
			"path":         r.URL.Path,
		})
	}

	slog.LogAttrs(
		context.TODO(),
		slog.LevelInfo,
		"proxy skeleton is working",
		slog.String("host", r.Host),
		slog.String("method", r.Method),
		slog.String("path", r.URL.Path),
		slog.Int("targets", len(cfg.Targets)),
	)
}
