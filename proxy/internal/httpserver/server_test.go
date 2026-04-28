package httpserver

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"sync"
	"testing"

	"github.com/Matvke/skuf/internal/config"
)

type MockEngine struct {
	Calls int
	mu    sync.Mutex
	In    []string
}

func (m *MockEngine) Anonymize(ctx context.Context, text string) (string, error) {
	m.mu.Lock()
	m.Calls += 1
	m.In = append(m.In, text)
	m.mu.Unlock()

	return "[ANON] " + text, nil
}

func (m *MockEngine) Health(ctx context.Context) error {
	return nil
}

func (m *MockEngine) SetBaseUrl(url string) {
	return
}

type MockForwarder struct {
	mu          sync.Mutex
	Calls       int
	UpstreamURL string
	Body        []byte
}

func (f *MockForwarder) Forward(ctx context.Context, w http.ResponseWriter, r *http.Request, upstreamURL string, body []byte) error {
	f.mu.Lock()
	f.Calls += 1
	f.UpstreamURL = upstreamURL
	f.Body = append([]byte(nil), body...)
	f.mu.Unlock()

	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte("ok"))
	return nil
}

func TestProxy_AnonymizeAndForward_ModifiesJSONBody(t *testing.T) {
	cfg := &config.Config{
		Targets: []config.Target{
			{
				Name:        "openai-chat",
				MatchHost:   "localhost:8080",
				MatchPath:   "/api/v1/static",
				Methods:     map[string]struct{}{"POST": {}},
				UpstreamURL: "http://localhost:8080/api/v1/static",
				JsonPaths:   []string{"data.chat.messages[*].parts[*].text"},
			},
		},
	}

	store := config.NewStore(cfg)

	testEngine := &MockEngine{}
	testForwarder := &MockForwarder{}

	testServer := New(store, "configs/config.yaml", testEngine, testForwarder)

	reqBody := []byte(`{
	  "data": {
	    "chat": {
	      "messages": [
	        {"parts":[{"text":"hello"},{"text":"world"}]},
	        {"parts":[{"text":"secret"}]}
	      ]
	    }
	  }
	}`)

	rec := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodPost, "http://localhost/api/v1/static", bytes.NewReader(reqBody))
	req.Host = "localhost:8080"
	req.Header.Set("Content-Type", "application/json")

	testServer.Handler().ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected status code 200, got %d", rec.Code)
	}

	if testForwarder.Calls != 1 {
		t.Fatalf("expected forwarder calls = 1, got %d", testForwarder.Calls)
	}

	if testEngine.Calls != 3 {
		t.Fatalf("expected engine calls = 3, got %d", testEngine.Calls)
	}

	var out any
	if err := json.Unmarshal(testForwarder.Body, &out); err != nil {
		t.Fatalf("failed to unmarshal forwarded body: %v; body=%s", err, testForwarder.Body)
	}

	root := out.(map[string]any)
	data := root["data"].(map[string]any)
	chat := data["chat"].(map[string]any)
	msgs := chat["messages"].([]any)

	msg0 := msgs[0].(map[string]any)
	parts0 := msg0["parts"].([]any)
	txt00 := parts0[0].(map[string]any)["text"].(string)
	txt01 := parts0[1].(map[string]any)["text"].(string)

	msg1 := msgs[1].(map[string]any)
	parts1 := msg1["parts"].([]any)
	txt10 := parts1[0].(map[string]any)["text"].(string)

	if txt00 != "[ANON] hello" || txt01 != "[ANON] world" || txt10 != "[ANON] secret" {
		t.Fatalf("unexpected anonymized texts: %q, %q, %q", txt00, txt01, txt10)
	}
}
