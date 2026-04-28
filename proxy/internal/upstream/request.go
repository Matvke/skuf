package upstream

import (
	"bytes"
	"context"
	"net/http"
	"net/url"
)

func (wp *WorkerPool) doRequest(ctx context.Context, r *http.Request, upstreamURL string, body []byte) (*http.Response, error) {
	url, err := url.Parse(upstreamURL)
	if err != nil {
		return nil, err
	}

	url.RawQuery = r.URL.RawQuery

	request, err := http.NewRequestWithContext(ctx, r.Method, url.String(), bytes.NewReader(body))
	if err != nil {
		return nil, err
	}

	for key, vv := range r.Header {
		if _, banned := hopByHopHeaders[key]; banned {
			continue
		}

		for _, value := range vv {
			request.Header.Add(key, value)
		}
	}

	request.Host = url.Host

	return wp.client.Do(request)
}
