package upstream

import (
	"context"
	"io"
	"net/http"
	"time"
)

func (wp *WorkerPool) doForward(ctx context.Context, w http.ResponseWriter, r *http.Request, upstreamURL string, body []byte) error {
	response, err := wp.doRequestWithRetry(ctx, r, upstreamURL, body, ConfigRetry{
		MaxRetries: 3,
		BaseDelay:  100 * time.Millisecond,
		MaxDelay:   2 * time.Second,
		Jitter:     0.5,
	})
	if err != nil {
		return err
	}

	for key, vv := range response.Header {
		if _, banned := hopByHopHeaders[key]; banned {
			continue
		}

		for _, value := range vv {
			w.Header().Add(key, value)
		}
	}

	w.WriteHeader(response.StatusCode)
	_, err = io.Copy(w, response.Body)
	return err
}
