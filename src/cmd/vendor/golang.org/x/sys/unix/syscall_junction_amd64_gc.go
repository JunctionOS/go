//go:build junction
// Copyright 2016 The Go Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

// +build amd64,junction,!linux
// +build gc

package unix

import "syscall"

//go:noescape
func gettimeofday(tv *Timeval) (err syscall.Errno)
