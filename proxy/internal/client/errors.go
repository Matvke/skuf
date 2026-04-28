package client

import "fmt"

type EngineHTTPError struct {
	Status int
	Body   string
}

func (e *EngineHTTPError) Error() string {
	if e.Body == "" {
		return fmt.Sprintf("engine http error: status=%d", e.Status)
	}
	return fmt.Sprintf("engine http error: status=%d body=%s", e.Status, e.Body)
}

type EngineValidationError struct {
	Status int
	Detail HTTPValidationError
	Body   string
}

func (e *EngineValidationError) Error() string {
	if len(e.Detail.Detail) > 0 {
		return fmt.Sprintf("engine validation error: status=%d, details=%d", e.Status, len(e.Detail.Detail))
	}

	if e.Body == "" {
		return fmt.Sprintf("engine validation error: status=%d", e.Status)
	}

	return fmt.Sprintf("engine validation error: status=%d, body=%s", e.Status, e.Body)
}
