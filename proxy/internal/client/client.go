package client

import (
	"bytes"
	"io"
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
		client:  &http.Client{Timeout: 5 * time.Second},
	}
}

func (e *EngineClient) Forward(body []byte) ([]byte, int, error) {
	req, _ := http.NewRequest("POST", e.baseUrl+"/sanitize", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")

	resp, err := e.client.Do(req)
	if err != nil {
		return nil, http.StatusBadRequest, err
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, http.StatusInternalServerError, err
	}

	return respBody, http.StatusOK, nil
}
