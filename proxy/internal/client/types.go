package client

type AnonymizeRequest struct {
	Text string `json:"text"`
}

type HTTPValidationError struct {
	Detail []ValidationError `json:"detail"`
}

type ValidationError struct {
	Loc   []any  `json:"loc"`
	Msg   string `json:"msg"`
	Type  string `json:"type"`
	Input any    `json:"input,omitempty"`
}
