package middleware

import (
	"net/http"

	requestid "github.com/Matvke/skuf/internal/request_id"
	"github.com/google/uuid"
)

func RequestID(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requestID := r.Header.Get(requestid.Header)
		if requestID == "" {
			requestID = uuid.NewString()
		}

		ctx := requestid.With(r.Context(), requestID)
		r = r.WithContext(ctx)

		w.Header().Set(requestid.Header, requestID)

		next.ServeHTTP(w, r)
	})
}
