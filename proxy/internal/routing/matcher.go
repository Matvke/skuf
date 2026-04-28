package routing

import (
	"net/http"
	"strings"

	"github.com/Matvke/skuf/internal/config"
)

func Match(cfg *config.Config, r *http.Request) *config.Target {
	if cfg == nil {
		return nil
	}

	requestUrl := r.URL.Path
	requestMethod := strings.ToUpper(r.Method)
	requestHost := strings.ToLower(r.Host)

	for i := range cfg.Targets {
		target := cfg.Targets[i]

		if target.MatchHost != "" && target.MatchHost != requestHost {
			continue
		}

		if target.UpstreamURL != "" && target.MatchPath != requestUrl {
			continue
		}

		if _, ok := target.Methods[requestMethod]; !ok {
			continue
		}

		return &target
	}

	return nil
}
