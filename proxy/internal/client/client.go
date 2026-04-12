package client

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	requestid "github.com/Matvke/skuf/internal/request_id"
)

type Engine interface {
	Anonymize(context.Context, string) (string, error)
	Health(context.Context) error
}
type EngineClient struct {
	baseUrl string
	client  *http.Client
}

func NewEngineClient(baseUrl string) *EngineClient {
	baseUrl = strings.TrimRight(baseUrl, "/")
	return &EngineClient{
		baseUrl: baseUrl,
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

func (c *EngineClient) Anonymize(ctx context.Context, text string) (string, error) {
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
		c.baseUrl+"/v1/anonimization/base",
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

	resp, err := c.client.Do(httpReq)
	if err != nil {
		return "", fmt.Errorf("http request: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		var anonymizedText string
		if err := json.NewDecoder(resp.Body).Decode(&anonymizedText); err != nil {
			return "", fmt.Errorf("decode 200 response: %v", err)
		}
		return anonymizedText, nil
	}

	errBody, _ := readBodyLimited(resp.Body, 64<<10)

	if resp.StatusCode == http.StatusUnprocessableEntity {
		var validationError HTTPValidationError
		if err := json.NewDecoder(resp.Body).Decode(&validationError); err != nil {
			return "", &EngineHTTPError{
				Status: resp.StatusCode,
				Body:   string(errBody),
			}
		}
		return "", &EngineValidationError{
			Status: resp.StatusCode,
			Detail: validationError,
			Body:   string(errBody),
		}
	}

	return "", &EngineHTTPError{
		Status: resp.StatusCode,
		Body:   string(errBody),
	}
}

func (c *EngineClient) Health(ctx context.Context) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.baseUrl+"/", nil)
	if err != nil {
		return err
	}

	resp, err := c.client.Do(req)
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
