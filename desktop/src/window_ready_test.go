package main

import (
	"testing"
	"time"
)

func TestWindowReadyWaitsForNavigation(t *testing.T) {
	app := &App{windowReady: make(chan struct{})}
	done := make(chan struct{})

	go func() {
		app.waitForWindowReady()
		close(done)
	}()

	select {
	case <-done:
		t.Fatal("waitForWindowReady returned before the window was ready")
	case <-time.After(20 * time.Millisecond):
	}

	app.markWindowReady()
	select {
	case <-done:
	case <-time.After(time.Second):
		t.Fatal("waitForWindowReady did not return after the window became ready")
	}
}

func TestWindowReadyCanBeMarkedMoreThanOnce(t *testing.T) {
	app := &App{windowReady: make(chan struct{})}

	app.markWindowReady()
	app.markWindowReady()

	select {
	case <-app.windowReady:
	default:
		t.Fatal("window readiness was not published")
	}
}
