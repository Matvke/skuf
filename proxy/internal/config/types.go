package config

type RawConfig struct {
	Port             int         `yaml:"port"`
	EngineUrl        string      `yaml:"engine_url"`
	ReloadDebounceMS int         `yaml:"reload_debounce_ms"`
	Targets          []RawTarget `yaml:"targets"`
}

type RawTarget struct {
	Name     string      `yaml:"name"`
	Profile  string      `yaml:"profile"`
	Match    RawMatch    `yaml:"match"`
	Upstream RawUpstream `yaml:"upstream"`
	Extract  Extractor   `yaml:"extract"`
}

type RawMatch struct {
	Host    string   `yaml:"host"`
	Path    string   `yaml:"path"`
	Methods []string `yaml:"methods"`
}

type RawUpstream struct {
	Scheme string `yaml:"scheme"`
	Host   string `yaml:"host"`
	Path   string `yaml:"path"`
}

type Extractor struct {
	JSONPaths []string `yaml:"json_paths"`
}
