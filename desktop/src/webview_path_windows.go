//go:build windows

package main

import (
	"os"
	"path/filepath"
)

func webviewUserDataPath() string {
	base, err := os.UserCacheDir()
	if err != nil || base == "" {
		return ""
	}
	return filepath.Join(base, "AllinpayAI", "WebView2")
}
