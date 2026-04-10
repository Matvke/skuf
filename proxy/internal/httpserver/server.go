package httpserver

import (
	"encoding/json"
	"errors"
	"log/slog"
	"net/http"

	"github.com/Matvke/skuf/internal/body"
	"github.com/Matvke/skuf/internal/client"
	"github.com/Matvke/skuf/internal/config"
	"github.com/Matvke/skuf/internal/extract"
	"github.com/Matvke/skuf/internal/middleware"
	"github.com/Matvke/skuf/internal/routing"
	"github.com/Matvke/skuf/internal/upstream"
)

type Server struct {
	cfgStore  *config.Store
	client    *client.EngineClient
	forwarder *upstream.Forwarder
}

func New(cfgStore *config.Store, engineClient *client.EngineClient, forwarder *upstream.Forwarder) *Server {
	return &Server{
		cfgStore:  cfgStore,
		client:    engineClient,
		forwarder: forwarder,
	}
}

func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("/health", s.handleHealth)
	mux.HandleFunc("/debug/config", s.handleConfig)
	mux.HandleFunc("/", s.handleCatchAll)

	var h http.Handler = mux
	h = middleware.RequestID(h)

	return h
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
	ctx := r.Context()

	cfg := s.cfgStore.Get()

	target := routing.Match(cfg, r)

	if target == nil {
		slog.LogAttrs(
			r.Context(),
			slog.LevelInfo,
			"unmatched target",
			slog.Bool("matched", false),
		)

		writeJSON(w, http.StatusNotFound, map[string]any{
			"error": "no route matched",
		})
		return
	}

	data, err := body.Reader(r, 1<<20)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]any{
			"error": err.Error(),
		})
		return
	}

	payload, err := body.ParseJSON(data)
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]any{
			"error": err.Error(),
		})
		return
	}

	extracted := make([]extract.Value, 0)

	for _, path := range target.JsonPaths {
		combinedPath, err := extract.ParsePath(path)
		if err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]any{
				"error": err.Error(),
			})
			return
		}

		values, err := extract.Extract(payload, *combinedPath)
		if err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]any{
				"error": err.Error(),
			})
			return
		}

		extracted = append(extracted, values...)
	}

	if len(extracted) == 0 {
		if err := s.forwarder.Forward(ctx, w, r, target.UpstreamURL, data); err != nil {
			writeJSON(w, http.StatusBadGateway, map[string]any{
				"error": err.Error(),
			})
		}
	}

	cache := make(map[string]string, len(extracted))

	for _, extractedValue := range extracted {
		anonymizedText, ok := cache[extractedValue.Value]
		if !ok {
			anonymizedText, err = s.client.Anonymize(ctx, extractedValue.Value)
			if err != nil {
				var validationError *client.EngineValidationError
				if errors.As(err, &validationError) {
					writeJSON(w, http.StatusBadGateway, map[string]any{
						"error": "engine validation error",
					})
					return
				}

				w.WriteHeader(http.StatusBadGateway)
				_ = json.NewEncoder(w).Encode(map[string]any{
					"error": err.Error(),
				})
				return
			}
			cache[extractedValue.Value] = anonymizedText
		}

		err = extract.SetString(payload, extractedValue.Path, anonymizedText)
		if err != nil {
			writeJSON(w, http.StatusBadGateway, map[string]any{
				"error": err.Error(),
			})
			return
		}
	}

	newBody, err := json.Marshal(payload)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]any{
			"error": err.Error(),
		})
		return
	}

	slog.LogAttrs(
		r.Context(),
		slog.LevelInfo,
		"forward request",
		slog.String("target", target.Name),
		slog.Int("extracted_count", len(extracted)),
		slog.String("upstream_url", target.UpstreamURL),
	)

	if err := s.forwarder.Forward(ctx, w, r, target.UpstreamURL, newBody); err != nil {
		writeJSON(w, http.StatusBadGateway, map[string]any{
			"error": err.Error(),
		})
		return
	}
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}
