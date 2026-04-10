package upstream

import (
	"bytes"
	"context"
	"io"
	"net/http"
	"net/url"
	"time"
)

type Forwarder struct {
	client *http.Client
}

var hopByHopHeaders = map[string]struct{}{
	"Connection":        {},
	"Proxy-Connection":  {},
	"Keep-Alive":        {},
	"Transfer-Encoding": {},
	"TE":                {},
	"Trailer":           {},
	"Upgrade":           {},
}

func NewForwarder() *Forwarder {
	return &Forwarder{
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

func (f *Forwarder) Forward(ctx context.Context, w http.ResponseWriter, r *http.Request, upstreamURL string, body []byte) error {
	url, err := url.Parse(upstreamURL)
	if err != nil {
		return err
	}

	url.RawQuery = r.URL.RawQuery

	request, err := http.NewRequestWithContext(ctx, r.Method, url.String(), bytes.NewReader(body))
	if err != nil {
		return err
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

	response, err := f.client.Do(request)
	if err != nil {
		return err
	}
	defer response.Body.Close()

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
