//go:build !windows

package main

import "log"

func reportApplicationError(err error) {
	if err != nil {
		log.Printf("desktop startup error: %v", err)
	}
}
