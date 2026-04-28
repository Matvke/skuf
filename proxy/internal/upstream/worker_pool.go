package upstream

import (
	"context"
	"net/http"
	"sync"
	"time"
)

const (
	maxQueue      = 1000
	workers       = 50
	clientTimeout = time.Second * 30
)

type WorkerPool struct {
	workers   int
	maxQueue  int
	taskQueue chan *forwardTask
	wg        sync.WaitGroup
	client    *http.Client
}

type forwardTask struct {
	ctx         context.Context
	w           http.ResponseWriter
	r           *http.Request
	upstreamURL string
	body        []byte
	resultChan  chan *forwardResult
}

type forwardResult struct {
	err error
}

type IForwarder interface {
	Forward(context.Context, http.ResponseWriter, *http.Request, string, []byte) error
}

var hopByHopHeaders = map[string]struct{}{
	"Connection":        {},
	"Proxy-Connection":  {},
	"Keep-Alive":        {},
	"Transfer-Encoding": {},
	"TE":                {},
	"Trailer":           {},
	"Upgrade":           {},
}

func NewWorkerPool() *WorkerPool {
	wp := &WorkerPool{
		workers:   workers,
		maxQueue:  maxQueue,
		taskQueue: make(chan *forwardTask, maxQueue),
		client: &http.Client{
			Timeout: clientTimeout,
		},
	}

	for i := 0; i < workers; i++ {
		wp.wg.Add(1)
		go wp.worker(i)
	}

	return wp
}

func (wp *WorkerPool) worker(id int) {
	defer wp.wg.Done()

	for task := range wp.taskQueue {
		if task == nil {
			return
		}

		result := &forwardResult{}
		result.err = wp.doForward(task.ctx, task.w, task.r, task.upstreamURL, task.body)
		task.resultChan <- result
	}
}

func (wp *WorkerPool) Forward(ctx context.Context, w http.ResponseWriter, r *http.Request, upstreamURL string, body []byte) error {
	resultChan := make(chan *forwardResult, 1)
	task := &forwardTask{
		ctx:         ctx,
		w:           w,
		r:           r,
		upstreamURL: upstreamURL,
		body:        body,
		resultChan:  resultChan,
	}

	select {
	case wp.taskQueue <- task:
		select {
		case result := <-resultChan:
			return result.err
		case <-ctx.Done():
			return ctx.Err()
		}
	case <-ctx.Done():
		return ctx.Err()
	default:
		return ErrQueueFull
	}
}

func (wp *WorkerPool) ShutDown(ctx context.Context) error {
	close(wp.taskQueue)

	done := make(chan struct{})
	go func() {
		wp.wg.Wait()
		close(done)
	}()

	select {
	case <-done:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}
