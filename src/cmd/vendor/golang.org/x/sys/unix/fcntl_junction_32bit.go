// Copyright 2014 The Go Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

//go:build ((junction && 386) || (junction && arm) || (junction && mips) || (junction && mipsle) || (junction && ppc)) && !linux
// +build junction,386,!linux junction,arm,!linux junction,mips,!linux junction,mipsle,!linux junction,ppc,!linux

package unix

func init() {
	// On 32-bit Linux systems, the fcntl syscall that matches Go's
	// Flock_t type is SYS_FCNTL64, not SYS_FCNTL.
	fcntl64Syscall = SYS_FCNTL64
}
