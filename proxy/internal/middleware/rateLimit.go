package middleware

import (
	"net"
	"net/http"
	"strings"
	"sync"
	"time"
)

type RateLimiter struct {
	buckets map[string]*tokenBucket
	ttl     time.Duration
	rate    float64
	burst   int
	mu      sync.RWMutex
}

type tokenBucket struct {
	tokens     float64
	lastUpdate time.Time
	mu         sync.Mutex
}

func NewRateLimiter(rate float64, burst int) *RateLimiter {
	rl := &RateLimiter{
		rate:    rate,
		burst:   burst,
		buckets: make(map[string]*tokenBucket),
		ttl:     time.Minute * 5,
	}

	go rl.cleanUpLoop()

	return rl
}

func (rl *RateLimiter) Allow(key string) bool {
	rl.mu.RLock()
	bucket, ok := rl.buckets[key]
	rl.mu.RUnlock()
	if !ok {
		rl.mu.Lock()
		bucket, ok = rl.buckets[key]
		if !ok {
			bucket = &tokenBucket{
				tokens:     float64(rl.burst),
				lastUpdate: time.Now(),
			}
			rl.buckets[key] = bucket
		}
		rl.mu.Unlock()
	}

	bucket.mu.Lock()
	defer bucket.mu.Unlock()

	now := time.Now()
	elapsed := now.Sub(bucket.lastUpdate).Seconds()
	bucket.tokens = min(float64(rl.burst), bucket.tokens+(elapsed*rl.rate))
	bucket.lastUpdate = now

	if bucket.tokens >= 1 {
		bucket.tokens -= 1
		return true
	}
	return false
}

func (rl *RateLimiter) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		key := IP(r)

		if !rl.Allow(key) {
			w.Header().Set("Retry-After", "1")
			w.WriteHeader(http.StatusTooManyRequests)
			w.Write([]byte(`{"error": "rate limit exceeded"}`))
			return
		}

		next.ServeHTTP(w, r)
	})
}

func (rl *RateLimiter) cleanUpLoop() {
	ticker := time.NewTicker(time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		now := time.Now()

		rl.mu.Lock()
		for key, bucket := range rl.buckets {
			bucket.mu.Lock()
			expired := now.Sub(bucket.lastUpdate) >= rl.ttl
			bucket.mu.Unlock()

			if expired {
				delete(rl.buckets, key)
			}
		}
		rl.mu.Unlock()
	}
}

func IP(r *http.Request) string {
	key := r.Header.Get("X-Forwarded-For")
	if key != "" {
		parts := strings.Split(key, ",")
		return strings.TrimSpace(parts[0])
	}

	key = r.Header.Get("X-Real-IP")
	if key != "" {
		return key
	}

	ip, _, _ := net.SplitHostPort(r.RemoteAddr)
	return ip
}
