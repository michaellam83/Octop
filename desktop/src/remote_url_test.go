package main

import "testing"

func TestConfiguredDesktopURLPrefersEnvironment(t *testing.T) {
	t.Setenv("OCTOP_DESKTOP_URL", " http://env.example.test:8088/ ")
	defaultRemoteURL = "http://compiled.example.test:8088"
	t.Cleanup(func() { defaultRemoteURL = "" })

	if got := configuredDesktopURL(); got != "http://env.example.test:8088/" {
		t.Fatalf("configuredDesktopURL() = %q, want environment URL", got)
	}
}

func TestConfiguredDesktopURLUsesCompiledDefault(t *testing.T) {
	t.Setenv("OCTOP_DESKTOP_URL", "")
	defaultRemoteURL = " http://compiled.example.test:8088/ "
	t.Cleanup(func() { defaultRemoteURL = "" })

	if got := configuredDesktopURL(); got != "http://compiled.example.test:8088/" {
		t.Fatalf("configuredDesktopURL() = %q, want compiled URL", got)
	}
}

func TestConfiguredDesktopURLFallsBackToLocalMode(t *testing.T) {
	t.Setenv("OCTOP_DESKTOP_URL", "")
	defaultRemoteURL = "  "
	t.Cleanup(func() { defaultRemoteURL = "" })

	if got := configuredDesktopURL(); got != "" {
		t.Fatalf("configuredDesktopURL() = %q, want empty local-mode URL", got)
	}
}
