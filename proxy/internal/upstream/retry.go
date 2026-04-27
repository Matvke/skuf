package upstream

import (
	"context"
	"io"
	"math/rand"
	"net/http"
	"time"
)

type ConfigRetry struct {
	MaxRetries int
	BaseDelay  time.Duration
	MaxDelay   time.Duration
	Jitter     float64
}

func (wp *WorkerPool) doRequestWithRetry(
	ctx context.Context,
	r *http.Request,
	upstreamURL string,
	body []byte,
	cfg ConfigRetry,
) (*http.Response, error) {
	var lastError error

	for attempt := 0; attempt <= cfg.MaxRetries; attempt += 1 {
		resp, err := wp.doRequest(ctx, r, upstreamURL, body)
		if err == nil && shouldRetryStatus(resp.StatusCode) == false {
			return resp, nil
		}

		if resp != nil {
			io.Copy(io.Discard, resp.Body)
			resp.Body.Close()
		}

		lastError = err

		if attempt == cfg.MaxRetries {
			break
		}

		delay := cfg.BaseDelay * time.Duration(1<<attempt)
		jitter := time.Duration(rand.Float64() * float64(delay) * cfg.Jitter)
		sleep := min(jitter, cfg.MaxDelay)

		select {
		case <-time.After(sleep):
		case <-ctx.Done():
			return nil, ctx.Err()
		}
	}

	return nil, lastError
}

func shouldRetryStatus(statusCode int) bool {
	return statusCode >= 500 || statusCode == 429
}
