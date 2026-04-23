package client

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"sync"
	"time"

	requestid "github.com/Matvke/skuf/internal/request_id"
)

type IEngine interface {
	Anonymize(context.Context, string) (string, error)
	Health(context.Context) error
}
type EngineClient struct {
	baseUrl  string
	client   *http.Client
	cache    sync.Map //map[string]*cacheEntry (text - [value: anonText, expiresAt: lifetime])
	ttl      time.Duration
	mu       sync.Mutex
	inflight map[string]*inflightCall
}

type cacheEntry struct {
	value     string
	expiresAt time.Time
}

type inflightCall struct {
	wg    sync.WaitGroup
	value string
	err   error
}

func NewEngineClient(baseUrl string) *EngineClient {
	baseUrl = strings.TrimRight(baseUrl, "/")
	engineClient := &EngineClient{
		baseUrl: baseUrl,
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
		ttl:      time.Minute * 5,
		inflight: make(map[string]*inflightCall),
	}

	go engineClient.cleanUpLoop()

	return engineClient
}

func (ec *EngineClient) Anonymize(ctx context.Context, text string) (string, error) {
	if entry, ok := ec.cache.Load(text); ok {
		e := entry.(*cacheEntry)
		if time.Now().Before(e.expiresAt) {
			return e.value, nil
		}
		ec.cache.Delete(text)
	}

	ec.mu.Lock()
	if call, ok := ec.inflight[text]; ok {
		ec.mu.Unlock()
		call.wg.Wait()
		return call.value, call.err
	}

	call := &inflightCall{}
	call.wg.Add(1)
	ec.inflight[text] = call
	ec.mu.Unlock()

	defer func() {
		ec.mu.Lock()
		delete(ec.inflight, text)
		ec.mu.Unlock()
		call.wg.Done()
	}()

	req := AnonymizeRequest{
		Text: text,
	}

	jsonData, err := json.Marshal(req)
	if err != nil {
		return "", fmt.Errorf("marshal request: %v", err)
	}

	httpReq, err := http.NewRequestWithContext(
		ctx,
		http.MethodPost,
		ec.baseUrl+"/v1/anonimization/base",
		bytes.NewReader(jsonData),
	)
	if err != nil {
		return "", fmt.Errorf("create request: %v", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Accept", "application/json")

	if requestId, ok := requestid.From(ctx); ok {
		httpReq.Header.Set(requestid.Header, requestId)
	}

	resp, err := ec.client.Do(httpReq)
	if err != nil {
		call.err = fmt.Errorf("http request: %v", err)
		return "", call.err
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		var anonymizedText string
		if err := json.NewDecoder(resp.Body).Decode(&anonymizedText); err != nil {
			call.err = fmt.Errorf("decode 200 response: %v", err)
			return "", call.err
		}

		ec.cache.Store(text, &cacheEntry{
			value:     anonymizedText,
			expiresAt: time.Now().Add(ec.ttl),
		})
		call.value = anonymizedText
		return anonymizedText, nil
	}

	errBody, err := readBodyLimited(resp.Body, 64<<10)
	if err != nil {
		call.err = fmt.Errorf("reading body, error: %v", err)
		return "", call.err
	}

	if resp.StatusCode == http.StatusUnprocessableEntity {
		var validationError HTTPValidationError
		if err := json.Unmarshal(errBody, &validationError); err != nil {
			call.err = &EngineHTTPError{
				Status: resp.StatusCode,
				Body:   string(errBody),
			}
			return "", call.err
		}
		call.err = &EngineValidationError{
			Status: resp.StatusCode,
			Detail: validationError,
			Body:   string(errBody),
		}
		return "", call.err
	}

	call.err = &EngineHTTPError{
		Status: resp.StatusCode,
		Body:   string(errBody),
	}
	return "", call.err
}

func (ec *EngineClient) Health(ctx context.Context) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, ec.baseUrl+"/", nil)
	if err != nil {
		return err
	}

	resp, err := ec.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("unhealthy status: %d", resp.StatusCode)
	}

	return nil
}

func readBodyLimited(r io.Reader, max int64) ([]byte, error) {
	limitedReader := io.LimitReader(r, max)
	return io.ReadAll(limitedReader)
}

func (ec *EngineClient) cleanUpLoop() {
	ticker := time.NewTicker(1 * time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		now := time.Now()

		ec.cache.Range(func(key, value any) bool {
			entry := value.(*cacheEntry)
			if now.After(entry.expiresAt) {
				ec.cache.Delete(key)
			}
			return true
		})
	}
}
