package upstream

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func TestWorkerPool_Forward_UsesWorkersConcurrently(t *testing.T) {
	const (
		requestsCount = 100
		upstreamDelay = 150 * time.Millisecond
	)

	var upstreamCalls atomic.Int32
	var inFlight atomic.Int32
	var maxInFlight atomic.Int32

	upstreamServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.RawQuery != "q=1" {
			t.Errorf("expected raw query q=1, got %q", r.URL.RawQuery)
		}

		upstreamCalls.Add(1)

		currentInFlight := inFlight.Add(1)
		for {
			prev := maxInFlight.Load()
			if currentInFlight <= prev || maxInFlight.CompareAndSwap(prev, currentInFlight) {
				break
			}
		}
		defer inFlight.Add(-1)

		time.Sleep(upstreamDelay)

		w.Header().Set("Content-Type", "application/json")
		_, _ = io.WriteString(w, `{"ok":true}`)
	}))
	defer upstreamServer.Close()

	pool := NewWorkerPool()
	t.Cleanup(func() {
		shutdownCtx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		if err := pool.ShutDown(shutdownCtx); err != nil {
			t.Fatalf("worker pool shutdown: %v", err)
		}
	})

	body := []byte(`{"hello":"world"}`)
	start := time.Now()

	var wg sync.WaitGroup
	errCh := make(chan error, requestsCount)

	for range requestsCount {
		wg.Add(1)
		go func() {
			defer wg.Done()

			rec := httptest.NewRecorder()
			req := httptest.NewRequest(http.MethodPost, "http://proxy.local/static?q=1", bytes.NewReader(body))
			req.Header.Set("Content-Type", "application/json")

			err := pool.Forward(req.Context(), rec, req, upstreamServer.URL+"/static", body)
			if err != nil {
				errCh <- fmt.Errorf("forward request: %w", err)
				return
			}

			if rec.Code != http.StatusOK {
				errCh <- fmt.Errorf("unexpected status code: %d, body=%s", rec.Code, rec.Body.String())
				return
			}

			if got := rec.Header().Get("Content-Type"); got != "application/json" {
				errCh <- fmt.Errorf("unexpected content-type: %q", got)
				return
			}

			if got := rec.Body.String(); got != `{"ok":true}` {
				errCh <- fmt.Errorf("unexpected body: %q", got)
			}
		}()
	}

	wg.Wait()
	close(errCh)

	for err := range errCh {
		t.Fatal(err)
	}

	elapsed := time.Since(start)

	if got := int(upstreamCalls.Load()); got != requestsCount {
		t.Fatalf("expected upstream calls = %d, got %d", requestsCount, got)
	}

	if got := maxInFlight.Load(); got < 10 {
		t.Fatalf("expected concurrent upstream requests >= 10, got %d", got)
	}

	if elapsed >= 5*time.Second {
		t.Fatalf("expected concurrent forwarding to finish in under 5s, got %v", elapsed)
	}
}
