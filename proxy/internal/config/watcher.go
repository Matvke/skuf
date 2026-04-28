package config

import (
	"context"
	"log/slog"
	"path/filepath"
	"time"

	"github.com/fsnotify/fsnotify"
)

type Watcher struct {
	path  string
	store *Store
}

func NewWatcher(path string, store *Store) *Watcher {
	return &Watcher{
		path:  path,
		store: store,
	}
}

func (w *Watcher) Run(ctx context.Context) error {
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		return err
	}
	defer watcher.Close()

	dir := filepath.Dir(w.path)
	if err = watcher.Add(dir); err != nil {
		return err
	}

	debounce := time.Duration(w.store.Get().ReloadDebounceMS) * time.Millisecond
	var timer *time.Timer
	var timerCh <-chan time.Time

	reload := func() {
		rawCfg, err := LoadFromFile(w.path)
		if err != nil {
			slog.LogAttrs(
				ctx,
				slog.LevelError,
				"Cant read from config file",
				slog.String("path", w.path),
				slog.Any("error", err),
			)
			return
		}

		if err = Validate(rawCfg); err != nil {
			slog.LogAttrs(
				ctx,
				slog.LevelError,
				"config validation failed",
				slog.Any("error", err),
			)
			return
		}

		cfg, err := Compile(rawCfg)
		if err != nil {
			slog.LogAttrs(
				ctx,
				slog.LevelError,
				"cant compile rawConfig",
				slog.Any("error", err),
			)
			return
		}

		w.store.Set(cfg)
		slog.LogAttrs(
			ctx,
			slog.LevelInfo,
			"config reloaded successfully",
		)
	}

	for {
		select {
		case <-ctx.Done():
			return nil
		case event, ok := <-watcher.Events:
			if !ok {
				return nil
			}

			if filepath.Clean(w.path) != filepath.Clean(event.Name) {
				continue
			}

			if event.Op&(fsnotify.Create|fsnotify.Write|fsnotify.Rename) != 0 {
				if timer != nil {
					timer.Stop()
				}
				timer = time.NewTimer(debounce)
				timerCh = timer.C
			}
		case <-timerCh:
			reload()
			timerCh = nil
		case err, ok := <-watcher.Errors:
			if !ok {
				return nil
			}
			slog.LogAttrs(
				ctx,
				slog.LevelError,
				"config watcher error",
				slog.Any("error", err),
			)
		}
	}
}
