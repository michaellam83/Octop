//go:build windows

package main

import (
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
	"unsafe"

	"golang.org/x/sys/windows"
)

var (
	user32MessageBox = windows.NewLazySystemDLL("user32.dll").NewProc("MessageBoxW")
	applicationError = sync.Once{}
)

func reportApplicationError(err error) {
	if err == nil {
		return
	}

	message := fmt.Sprintf("%s\n\n日志位置：%s", err, applicationLogPath())
	appendApplicationLog(err)
	applicationError.Do(func() {
		text, textErr := windows.UTF16PtrFromString(message)
		caption, captionErr := windows.UTF16PtrFromString("AllinpayAI 启动失败")
		if textErr == nil && captionErr == nil {
			_, _, _ = user32MessageBox.Call(
				0,
				uintptr(unsafe.Pointer(text)),
				uintptr(unsafe.Pointer(caption)),
				0x10,
			)
		}
	})
}

func applicationLogPath() string {
	base, err := os.UserCacheDir()
	if err != nil || base == "" {
		base = os.TempDir()
	}
	return filepath.Join(base, "AllinpayAI", "logs", "desktop.log")
}

func appendApplicationLog(err error) {
	path := applicationLogPath()
	if mkdirErr := os.MkdirAll(filepath.Dir(path), 0o755); mkdirErr != nil {
		return
	}
	file, openErr := os.OpenFile(path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
	if openErr != nil {
		return
	}
	defer file.Close()
	_, _ = fmt.Fprintf(file, "[%s] %v\r\n", time.Now().Format(time.RFC3339), err)
}
