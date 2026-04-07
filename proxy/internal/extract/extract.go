package extract

import "fmt"

func Extract(payload any, path CompiledPath) ([]Value, error) {
	current := []CurrentNode{
		CurrentNode{
			Node: payload,
			Path: "",
		},
	}

	for _, segment := range path.Segments {
		next := make([]CurrentNode, 0)

		switch segment.Kind {
		case FieldSegment:
			for _, node := range current {
				n, ok := node.Node.(map[string]any)
				if !ok {
					continue
				}

				field, ok := n[segment.Field]
				if !ok {
					return nil, fmt.Errorf("invalid segment field, cant find in map")
				}
				p := ""
				if node.Path == "" {
					p = segment.Field
				} else {
					p = fmt.Sprintf("%s.%s", node.Path, segment.Field)
				}
				next = append(next, CurrentNode{
					Node: field,
					Path: p,
				})
			}
		case WildcardSegment:
			for _, node := range current {
				n, ok := node.Node.([]any)
				if !ok {
					continue
				}
				for i, v := range n {
					next = append(next, CurrentNode{
						Node: v,
						Path: fmt.Sprintf("%s.%d", node.Path, i),
					})
				}
			}
		case IndexSegment:
			for _, node := range current {
				n, ok := node.Node.([]any)
				if segment.Index < 0 || segment.Index >= len(n) {
					return nil, fmt.Errorf("invalid segment index, out of range")
				}
				if !ok {
					continue
				}
				next = append(next, CurrentNode{
					Node: n[segment.Index],
					Path: fmt.Sprintf("%s.%d", node.Path, segment.Index),
				})
			}
		}
		current = next
	}

	var result []Value
	for _, node := range current {
		n, ok := node.Node.(string)
		if ok {
			result = append(result, Value{
				Path:  node.Path,
				Value: n,
			})
		}
	}

	return result, nil
}
