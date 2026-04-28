package config

import "sync/atomic"

type Store struct {
	current atomic.Value
}

func NewStore(initial *Config) *Store {
	st := &Store{}
	st.current.Store(initial)
	return st
}

func (s *Store) Get() *Config {
	v := s.current.Load()
	if v == nil {
		return nil
	}

	return v.(*Config)
}

func (s *Store) Set(cfg *Config) {
	s.current.Store(cfg)
}
