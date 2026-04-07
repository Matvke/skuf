package body

import (
	"encoding/json"
	"fmt"
)

func ParseJSON(data []byte) (map[string]any, error) {
	if len(data) == 0 {
		return nil, nil
	}

	v := make(map[string]any)
	if err := json.Unmarshal(data, &v); err != nil {
		return nil, fmt.Errorf("failed parsing json: %v", err)
	}

	return v, nil
}
