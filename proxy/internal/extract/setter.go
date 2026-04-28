package extract

import (
	"fmt"
	"strconv"
	"strings"
)

type resolvedPath struct {
	isIndex bool
	index   int
	field   string
}

func parseResolvedPath(path string) ([]resolvedPath, error) {
	path = strings.TrimSpace(path)
	if path == "" {
		return nil, fmt.Errorf("empty resolved path")
	}

	parts := strings.Split(path, ".")
	segments := make([]resolvedPath, 0, len(parts))

	for _, part := range parts {
		if part == "" {
			return nil, fmt.Errorf("invalid resolved path %q: empty segment", path)
		}

		if idx, err := strconv.Atoi(part); err == nil {
			if idx < 0 {
				return nil, fmt.Errorf("invalid resolved path %q: negative index %d", path, idx)
			}

			segments = append(segments, resolvedPath{
				isIndex: true,
				index:   idx,
			})
			continue
		}

		segments = append(segments, resolvedPath{
			field: part,
		})
	}

	return segments, nil
}

func SetString(payload any, resolvedPath string, newValue string) error {
	segments, err := parseResolvedPath(resolvedPath)
	if err != nil {
		return err
	}

	if len(segments) == 0 {
		return fmt.Errorf("empty resolved path segments")
	}

	curr := payload

	for i := 0; i < len(segments)-1; i++ {
		segment := segments[i]

		if segment.isIndex {
			arr, ok := curr.([]any)
			if !ok {
				return fmt.Errorf("path %q: expected array at segment %d", resolvedPath, i)
			}

			if segment.index > len(arr) {
				return fmt.Errorf("path %q: index out of range at segment %d", resolvedPath, i)
			}

			curr = arr[segment.index]
			continue
		}

		obj, ok := curr.(map[string]any)
		if !ok {
			return fmt.Errorf("path %q: expected object at segment %d", resolvedPath, i)
		}

		v, exists := obj[segment.field]
		if !exists {
			return fmt.Errorf("path %q: missing field %q at segment %d", resolvedPath, segment.field, i)
		}
		curr = v
	}

	last := segments[len(segments)-1]

	if last.isIndex {
		arr, ok := curr.([]any)
		if !ok {
			return fmt.Errorf("path %q: expected array at segment %d", resolvedPath, last.index)
		}

		if last.index > len(arr) {
			return fmt.Errorf("path %q: index out of range at segment %d", resolvedPath, last.index)
		}

		arr[last.index] = newValue
		return nil
	}

	obj, ok := curr.(map[string]any)
	if !ok {
		return fmt.Errorf("path %q: expected object at segment %d", resolvedPath, last.index)
	}

	obj[last.field] = newValue
	return nil
}
