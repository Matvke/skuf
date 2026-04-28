package config

import (
	"errors"
	"fmt"
	"net/url"
	"strings"
)

func Validate(cfg *RawConfig) error {
	if cfg == nil {
		return errors.New("Config is nil")
	}

	if cfg.Port <= 0 || cfg.Port > 65535 {
		return fmt.Errorf("Invalid port in config: %d", cfg.Port)
	}

	if cfg.EngineUrl == "" {
		return errors.New("Engine url is empty")
	}

	if _, err := url.ParseRequestURI(cfg.EngineUrl); err != nil {
		return fmt.Errorf("Cant parse engine url, invalid, err: %v", err)
	}

	for i, t := range cfg.Targets {
		if strings.TrimSpace(t.Name) == "" {
			return fmt.Errorf("targets[%d].name is required", i)
		}

		if strings.TrimSpace(t.Match.Path) == "" {
			return fmt.Errorf("targets[%d].match.path is required", i)
		}

		if len(t.Match.Methods) == 0 {
			return fmt.Errorf("targets[%d].match.methods is required", i)
		}

		if strings.TrimSpace(t.Upstream.Scheme) == "" {
			return fmt.Errorf("targets[%d].upstream.scheme is required", i)
		}

		if strings.TrimSpace(t.Upstream.Host) == "" {
			return fmt.Errorf("targets[%d].upstream.host is required", i)
		}
	}

	if cfg.ReloadDebounceMS <= 0 {
		cfg.ReloadDebounceMS = 500
	}

	return nil
}
