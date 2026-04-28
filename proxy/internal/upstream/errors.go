package upstream

import "errors"

var (
	ErrQueueFull = errors.New("Queue of requests is full")
)
