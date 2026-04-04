package main

import (
	"context"
	"log"
	"net/http"
	"os/signal"
	"syscall"
	"time"

	"github.com/Matvke/skuf/internal/config"
	"github.com/Matvke/skuf/internal/httpserver"
)

func main() {
	configPath := "configs/config.yaml"

	cfg, err := config.LoadFromFile(configPath)
	if err != nil {
		log.Fatalf("failed loading config: %v", err)
	}

	if err = config.Validate(cfg); err != nil {
		log.Fatalf("failed validating config: %v", err)
	}

	store := config.NewStore(cfg)

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	cfgWatcher := config.NewWatcher(configPath, store)
	go func() {
		if err := cfgWatcher.Run(ctx); err != nil {
			log.Printf("config watcher stopped with error: %v", err)
		}
	}()

	srv := httpserver.New(store)

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

	if err := httpServ.Shutdown(shutdownCtx); err != nil {
		log.Printf("http shutdown error: %v", err)
	}

	log.Println("server stopped")
}
