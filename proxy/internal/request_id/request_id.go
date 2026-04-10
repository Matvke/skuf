package requestid

import "context"

type requestIdKey struct{}

const Header = "X-request-Id"

func With(ctx context.Context, id string) context.Context {
	return context.WithValue(ctx, requestIdKey{}, id)
}

func From(ctx context.Context) (string, bool) {
	v := ctx.Value(requestIdKey{})
	if v == nil {
		return "", false
	}

	s, ok := v.(string)
	return s, ok && s != ""
}
