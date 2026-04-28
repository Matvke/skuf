package body

import (
	"fmt"
	"io"
	"net/http"
)

func Reader(r *http.Request, maxByte int64) ([]byte, error) {
	if r.Body == nil {
		return nil, nil
	}
	defer r.Body.Close()

	limited := io.LimitReader(r.Body, maxByte)
	data, err := io.ReadAll(limited)
	if err != nil {
		return nil, fmt.Errorf("failed reading request body: %v", err)
	}

	return data, nil
}
