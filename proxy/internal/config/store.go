package config

import "sync/atomic"

type Store struct {
	current atomic.Value
}

func NewStore(initial *RawConfig) *Store {
	st := &Store{}
	st.current.Store(initial)
	return st
}

func (s *Store) Get() *RawConfig {
	v := s.current.Load()
	if v == nil {
		return nil
	}

	return v.(*RawConfig)
}

func (s *Store) Set(cfg *RawConfig) {
	s.current.Store(cfg)
}
