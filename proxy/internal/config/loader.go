package config

import (
	"fmt"
	"os"

	"gopkg.in/yaml.v3"
)

func LoadFromFile(path string) (*RawConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("Cant read config from %s, err: %v", path, err)
	}

	var cfg RawConfig
	if err = yaml.Unmarshal(data, &cfg); err != nil {
		return nil, fmt.Errorf("Cant unmarshal data from %s to config struct, err: %v", path, err)
	}

	return &cfg, nil
}

func SaveToFile(path string, cfg *RawConfig) error {
	if cfg == nil {
		return fmt.Errorf("config is nil")
	}

	data, err := yaml.Marshal(cfg)
	if err != nil {
		return fmt.Errorf("cant marshal config to yaml, err: %v", err)
	}

	if err := os.WriteFile(path, data, 0o644); err != nil {
		return fmt.Errorf("cant write config file %s, err: %v", path, err)
	}

	return nil
}
