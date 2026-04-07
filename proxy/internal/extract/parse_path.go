package extract

import (
	"fmt"
	"strconv"
	"strings"
)

func ParsePath(path string) (*CompiledPath, error) {
	path = strings.TrimSpace(path)
	if path == "" {
		return nil, fmt.Errorf("empty path")
	}

	result := &CompiledPath{
		RawPath:  path,
		Segments: make([]Segment, 0),
	}

	parts := strings.Split(path, ".")
	for _, part := range parts {
		if part == "" {
			return nil, fmt.Errorf("invalid empty segment in path")
		}

		bracketIdx := strings.Index(part, "[")
		if bracketIdx == -1 {
			result.Segments = append(result.Segments, Segment{
				Field: part,
				Kind:  FieldSegment,
			})
			continue
		}

		if !strings.HasSuffix(part, "]") {
			return nil, fmt.Errorf("invalid type of segment no ]")
		}

		field := part[:bracketIdx]
		if field == "" {
			return nil, fmt.Errorf("invalid segment %q, empty field name", part)
		}

		inside := part[bracketIdx+1 : len(part)-1]
		if inside == "" {
			return nil, fmt.Errorf("invalid segment %q, empty brackets", part)
		}

		result.Segments = append(result.Segments, Segment{
			Kind:  FieldSegment,
			Field: field,
		})

		if inside == "*" {
			result.Segments = append(result.Segments, Segment{
				Kind: WildcardSegment,
			})
			continue
		}

		idx, err := strconv.Atoi(inside)
		if err != nil {
			return nil, fmt.Errorf("invalid segment %q, wrong index in brackets", part)
		}

		result.Segments = append(result.Segments, Segment{
			Kind:  IndexSegment,
			Index: idx,
		})
	}

	return result, nil
}
