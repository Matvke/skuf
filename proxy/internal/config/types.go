package config

type RawConfig struct {
	Port             int         `yaml:"port" json:"port"`
	EngineUrl        string      `yaml:"engine_url" json:"engine_url"`
	ReloadDebounceMS int         `yaml:"reload_debounce_ms" json:"reload_debounce_ms"`
	Targets          []RawTarget `yaml:"targets" json:"targets"`
}

type RawTarget struct {
	Name     string      `yaml:"name" json:"name"`
	Match    RawMatch    `yaml:"match" json:"match"`
	Upstream RawUpstream `yaml:"upstream" json:"upstream"`
	Extract  Extractor   `yaml:"extract" json:"extract"`
}

type RawMatch struct {
	Host    string   `yaml:"host" json:"host"`
	Path    string   `yaml:"path" json:"path"`
	Methods []string `yaml:"methods" json:"methods"`
}

type RawUpstream struct {
	Scheme string `yaml:"scheme" json:"scheme"`
	Host   string `yaml:"host" json:"host"`
	Path   string `yaml:"path" json:"path"`
}

type Extractor struct {
	JSONPaths []string `yaml:"json_paths" json:"json_paths"`
}

type Config struct {
	Port             int
	EngineUrl        string
	ReloadDebounceMS int
	Targets          []Target
}

type Target struct {
	Name        string
	MatchHost   string
	MatchPath   string
	Methods     map[string]struct{}
	UpstreamURL string
	JsonPaths   []string
}
