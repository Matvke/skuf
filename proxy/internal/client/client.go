package client

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

type EngineClient struct {
	baseUrl string
	client  *http.Client
}

func NewEngineClient(baseUrl string) *EngineClient {
	return &EngineClient{
		baseUrl: baseUrl,
		client:  &http.Client{Timeout: 30 * time.Second},
	}
}

type AnonymizeRequest struct {
	Text    string `json:"text"`
	Profile string `json:"profile"`
}

type AnonymizeResponse struct {
	Action         string `json:"action"`
	AnonymizedText string `json:"anonymized_text"`
	Reason         string `json:"reason,omitempty"`
}

func (c *EngineClient) Anonymize(ctx context.Context, text, profile string) (*AnonymizeResponse, error) {
	req := AnonymizeRequest{
		Text:    text,
		Profile: profile,
	}

	jsonData, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("marshal request: %v", err)
	}

	httpReq, err := http.NewRequestWithContext(
		ctx,
		http.MethodPost,
		c.baseUrl+"/v1/anonimization/all",
		bytes.NewBuffer(jsonData),
	)
	if err != nil {
		return nil, fmt.Errorf("create request: %v", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := c.client.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("http request: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("engine returned status %d", resp.StatusCode)
	}

	var result AnonymizeResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("decode response: %v", err)
	}

	return &result, nil
}

func (c *EngineClient) Health(ctx context.Context) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.baseUrl+"/health", nil)
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
