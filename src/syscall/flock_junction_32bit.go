//go:build junction
// Copyright 2014 The Go Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

// If you change the build tags here, see
// internal/syscall/unix/fcntl_linux_32bit.go.

// +build junction,386,!linux junction,arm,!linux junction,mips,!linux junction,mipsle,!linux

package syscall

func init() {
	// On 32-bit Linux systems, the fcntl syscall that matches Go's
	// Flock_t type is SYS_FCNTL64, not SYS_FCNTL.
	fcntl64Syscall = SYS_FCNTL64
}
