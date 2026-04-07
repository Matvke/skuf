package httpserver

import (
	"encoding/json"
	"log/slog"
	"net/http"

	"github.com/Matvke/skuf/internal/body"
	"github.com/Matvke/skuf/internal/config"
	"github.com/Matvke/skuf/internal/extract"
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
			r.Context(),
			slog.LevelInfo,
			"unmatched target",
			slog.Bool("matched", false),
		)

		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]any{
			"matched": false,
		})
		return
	}

	data, err := body.Reader(r, 1<<20)
	if err != nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		_ = json.NewEncoder(w).Encode(map[string]any{
			"error": err.Error(),
		})
		return
	}

	payload, err := body.ParseJSON(data)
	if err != nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		_ = json.NewEncoder(w).Encode(map[string]any{
			"error": err.Error(),
		})
		return
	}

	extracted := make([]extract.Value, 0)

	for _, path := range target.JsonPaths {
		combinedPath, err := extract.ParsePath(path)
		if err != nil {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusBadRequest)
			_ = json.NewEncoder(w).Encode(map[string]any{
				"error": err.Error(),
			})
			return
		}

		values, err := extract.Extract(payload, *combinedPath)
		if err != nil {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusBadRequest)
			_ = json.NewEncoder(w).Encode(map[string]any{
				"error": err.Error(),
			})
			return
		}

		extracted = append(extracted, values...)
	}

	slog.LogAttrs(
		r.Context(),
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
		"body_size":    len(data),
		"json":         "valid",
		"extracted":    extracted,
	})
}
