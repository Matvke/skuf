package extract

import "fmt"

func MessagesContent(payload map[string]any) ([]Value, error) {
	rawMessages, ok := payload["messages"]
	if !ok {
		return nil, nil
	}

	messages, ok := rawMessages.([]any)
	if !ok {
		return nil, fmt.Errorf("messages is not an array")
	}

	result := make([]Value, 0)

	for i, m := range messages {
		msg, ok := m.(map[string]any)
		if !ok {
			continue
		}

		rawContent, ok := msg["content"]
		if !ok {
			continue
		}

		content, ok := rawContent.(string)
		if !ok {
			continue
		}

		result = append(result, Value{
			Path:  fmt.Sprintf("messages.%d.content", i),
			Value: content,
		})
	}

	return result, nil
}
