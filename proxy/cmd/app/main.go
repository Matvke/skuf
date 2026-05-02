package main

import (
	"context"
	"log"
	"log/slog"
	"net/http"
	"os/signal"
	"syscall"
	"time"

	"github.com/Matvke/skuf/internal/client"
	"github.com/Matvke/skuf/internal/config"
	"github.com/Matvke/skuf/internal/httpserver"
	"github.com/Matvke/skuf/internal/upstream"
)

const (
	configPath = "configs/config.yaml"
)

func main() {
	rawCfg, err := config.LoadFromFile(configPath)
	if err != nil {
		log.Fatalf("failed loading config: %v", err)
	}

	if err = config.Validate(rawCfg); err != nil {
		log.Fatalf("failed validating config: %v", err)
	}

	cfg, err := config.Compile(rawCfg)
	if err != nil {
		log.Fatalf("failed compiling rawConfig: %v", err)
	}

	store := config.NewStore(cfg)

	watcher := config.NewWatcher(configPath, store)

	go func() {
		if err := watcher.Run(context.Background()); err != nil {
			log.Fatal(err)
		}
	}()

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	engineClient := client.NewEngineClient(cfg.EngineUrl)
	forwarder := upstream.NewWorkerPool()

	srv := httpserver.New(store, configPath, engineClient, forwarder)

	httpServ := &http.Server{
		Addr:              ":8080",
		Handler:           srv.Handler(),
		ReadHeaderTimeout: 5 * time.Second,
	}

	go func() {
		log.Printf("server started on %s", httpServ.Addr)
		if err := httpServ.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("http server error: %v", err)
		}
	}()

	<-ctx.Done()

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := forwarder.ShutDown(shutdownCtx); err != nil {
		log.Printf("forwarder shutdown error: %v", err)
	}

	if err := httpServ.Shutdown(shutdownCtx); err != nil {
		log.Printf("http shutdown error: %v", err)
	}

	slog.Info("server stopped")
}
