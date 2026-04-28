package config

import (
	"errors"
	"fmt"
	"strings"
)

func Compile(rawCfg *RawConfig) (*Config, error) {
	if rawCfg == nil {
		return nil, errors.New("RawConfig is nil")
	}

	cfg := &Config{
		Port:             rawCfg.Port,
		EngineUrl:        rawCfg.EngineUrl,
		ReloadDebounceMS: rawCfg.ReloadDebounceMS,
		Targets:          make([]Target, 0, len(rawCfg.Targets)),
	}

	for _, rt := range rawCfg.Targets {
		methods := make(map[string]struct{}, len(rt.Match.Methods))
		for _, m := range rt.Match.Methods {
			methods[strings.ToUpper(m)] = struct{}{}
		}

		upstreamUrl := fmt.Sprintf("%s://%s%s", rt.Upstream.Scheme, rt.Upstream.Host, rt.Upstream.Path)

		target := Target{
			Methods:     methods,
			UpstreamURL: upstreamUrl,
			MatchHost:   strings.ToLower(rt.Match.Host),
			MatchPath:   rt.Match.Path,
			Name:        rt.Name,
			JsonPaths:   rt.Extract.JSONPaths,
		}

		cfg.Targets = append(cfg.Targets, target)
	}

	return cfg, nil
}
